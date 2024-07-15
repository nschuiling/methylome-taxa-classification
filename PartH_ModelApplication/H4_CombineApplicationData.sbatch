#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=00:05:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=100GB

# Save errors and logs
#SBATCH --output=./slurmlog/H4-slurm-%j.out
#SBATCH --error=./slurmlog/H4-slurm-%j.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_JOB_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####


## RUN THIS SCRIPT FOR THE ADDITIONAL APPLICATION SAMPLES (samples 9-15)


# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartH_ModelApplication"

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.9/etc/profile.d/conda.sh
conda activate methylationprofiling


######################################################
##### DEFINE INPUT AND OUTPUT FILES AND SETTINGS #####


## RUN THIS SCRIPT FOR THE ADDITIONAL APPLICATION SAMPLES (samples 9-15)


## Input: Complete profiles
# Folder
PROFILE_DIR="./files/H3_CompleteProfilePerSample"
# Files
CHICKENBENTO_DBL="${PROFILE_DIR}/CHICKENBENTO_DBL_completeprofile.tsv"
CHICKENLAB_DBL="${PROFILE_DIR}/CHICKENLAB_DBL_completeprofile.tsv"
SLUDGELAB2_DBL="${PROFILE_DIR}/SLUDGELAB2_DBL_completeprofile.tsv"
LAKEBENTO_DBL="${PROFILE_DIR}/LAKEBENTO_DBL_completeprofile.tsv"
LAKELAB_DBL="${PROFILE_DIR}/LAKELAB_DBL_completeprofile.tsv"

## Output: combined normalized application profile
# Folder
COMBINED_DIR="./files/H4_CombinedApplicationProfiles"
mkdir -p ${COMBINED_DIR}
# File
COMBINED_PROFILE="${COMBINED_DIR}/ApplicationSamples9-15_profiles_combined_normalized.tsv"
NUMPY_PROFILE="${COMBINED_DIR}/ApplicationSamples9-15_profiles_combined_normalized.npy"


##############################
##### PROFILE COMPLETION ##### 
 
##### Profile annotation
echo "Starting profile combination (application data) using the files: ${CHICKENBENTO_DBL} ${CHICKENLAB_DBL} ${SLUDGELAB2_DBL} ${LAKEBENTO_DBL} ${LAKELAB_DBL} ."
python H4_CombineApplicationData.py ${COMBINED_PROFILE} ${NUMPY_PROFILE} ${CHICKENBENTO_DBL} ${CHICKENLAB_DBL} ${SLUDGELAB2_DBL} ${LAKEBENTO_DBL} ${LAKELAB_DBL}
wait
echo "Finished profile combination. Output in ${COMBINED_PROFILE} and ${NUMPY_PROFILE}."

echo "DONE."

