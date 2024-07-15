#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=00:05:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=20GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X

# Save errors and logs
#SBATCH --output=./slurmlog/G1b-slurm-%A_%a.out
#SBATCH --error=./slurmlog/G1b-slurm-%A_%a.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartG_ClassificationModel"

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate classification

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


######################################################
##### DEFINE INPUT AND OUTPUT FILES AND SETTINGS #####

# Input: Normalized top 50 validation/appllication profile
VALAPP_DIR="../PartE_ProfileAnnotation/files/E6_ValidationApplicationProfiles/${project_name}/${run_name}"
VALAPP_PROFILE="${VALAPP_DIR}/${run_name}_normalized_top50.tsv"

## Output dir
VALAPPDATA_DIR="./files/G1b_ValidationApplicationData"
mkdir -p ${VALAPPDATA_DIR}
output_folder_and_prefix="${VALAPPDATA_DIR}/${run_name}"


##########################################################################################
##### CREATE NUMPY REPRESENTATIONS FOR ADDITIONAL DATASETS (VALIDATION, APPLICATION) #####

## Preprocessing
echo "Starting data preparation of file ${VALAPP_PROFILE}."
python G1b_ValidationData.py ${VALAPP_PROFILE} ${output_folder_and_prefix}
wait
echo "Finished data preparation. Files in ${output_folder_and_prefix}."

echo "DONE."