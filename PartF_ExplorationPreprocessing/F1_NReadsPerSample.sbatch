#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=01:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=20GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/F1-slurm-%A_%a.out
#SBATCH --error=./slurmlog/F1-slurm-%A_%a.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartF_ExplorationPreprocessing"

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate samtools

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


##############################################################
##### RETRIEVE NR OF READS FOR DIFFERENT ANALYSIS STAGES #####

# Pre-QC-filter bam file
BASECALLS_DIR="../PartA_DataCollection/files/A3_BamBasecalls/${project_name}/${run_name}"
UNFILTERED_BAM="${BASECALLS_DIR}/${run_name}.bam"
# Nr of reads
basecalled_reads=$( samtools view -c ${UNFILTERED_BAM} )
echo ${basecalled_reads}

# Post-QC-filter bam
QC_FILTERED_DIR="../PartA_DataCollection/files/A5_QCFilteredBasecalls/${project_name}/${run_name}"
ANALYSIS_BAM="${QC_FILTERED_DIR}/${run_name}_analysis.bam"
# Nr of reads
filtered_reads=$( samtools view -c ${ANALYSIS_BAM} )
echo ${filtered_reads}

# Methylation profiled reads
METHYLATED_PROFILE_DIR="../PartD_MethylationProfiling/files/D3_FullMethylationProfile/${project_name}/${run_name}"
METHYLATED_PROFILE_FULL="${METHYLATED_PROFILE_DIR}/methylated_profile_kmax12_5mC_6mA.tsv"
# Nr of reads
profiled_reads=$( awk 'END { print NR - 1 }' ${METHYLATED_PROFILE_FULL} )
echo ${profiled_reads}

# Taxonomic annotated reads
TAXONOMY_DIR="../PartE_ProfileAnnotation/files/E1_TaxonomicAnnotation/${project_name}/${run_name}"
MEGAN_INFO="${TAXONOMY_DIR}/${run_name}_minimap2megan.tsv"
# Nr of reads
taxon_reads=$( awk 'END { print NR - 1 }' ${MEGAN_INFO} )
echo ${taxon_reads}

# Annotation at species level
PROFILE_DIR="../PartE_ProfileAnnotation/files/E4_CompleteProfiles/${project_name}/${run_name}"
ANNOTATED_PROFILE="${PROFILE_DIR}/${run_name}_completeprofile.tsv"
# Nr of reads
species_reads=$( awk 'END { print NR - 1 }' ${ANNOTATED_PROFILE} )
echo ${species_reads}

# Nr of reads amongst the top 50 species
# ADD MANUALLY TO OUTPUT (df shape from the complete profiles per sample)

# Output file to save all read numbers to
# Folder
NREADS_DIR="./files/F1_ReadsPerSample"
mkdir -p ${NREADS_DIR}
# File
NREADS_FILE="${NREADS_DIR}/Sample8_nreads.tsv"

## Add all numbers to the output .tsv file
# Write a header only once (when the file does not exist yet)
if [ ! -f ${NREADS_FILE} ]; then
    echo -e "run_name\tbasecalled_reads\tfiltered_reads\tprofiled_reads\ttaxon_reads\tspecies_reads" >> ${NREADS_FILE}
fi
echo -e "${run_name}\t${basecalled_reads}\t${filtered_reads}\t${profiled_reads}\t${taxon_reads}\t${species_reads}" >> ${NREADS_FILE}

