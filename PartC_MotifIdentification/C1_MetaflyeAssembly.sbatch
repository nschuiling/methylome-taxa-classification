#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=medium
#SBATCH --time=24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=12
#SBATCH --mem=200GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/C1-slurm-%A_%a.out
#SBATCH --error=./slurmlog/C1-slurm-%A_%a.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartC_MotifIdentification"

# Load necessary modules and virtual environments
module use /opt/insy/modulefiles
module use /opt/insy/modules/DBL/modulefiles
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
module load minimap2

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

# Input: QC-filtered basecalled bam and fasta files
# Folder
QC_FILTERED_DIR="../PartA_DataCollection/files/A5_QCFilteredBasecalls/${project_name}/${run_name}"
# Files
ANALYSIS_BAM="${QC_FILTERED_DIR}/${run_name}_analysis.bam"
ANALYSIS_FA="${QC_FILTERED_DIR}/${run_name}_analysis.fasta"

# Metaflye output: metagenomic assembly files
# Folder
ASSEMBLY_DIR="./files/C1_MetaflyeAssembly/${project_name}/${run_name}"
mkdir -p ${ASSEMBLY_DIR}
# Files
ASSEMBLY_FASTA="${ASSEMBLY_DIR}/assembly.fasta"  # named automatically
CONTIG_READ_BAM="${ASSEMBLY_DIR}/${run_name}_contigreadmap.bam"


###########################################################
##### LONG-READ METAGENOMIC ASSEMBLY AND READ MAPPING #####

## Perform metagenomic assembly with metaflye
# Include 3 polishing rounds, use 10 threads
conda activate metaflye
echo "Starting metaflye assembly. Using input file ${ANALYSIS_FA}."
srun flye --meta --nano-hq ${ANALYSIS_FA} --out-dir ${ASSEMBLY_DIR} -t 10 -i 3
wait
echo "Completed metaflye assembly for run ${run_name}. Results in ${ASSEMBLY_DIR}."

## Map the reads back to the contigs
conda activate samtools
echo "Starting read-contig mapping. Using minimap2 on input files: ${ANALYSIS_BAM} and ${ASSEMBLY_FASTA}."
srun samtools fastq -T MM,ML ${ANALYSIS_BAM} | \
  minimap2 -ax map-ont -t 10 -y ${ASSEMBLY_FASTA} - | \
  samtools view -bS | \
  samtools sort -o ${CONTIG_READ_BAM}
wait
echo "Completed read-contig mapping for run ${run_name}. Results in ${CONTIG_READ_BAM}."

# Index the bam file for usage with Modkit pileup
samtools index ${CONTIG_READ_BAM}
echo "Indexed ${CONTIG_READ_BAM}."

echo "DONE."
