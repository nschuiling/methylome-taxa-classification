#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=01:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=800GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/D3-slurm-%A_%a.out
#SBATCH --error=./slurmlog/D3-slurm-%A_%a.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartD_MethylationProfiling"

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
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


##############################################
##### DEFINE INPUT AND OUTPUT FILE PATHS #####

## Input: methylation profiles for 5mC and 6mA methylations per read
# Folder
METHYLATED_MOTIFS_DIR="./files/D2_MethylatedMotifs/${project_name}/${run_name}"
# Files
METHYLATED_PROFILE_5mC="${METHYLATED_MOTIFS_DIR}/methylated_profile_kmax12_5mC.tsv"
METHYLATED_PROFILE_6mA="${METHYLATED_MOTIFS_DIR}/methylated_profile_kmax12_6mA.tsv"

## Output: merged profile (5mC and 6mA methylation in one vector per read)
# Folder
METHYLATED_PROFILE_DIR="./files/D3_FullMethylationProfile/${project_name}/${run_name}"
mkdir -p ${METHYLATED_PROFILE_DIR}
# File
METHYLATED_PROFILE_FULL="${METHYLATED_PROFILE_DIR}/methylated_profile_kmax12_5mC_6mA.tsv"


#################################################################
##### CREATING A COMBINED (5mC and 6mA) METHYLATION PROFILE #####

## Join the methylation profiles per read
echo "Merging the 5mC and 6mA methylation profiles, using ${METHYLATED_PROFILE_5mC} and ${METHYLATED_PROFILE_6mA}."
python D3_MergeProfiles.py ${METHYLATED_PROFILE_5mC} ${METHYLATED_PROFILE_6mA} ${METHYLATED_PROFILE_FULL}
wait
echo "Finished the merged methylation profile. Results in ${METHYLATED_PROFILE_FULL}."

echo "DONE."