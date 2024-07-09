#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=00:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=800GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/E5-slurm-%A_%a.out
#SBATCH --error=./slurmlog/E5-slurm-%A_%a.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartE_ProfileAnnotation"

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.9/etc/profile.d/conda.sh
conda activate methylationprofiling


##############################################
##### DEFINE INPUT AND OUTPUT FILE PATHS #####

## Input: complete annotated methylation profiles
# Folder
PROFILE_DIR="./files/E4_CompleteProfiles"
# Files (the datasets to combine)
EL2W_ERR11004357="${PROFILE_DIR}/CHEESE_PRJEB58160/EL2W_ERR11004357/EL2W_ERR11004357_completeprofile.tsv"
OM2_ERR11168802="${PROFILE_DIR}/CHEESE_PRJEB58160/OM2_ERR11168802/OM2_ERR11168802_completeprofile.tsv"
WH1M_ERR11007628="${PROFILE_DIR}/CHEESE_PRJEB58160/WH1M_ERR11007628/WH1M_ERR11007628_completeprofile.tsv"
ZYMO_ERR13034758="${PROFILE_DIR}/NANOMOTIF_PRJEB74343/ZYMO_ERR13034758/ZYMO_ERR13034758_completeprofile.tsv"
HUMGUT_ERR13033930="${PROFILE_DIR}/NANOMOTIF_PRJEB74343/HUMGUT_ERR13033930/HUMGUT_ERR13033930_completeprofile.tsv"

## Output: combined profile (and a normalized version)
# Folder
COMBINED_DIR="./files/E5_CombinedProfile/"
mkdir -p ${COMBINED_DIR}
# File
COMBINED_PROFILE="${COMBINED_DIR}/Samples1-5_profiles_combined.tsv"
NORMALIZED_PROFILE="${COMBINED_DIR}/Samples1-5_profiles_combined_normalized.tsv"
NORMALIZED_PROFILE_TOP50="${COMBINED_DIR}/Samples1-5_profiles_combined_normalized_top50.tsv"
COMBINED_PROFILE_TOP50="${COMBINED_DIR}/Samples1-5_profiles_combined_top50.tsv"

## Output: lists of species and motifs from the final data
LIST_SPECIES="${COMBINED_DIR}/Samples1-5_top50_species.list"
LIST_MOTIFS="${COMBINED_DIR}/Samples1-5_allmotifs.list"


###############################
##### PROFILE COMBINATION ##### 

## Combine the profiles from the different samples
echo "Starting profile combination using the files ${EL2W_ERR11004357} ${OM2_ERR11168802} ${WH1M_ERR11007628} ${ZYMO_ERR13034758} ${HUMGUT_ERR13033930}."
python E5_ProfileCombination.py ${COMBINED_PROFILE} ${NORMALIZED_PROFILE} ${NORMALIZED_PROFILE_TOP50} ${COMBINED_PROFILE_TOP50} ${LIST_SPECIES} ${LIST_MOTIFS} ${EL2W_ERR11004357} ${OM2_ERR11168802} ${WH1M_ERR11007628} ${ZYMO_ERR13034758} ${HUMGUT_ERR13033930}
wait
echo "Finished profile combination. Output in ${COMBINED_PROFILE} and ${NORMALIZED_PROFILE}."

echo "DONE."

