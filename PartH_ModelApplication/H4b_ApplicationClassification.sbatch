#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=00:15:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=40GB

# Save errors and logs
#SBATCH --output=./slurmlog/H4b-slurm-%j.out 
#SBATCH --error=./slurmlog/H4b-slurm-%j.err    

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_JOB_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####


## RUN THIS SCRIPT FOR THE ADDITIONAL APPLICATION SAMPLES (samples 9-15)


# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartH_ModelApplication"

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


## RUN THIS SCRIPT FOR THE ADDITIONAL APPLICATION SAMPLES (samples 9-15)


## Input data: application data
X_data="./files/H4_CombinedApplicationProfiles/ApplicationSamples9-15_profiles_combined_normalized.npy"

## Analysis settings (make sure they align with the model!):
rank_level="genus"              # "genus" or "species"
classifier="svc_linear"         # "random_forest" or "svc_linear"
trained_classifier_path="../PartG_ClassificationModel/files/G5_FinalTrainedModel/${classifier}_${rank_level}.pkl"

## Define output folder
predictions_folder="./files/H4b_ApplicationPredictions"
mkdir -p ${predictions_folder}
predictions_output_prefix="${predictions_folder}/${classifier}_${rank_level}"


#############################################
##### RUN THE OPTUNA OPTIMIZATION STUDY #####

echo "Applying the final model (${trained_classifier_path}) on rank ${rank_level}, on the data from ${X_data}."
python H4b_ApplicationClassification.py ${X_data} ${rank_level} ${trained_classifier_path} ${predictions_output_prefix}

wait
echo "Resulting predictions in ${predictions_output_prefix}."
echo "DONE."
