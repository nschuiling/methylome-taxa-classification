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

# Rank and model to analyse
rank="species"  # 'species' or 'genus'
classifier="random_forest"  # 'svc_linear' or 'random_forest'


# Input folders and files
test_performance_folder="./files/G6_TestSetsPerformance"
holdout_folder="./files/G1_TrainTestData"
independent_folder="./files/G1b_ValidationApplicationData"
pickle_taxon_dictionaries="../PartF_ExplorationPreprocessing/files/F2_TaxonomyDictsTrees/Samples1-5_dictionaries.tsv"


# Output folder
output_folder="./files/G6b_TestSetsPerformancesPlots"
mkdir -p ${output_folder}


###################################
##### CREATE COMPARISON PLOTS #####

echo "Starting performance evaluation."
python G6b_TestSetPlots.py ${rank} ${classifier} ${test_performance_folder} ${holdout_folder} ${independent_folder} ${pickle_taxon_dictionaries} ${output_folder}
echo "Finished evaluation. Results in ${output_folder}."

echo "DONE."



