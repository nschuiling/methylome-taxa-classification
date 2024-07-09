#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=600GB                                  

# Save errors and logs
#SBATCH --output=./slurmlog/E7-slurm-%j.out
#SBATCH --error=./slurmlog/E7-slurm-%j.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartE_ProfileAnnotation"

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate dataexploration


######################################################
##### DEFINE INPUT AND OUTPUT FILES AND SETTINGS #####

## Input: full combined and annotated profile
# Folder
COMBINED_DIR="./files/E5_CombinedProfile/"
# Files
COMBINED_PROFILE="${COMBINED_DIR}/Samples1-5_profiles_combined.tsv"
COMBINED_TOP50_PROFILE="${COMBINED_DIR}/Samples1-5_profiles_combined_normalized_top50.tsv"

## Output: subset of the combined profile
SUBSET_PROFILE="${COMBINED_DIR}/Samples1-5_profiles_combined_10000reads.tsv"
SUBSET_TOP50_PROFILE="${COMBINED_DIR}/Samples1-5_profiles_combined_normalized_top50_1000000reads.tsv"


##################################################
##### CREATE A SMALLER SUBSAMPLE OF THE DATA #####

# Create a subsample of the full dataset
python E7_SubSampleDF.py ${COMBINED_TOP50_PROFILE} ${SUBSET_TOP50_PROFILE}
wait


echo "DONE."
