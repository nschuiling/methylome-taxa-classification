#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

# See 'man sbatch' for more information on setting the parameters)

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=00:05:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=40GB

# Save errors and logs
#SBATCH --output=./slurmlog/G6-slurm-%j.out 
#SBATCH --error=./slurmlog/G6-slurm-%j.err    

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
Xy_holdout_prefix="./files/G1_TrainTestData/Top50NormalizedProfile"
Xy_independent_prefix="./files/G1b_ValidationApplicationData/ZYMOMOCK_DBL"

## Analysis settings (make sure they align with the model!):
rank_level="genus"              # "genus" or "species"
classifier="svc_linear"      # "random_forest" or "svc_linear"
trained_classifier_path="./files/G5_FinalTrainedModel/${classifier}_${rank_level}.pkl"

## Define output folder
evaluation_folder="./files/G6_TestSetsPerformance"
mkdir -p ${evaluation_folder}
evaluation_output_prefix="${evaluation_folder}/${classifier}_${rank_level}"


#############################################
##### RUN THE OPTUNA OPTIMIZATION STUDY #####

echo "Evaluatimg the final model (${trained_classifier_path}) on rank ${rank_level}, on the data from ${Xy_holdout_prefix} and ${Xy_independent_prefix}."
python G6_TestSetsEvaluation.py ${Xy_holdout_prefix} ${Xy_independent_prefix} ${rank_level} ${trained_classifier_path} ${evaluation_output_prefix}

wait
echo "Resulting model in ${evaluation_output_prefix}."
echo "DONE."
