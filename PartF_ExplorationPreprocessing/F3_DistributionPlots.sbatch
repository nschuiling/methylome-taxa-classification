#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=03:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=1000GB                                  

# Save errors and logs
#SBATCH --output=./slurmlog/F3-slurm-%j.err
#SBATCH --error=./slurmlog/F3-slurm-%j.err

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
conda activate dataexploration


######################################################
##### DEFINE INPUT AND OUTPUT FILES AND SETTINGS #####

# The complete, combined profiles
COMBINED_DIR="../PartE_ProfileAnnotation/files/E5_CombinedProfile/"
#COMBINED_PROFILE="${COMBINED_DIR}/Samples1-5_profiles_combined.tsv"
TOP50_PROFILE="${COMBINED_DIR}/Samples1-5_profiles_combined_normalized_top50.tsv"

# All read numbers for different analysis stages
NREADS_DIR="./files/F1_ReadsPerSample"
NREADS_FILE="${NREADS_DIR}/Samples1-5_nreads.tsv"

# File with dictionaries to map taxon id's to taxon names
DICTS_DIR="./files/F2_TaxonomyDictsTrees"
DICT_FILE="${DICTS_DIR}/Samples1-5_dictionaries.tsv"

# Folder to save the figures to
PLOTS_DIR="./files/F3_DistributionsPlots"
mkdir -p ${PLOTS_DIR}
PNG_PREFIX="${PLOTS_DIR}/Top50"

echo "Creating plots for the completed combined profile ${TOP50_PROFILE}, with numbers of reads ${NREADS_FILE}."
python F3_DistributionsPlots.py ${NREADS_FILE} ${TOP50_PROFILE} ${PNG_PREFIX} ${DICT_FILE}

wait
echo "Results in ${PNG_PREFIX}."
echo "DONE."