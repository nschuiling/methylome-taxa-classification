#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=00:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=200GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/E4-slurm-%A_%a.out
#SBATCH --error=./slurmlog/E4-slurm-%A_%a.err

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

# The data consists of multiple datasets (samples/runs) for different projects
# The configuration file contains all information for the analysis of each dataset
config="../configurations/allprojects.config"

# The following projects are in the config file (accessable via #SBATCH --array=xx above):
# "CHEESE_PRJEB58160" (--array=1-3), "NANOMOTIF_PRJEB74343" (--array=4-7), "DBL_SAMPLES" (--array=8-15)

# Define the run specifications using the current array position
project_name=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $2}' ${config})
run_name=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $3}' ${config})
data_url=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $4}' ${config})
data_size=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $5}' ${config})
data_type=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $6}' ${config})
basecall_model=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $7}' ${config})

# Print which data will be analysed
echo "Project: ${project_name}. Run: ${run_name}."


##############################################
##### DEFINE INPUT AND OUTPUT FILE PATHS #####

## Input: methylation profile
# Folder
METHYLATED_PROFILE_DIR="../PartD_MethylationProfiling/files/D3_FullMethylationProfile/${project_name}/${run_name}"
# File
METHYLATED_PROFILE_FULL="${METHYLATED_PROFILE_DIR}/methylated_profile_kmax12_5mC_6mA.tsv"

## Input: read taxonomies
# Folder
RANKS_DIR="./files/E2_TaxonomicRanks/${project_name}/${run_name}"
# File
TSV_TAXONOMIC_RANKS="${RANKS_DIR}/${run_name}_taxonomy_SGF.tsv"

## Input: read lengths
# Folder
READ_LENGTHS_DIR="./files/E3_ReadLenths/${project_name}/${run_name}"
# File
TSV_READ_LENGTHS="${READ_LENGTHS_DIR}/${run_name}_readlengths.tsv"

## Output: annotated profile
# Folder
PROFILE_DIR="./files/E4_CompleteProfiles/${project_name}/${run_name}"
mkdir -p ${PROFILE_DIR}
# File
ANNOTATED_PROFILE="${PROFILE_DIR}/${run_name}_completeprofile.tsv"


##############################
##### PROFILE COMPLETION ##### 
 
## Profile annotation
echo "Starting profile annotation using the files ${METHYLATED_PROFILE_FULL}, ${TSV_TAXONOMIC_RANKS}, and ${TSV_READ_LENGTHS}."
python E4_ProfileAnnotation.py ${METHYLATED_PROFILE_FULL} ${TSV_TAXONOMIC_RANKS} ${TSV_READ_LENGTHS} ${ANNOTATED_PROFILE} ${run_name}
wait
echo "Finished profile annotation. Output in ${ANNOTATED_PROFILE}."

echo "DONE."