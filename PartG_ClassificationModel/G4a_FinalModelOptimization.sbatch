#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

# See 'man sbatch' for more information on setting the parameters)

#SBATCH --partition=general
#SBATCH --qos=long
#SBATCH --time=55:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=350GB

# Save errors and logs
#SBATCH --output=./slurmlog/G4a-slurm-%j.out 
#SBATCH --error=./slurmlog/G4a-slurm-%j.err    

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
# Classification rank level: "species" or "genus" or "family"
# Classifier: 'random_model', 'random_forest', 'mlp','svc_linear', 'elastic_net', 'svc_nonlinear', 'knn', or 'naivebayes'
# Optuna trials: nr of different settings tried per classifier
# Repetition nr: the same settings can be run multiple times to obtain more robust results
rank_level="genus"
classifier_to_evaluate="svc_linear"
settings_nr=100
optuna_trials=100   # SET TO 100

## Define output folder
output_folder="./files/G4_FinalModelSettings/${rank_level}/${classifier_to_evaluate}"
mkdir -p ${output_folder}


#############################################
##### RUN THE OPTUNA OPTIMIZATION STUDY #####

echo "Running model optimization and evaluation studies for the classifier ${classifier_to_evaluate}, on rank ${rank_level}, on the data from ${Xy_prefix}. Using ${optuna_trials} trials."
python G4a_FinalModelOptimization.py ${Xy_prefix} ${rank_level} ${classifier_to_evaluate} ${output_folder} ${optuna_trials} ${settings_nr}

wait
echo "Results in ${output_folder}."
echo "DONE."
