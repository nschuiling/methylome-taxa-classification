#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=800GB

# Save errors and logs
#SBATCH --output=./slurmlog/G1a-slurm-%j.out 
#SBATCH --error=./slurmlog/G1a-slurm-%j.err    

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_JOB_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartG_ClassificationModel"

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate classification


######################################################
##### DEFINE INPUT AND OUTPUT FILES AND SETTINGS #####

# Input: The complete, combined profiles (normalized, only top50 species)
COMBINED_DIR="../PartE_ProfileAnnotation/files/E5_CombinedProfile/"
TOP50_PROFILE="${COMBINED_DIR}/Samples1-5_profiles_combined_normalized_top50.tsv"

## Output dir
TRAINTEST_DIR="./files/G1_TrainTestData"
mkdir -p ${TRAINTEST_DIR}
output_folder_and_prefix="${TRAINTEST_DIR}/Top50NormalizedProfile"


###################################################################
##### CREATE A TRAIN-TEST SPLIT ON THE MODEL BUILDING DATASET #####

## Preprocessing
echo "Starting train-test split of file ${TOP50_PROFILE}."
python G1a_TrainTestSplit.py ${TOP50_PROFILE} ${output_folder_and_prefix}
wait
echo "Finished train-test split. Files in ${output_folder_and_prefix}."

echo "DONE."