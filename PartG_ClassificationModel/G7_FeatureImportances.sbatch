#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

# See 'man sbatch' for more information on setting the parameters)

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=00:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=40GB

# Save errors and logs
#SBATCH --output=./slurmlog/G7-slurm-%j.out 
#SBATCH --error=./slurmlog/G7-slurm-%j.err    

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

## Input data: test datasets (holdout and independent sample)
#Xy_holdout_prefix="./files/G1_TrainTestData/Top50NormalizedProfile"
#Xy_independent_prefix="./files/G1b_ValidationApplicationData/ZYMOMOCK_DBL"

## Analysis settings (make sure they align with the model!):
rank_level="species"           # "genus" or "species"
classifier_type="random_forest"   # "random_forest" or "svc_linear"
feature_selection="False"      # "True" or "False" --> only true for linSVM genus

trained_pipeline_path="./files/G5_FinalTrainedModel/${classifier_type}_${rank_level}.pkl"
motifs_list_file="../PartE_ProfileAnnotation/files/E5_CombinedProfile/Samples1-5_allmotifs.list"

## Define output folder
output_folder="./files/G7_FeatureImportances/${classifier}"
mkdir -p ${output_folder}
output_prefix="${output_folder}/${classifier_type}_${rank_level}"



#############################################
##### RUN THE OPTUNA OPTIMIZATION STUDY #####

echo "Evaluatimg the feature importances of the final model (${trained_pipeline_path}) on rank ${rank_level}."
python G7_FeatureImportances.py ${rank_level} ${classifier_type} ${feature_selection} ${trained_pipeline_path} ${motifs_list_file} ${output_prefix}
wait
echo "Resulting importances in ${output_prefix}."
echo "DONE."


