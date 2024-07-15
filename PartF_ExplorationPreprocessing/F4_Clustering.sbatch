#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=03:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=1500GB

# Save errors and logs
#SBATCH --output=./slurmlog/F4-slurm-%j.out     
#SBATCH --error=./slurmlog/F4-slurm-%j.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_JOB_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####


# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartF_ExplorationPreprocessing"

# Load necessary modules and virtual environments
module use /opt/insy/modulefiles
module use /opt/insy/modules/DBL/modulefiles
module load cuda/12.0
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate dataexploration


######################################################
##### DEFINE INPUT AND OUTPUT FILES AND SETTINGS #####

# The complete, combined profiles
# Folder
COMBINED_DIR="../PartE_ProfileAnnotation/files/E5_CombinedProfile/"
# File
TOP50_PROFILE="${COMBINED_DIR}/Samples1-5_profiles_combined_normalized_top50.tsv"
TOP50_PROFILE="${COMBINED_DIR}/Samples1-5_profiles_combined_normalized_top50_1000000reads.tsv"

# File with dictionaries to map taxon id's to taxon names
DICTS_DIR="./files/F2_TaxonomyDictsTrees"
DICT_FILE="${DICTS_DIR}/Samples1-5_dictionaries.tsv"

# Folder to save the figures to
PLOTS_DIR="./files/F4_Clustering"
mkdir -p ${PLOTS_DIR}
PNG_PREFIX="${PLOTS_DIR}/Top50"


################################
##### PERFORM PCA AND UMAP #####

echo "Creating clustering plots for the completed combined profile ${TOP50_PROFILE}."
python F4_Clustering.py ${TOP50_PROFILE} ${DICT_FILE} ${PNG_PREFIX}

wait
echo "Results in ${PNG_PREFIX}."
echo "DONE."
