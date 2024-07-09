#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=00:05:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=20GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/E6-slurm-%A_%a.out
#SBATCH --error=./slurmlog/E6-slurm-%A_%a.err

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
conda activate methylationprofiling

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


###################################
##### INPPUT AND OUTPUT FILES #####

## Input: annotated profile
# Folder
PROFILE_DIR="./files/E4_CompleteProfiles/${project_name}/${run_name}"
# File
ANNOTATED_PROFILE="${PROFILE_DIR}/${run_name}_completeprofile.tsv"

## Input: top 50 species list
# Folder
COMBINED_DIR="./files/E5_CombinedProfile/"
# File
LIST_SPECIES="${COMBINED_DIR}/Samples1-5_top50_species.list"

## Output: normalized profile with only top 50 species (present in training dataset)
VALAPP_DIR="./files/E6_ValidationApplicationProfiles/${project_name}/${run_name}"
mkdir -p ${VALAPP_DIR}
VALAPP_PROFILE="${VALAPP_DIR}/${run_name}_normalized_top50.tsv"


################################
##### PROFILE NORMALIZATON ##### 
 
echo "Starting profile normalization and filtering, using the files ${ANNOTATED_PROFILE}, and ${LIST_SPECIES}."
python E6_ValidationNormalization.py ${ANNOTATED_PROFILE} ${LIST_SPECIES} ${VALAPP_PROFILE}
wait
echo "Finished profile normalization and filtering. Output in ${VALAPP_PROFILE}."

echo "DONE."