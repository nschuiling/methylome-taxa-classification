#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=2GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/A5-slurm-%A_%a.out
#SBATCH --error=./slurmlog/A5-slurm-%A_%a.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartA_DataCollection"

# Load necessary modules and virtual environments
module use /opt/insy/modulefiles
module use /opt/insy/modules/DBL/modulefiles
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate chopper

# The data consists of multiple datasets (samples/runs) for different projects
# The configuration file contains all information for the analysis of each dataset
config="../configurations/allprojects.config"

# The following projects are in the config file (accessable via #SBATCH --array=xx above):
# "CHEESE_PRJEB58160" (--array=1-3), "NANOMOTIF_PRJEB74343" (--array=4-7), "DBL_SAMPLES" (--array=8-15)

# Define the run specifications using the current array position
project_name=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $2}' ${config})
run_name=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $3}' ${config})
data_url=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $4}' ${config})
data_size=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $5}' ${config})
data_type=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $6}' ${config})
basecall_model=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $7}' ${config})

# Print which data will be analysed
echo "Project: ${project_name}. Run: ${run_name}."


##############################################
##### DEFINE INPUT AND OUTPUT FILE PATHS #####

## Input: unfiltered basecalled bam file
# Folder
BASECALLS_DIR="./files/A3_BamBasecalls/${project_name}/${run_name}"
# File
UNFILTERED_BAM="${BASECALLS_DIR}/${run_name}.bam"

## Output: QC-filtered basecalls
# Final output folder
QC_FILTERED_DIR="./files/A5_QCFilteredBasecalls/${project_name}/${run_name}"
mkdir -p ${QC_FILTERED_DIR}
# Intermediate output folder
TMP_DIR="${QC_FILTERED_DIR}/tmp"
mkdir -p "${TMP_DIR}"
# Intermediate files
FILTERED_FASTQ="${TMP_DIR}/${run_name}_filtered.fastq"
FILTERED_BAM="${TMP_DIR}/${run_name}_filtered.bam"
FILTERED_BAM_SORTED="${TMP_DIR}/${run_name}_filtered_sorted.bam"
UNFILTERED_BAM_SORTED="${TMP_DIR}/${run_name}_unfiltered_sorted.bam"
REPAIRED_BAM="${TMP_DIR}/${run_name}_repaired.bam"
# Final files
ANALYSIS_BAM="${QC_FILTERED_DIR}/${run_name}_analysis.bam"
ANALYSIS_FA="${QC_FILTERED_DIR}/${run_name}_analysis.fasta"


#######################################################
##### QUALITY CONTROL AND FILTERING OF .BAM FILES #####

## Apply Chopper QC filtering to the raw reads .bam file
## Command/parameter breakdown:
# samtools fastq: convert the .bam file to .fastq format for processing with Chopper
# -T "*": maintain all tags in the .bam file (to recover these back later)
# ${UNFILTERED_BAM}: use the unfiltered .bam file as input
# | chopper: pipe the output of the .fastq conversion to chopper
# -q 0: initially, do not filter out reads based on their quality score
# --headcrop 50 --tailcrop 30: trim bases from the read beginnings (50) and ends (30)
# | chopper: pipe the trimmed reads output to another round of chopper
# -q 13: filter out reads with a Phred average quality score below 13
# -l 500: filter out reads with a read length below 500
# > ${FILTERED_FASTQ}: save the results to the filtered fastq file (temporary)
echo "Starting QC-filtering with Chopper on bam file: ${UNFILTERED_BAM}."
srun samtools fastq -T "*" ${UNFILTERED_BAM} | \
  chopper -q 0 --headcrop 50 --tailcrop 30 | \
  chopper -q 13 -l 500 > ${FILTERED_FASTQ}
wait
echo "Bam (fastq version) filtered by chopper."
    
    
## Convert the QC-filtered .fastq file back to .bam format
## Command/parameter breakdown:
# samtools import: command to load a .fastq file and convert it to .bam format
#  -T "*": copy all tags to the output
# ${FILTERED_FASTQ} > ${FILTERED_BAM}: input .fastq file (from the step above) and output .bam file
echo "Converting filtered fastq file back to bam file."
srun samtools import -T "*" ${FILTERED_FASTQ} > ${FILTERED_BAM}
wait
echo "Filtered fastq converted back to bam format."


## Repair the methylation tags in the .bam file
# First sort the .bam files
echo "Sorting the filtered and unfiltered bam files for methylation tag repairment."
samtools sort -n ${FILTERED_BAM} -o ${FILTERED_BAM_SORTED}
samtools sort -n ${UNFILTERED_BAM} -o ${UNFILTERED_BAM_SORTED}
# Run modkit to rapair the tags, using the tags from the original .bam file
echo "Starting methylation tag repairment with Modkit."
srun ./software/modkit_v0.2.6_centos7_x86_64/modkit repair \
    --donor-bam ${UNFILTERED_BAM_SORTED} \
    --acceptor-bam ${FILTERED_BAM_SORTED} \
    --output-bam ${REPAIRED_BAM}
wait
echo "Repaired the QC-filtered bam file with its original modification tags."


## Reset the .bam file to ensure usable formatting
## Command/parameter breakdown:
# samtools reset: removes alignment information (and tags), simplifying the .bam file
#  -o ${ANALYSIS_BAM}: output (after reset) .bam file
#  --keep-tag MM,ML: only keep the relevant tags (the methylation tags)
#  ${REPAIRED_BAM}: input .bam file to use
echo "Resetting the bam file to ensure correct formatting."
srun samtools reset -o ${ANALYSIS_BAM} --keep-tag MM,ML ${REPAIRED_BAM}
wait


## Convert the final .bam file to a .fasta formatted copy
# This is needed for some analyses later on
echo "Creating a fasta version of the QC-filtered bam file."
srun samtools fasta ${ANALYSIS_BAM} > ${ANALYSIS_FA}
wait
echo "Fasta version of analysis .bam created, without tags." 


## Remove unnecessary intermediate files
echo "Finished QC filtering of run ${run_name}." 
rm -r ${TMP_DIR}
echo "Removed temporary intermediate files."  
    

## Perform basic checks on the final .bam file (and compare with the original)
# Check the number of reads in the bam files
echo "Number of reads in the original .bam: $(samtools view -c ${UNFILTERED_BAM})"
echo "Number of reads in the QC filtered .bam: $(samtools view -c ${ANALYSIS_BAM})"
# Check headers of the .bam files
echo "Header of the original .bam:"
samtools view -H ${UNFILTERED_BAM}
echo "Header of the QC filtered .bam:"
samtools view -H ${ANALYSIS_BAM}
# Check first lines of the .bam files
echo "First lines of the original .bam:"
samtools view ${UNFILTERED_BAM} | head -n2
echo "First lines of the QC filtered .bam:"
samtools view ${ANALYSIS_BAM} | head -n2

echo "DONE."
