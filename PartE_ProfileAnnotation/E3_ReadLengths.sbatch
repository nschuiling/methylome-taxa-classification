#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=40GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/E3-slurm-%A_%a.out
#SBATCH --error=./slurmlog/E3-slurm-%A_%a.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartE_ProfileAnnotation"

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.9/etc/profile.d/conda.sh
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


##############################################
##### DEFINE INPUT AND OUTPUT FILE PATHS #####

# Input: QC-filtered basecalled bam file
# Folder
QC_FILTERED_DIR="../PartA_DataCollection/files/A5_QCFilteredBasecalls/${project_name}/${run_name}"
# File path
ANALYSIS_BAM="${QC_FILTERED_DIR}/${run_name}_analysis.bam"

## Output: read lengths per read
# Folder
READ_LENGTHS_DIR="./files/E3_ReadLenths/${project_name}/${run_name}"
mkdir -p ${READ_LENGTHS_DIR}
# File
READ_LENGTHS_FILE="${READ_LENGTHS_DIR}/${run_name}_readlengths.tsv"


####################################################
##### READ LENGTH EXTRACTION FOR NORMALIZATION #####

## Run read length extraction
echo "Starting read length extraction for run ${run_name} using file ${ANALYSIS_BAM}."
# Create .tsv with one column for read_id and one for read_length
srun samtools view -h ${ANALYSIS_BAM} | awk '!/^@/ && length($10) > 0 {print $1 "\t" length($10)}' > ${READ_LENGTHS_FILE}
wait
# Add column names to the final output
srun echo -e "read_id\tread_length" | cat - ${READ_LENGTHS_FILE} > temp && mv temp ${READ_LENGTHS_FILE}
wait
echo "Finished read length extraction for run ${run_name}. Results written to: ${READ_LENGTHS_FILE}." 

echo "DONE."
