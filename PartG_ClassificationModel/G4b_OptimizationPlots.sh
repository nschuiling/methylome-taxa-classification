#!/bin/sh

################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartG_ClassificationModel"

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate classification


######################################################
##### DEFINE INPUT AND OUTPUT FILES AND SETTINGS #####

classifier="svc_linear"   # "random_forest" or "svc_linear"
rank="genus"                 # "genus" or "species"

## Input: Optimization study
STUDY_FOLDER="./files/G4_FinalModelSettings/"
STUDY_FILE="${STUDY_FOLDER}/${rank}/${classifier}/${classifier}_${rank}_100trials_study.pkl"

# Folder to save results to
OUTPUT_DIR="./files/G4b_OptimizationPlots"
mkdir -p ${OUTPUT_DIR}
OUTPUT_PREFIX="${OUTPUT_DIR}/${classifier}_${rank}_100trials_study"


###########################################
##### CREATE OPTIMIZATION STUDY PLOTS #####

echo "Starting plotting for optimization study: ${STUDY_FILE}."
python G4b_OptimizationPlots.py ${STUDY_FILE} ${OUTPUT_PREFIX}
echo "Finished plotting. Results in ${OUTPUT_PREFIX}."

echo "DONE."
