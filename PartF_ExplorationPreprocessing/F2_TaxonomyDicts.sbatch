#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=01:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=200GB                                  

# Save errors and logs
#SBATCH --output=./slurmlog/F2-slurm-%j.err
#SBATCH --error=./slurmlog/F2-slurm-%j.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartF_ExplorationPreprocessing"

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate taxoniq


######################################################
##### DEFINE INPUT AND OUTPUT FILES AND SETTINGS #####

## Input: the complete and annotated profile with all samples combined
# Folder
COMBINED_DIR="../PartE_ProfileAnnotation/files/E5_CombinedProfile/"
# Files
COMBINED_PROFILE="${COMBINED_DIR}/Samples1-5_profiles_combined_top50.tsv"
TOP50_SPECIES_LIST="../PartE_ProfileAnnotation/files/E5_CombinedProfile/Samples1-5_top50_species.list"

## Output: dictionaries to map all taxa id's to names, and phylogenetic trees
# Folder
OUT_DIR="./files/F2_TaxonomyDictsTrees"
mkdir -p ${OUT_DIR}
# File
TAXONOMIC_DICT_FILE="${OUT_DIR}/Samples1-5_dictionaries.tsv"


###############################
##### CREATE DICTIONARIES #####

echo "Creating taxonomic dictionaries for the completed combined profile ${COMBINED_PROFILE}."
python F2a_TaxonomyDicts.py ${COMBINED_PROFILE} ${TAXONOMIC_DICT_FILE}
echo "Done creating taxonomic dictionaries. Result in ${TAXONOMIC_DICT_FILE}."

echo "Creating phylogenetic trees for the included taxa."
python F2b_TaxonomicTrees.py ${OUT_DIR} ${TOP50_SPECIES_LIST}
echo "Done creating phylogenetic trees. Results in ${OUT_DIR}."

wait
echo "DONE."