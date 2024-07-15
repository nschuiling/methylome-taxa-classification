#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=medium
#SBATCH --time=10:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=6
#SBATCH --mem=1200GB

# Save errors and logs
#SBATCH --output=./slurmlog/F5-slurm-%j.out     
#SBATCH --error=./slurmlog/F5-slurm-%j.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_JOB_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####


# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartF_ExplorationPreprocessing"

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate dataexploration


######################################################
##### DEFINE INPUT AND OUTPUT FILES AND SETTINGS #####

## Input: the complete, combined methylation profiles
# Folder
COMBINED_DIR="../PartE_ProfileAnnotation/files/E5_CombinedProfile/"
# File
TOP50_PROFILE="${COMBINED_DIR}/Samples1-5_profiles_combined_normalized_top50.tsv"

## Input: file with dictionaries to map taxon id's to taxon names
# Folder
DICTS_TREES_DIR="./files/F2_TaxonomyDictsTrees"
# File
DICT_FILE="${DICTS_TREES_DIR}/Samples1-5_dictionaries.tsv"

## Input: order of the nodes in the trees
TREE_NODES_ORDER="${DICTS_TREES_DIR}/tree_orders_dict.pkl"

# Folder to save the figures to
HEATMAPS_DIR="./files/F5_Heatmaps"
mkdir -p ${HEATMAPS_DIR}


###########################
##### CREATE HEATMAPS #####

echo "Creating heatmaps for the completed combined profile ${TOP50_PROFILE}."
python F5_ProfileHeatmaps.py ${TOP50_PROFILE} ${DICT_FILE} ${TREE_NODES_ORDER} ${DICTS_TREES_DIR} ${HEATMAPS_DIR}
wait
echo "Done creating heatmaps. Results in ${HEATMAPS_DIR}."

echo "DONE."
