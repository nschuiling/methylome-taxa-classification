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

# Folder with all scores
JSON_DIRECTORY="./files/G2_ModelPerformances/"

# Folder to save results to
OUTPUT_DIR="./files/G3_ClassifierComparison"
mkdir -p ${OUTPUT_DIR}
PNG_PREFIX="${OUTPUT_DIR}/SimpleModels"

# Taxon dictionaries for mapping id's to names
TAXON_DICTS="../PartF_ExplorationPreprocessing/files/F2_TaxonomyDictsTrees/Samples1-5_dictionaries.tsv"


###################################
##### CREATE COMPARISON PLOTS #####

echo "Starting classifier comparison evalluation and plotting. Using the scores from ${JSON_DIRECTORY}."
python G3_ClassifierComparison.py ${JSON_DIRECTORY} ${PNG_PREFIX} ${TAXON_DICTS}
echo "Finished classifier comparison."

echo "DONE."