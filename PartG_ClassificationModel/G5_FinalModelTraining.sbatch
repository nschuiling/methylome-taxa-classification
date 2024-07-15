#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

# See 'man sbatch' for more information on setting the parameters)

#SBATCH --partition=general
#SBATCH --qos=medium
#SBATCH --time=24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=600GB

# Save errors and logs
#SBATCH --output=./slurmlog/G5-slurm-%j.out 
#SBATCH --error=./slurmlog/G5-slurm-%j.err    

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_JOB_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####


# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartG_ClassificationModel"

module use /opt/insy/modulefiles
module use /opt/insy/modules/DBL/modulefiles
module load cuda/12.0
module load devtoolset/8
module load intel/oneapi

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate classification


######################################################
##### DEFINE INPUT AND OUTPUT FILES AND SETTINGS #####

## Input data: training data
TRAINTEST_DIR="./files/G1_TrainTestData"
# The data was saved to the train-test folder with the prefix:
Xy_prefix="${TRAINTEST_DIR}/Top50NormalizedProfile"

## Analysis settings:
rank_level="genus"                 # "species" or "genus" 
selected_classifier="svc_linear"   # "svc_linear" or "random_forest"

## Define output folder
model_folder="./files/G5_FinalTrainedModel"
mkdir -p ${model_folder}


#############################################
##### RUN THE OPTUNA OPTIMIZATION STUDY #####

echo "Training the final model on rank ${rank_level}, on the data from ${Xy_prefix}."
python G5_FinalModelTraining.py ${Xy_prefix} ${rank_level} ${model_folder} ${selected_classifier}

wait
echo "Resulting model in ${model_folder}."
echo "DONE."

