#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=00:10:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=10GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=9-15

# Save errors and logs
#SBATCH --output=./slurmlog/H3-slurm-%A_%a.out
#SBATCH --error=./slurmlog/H3-slurm-%A_%a.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####


## RUN THIS SCRIPT FOR THE ADDITIONAL APPLICATION SAMPLES (samples 9-15)


# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartH_ModelApplication"

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.9/etc/profile.d/conda.sh
conda activate methylationprofiling

# The data consists of multiple samples for different projects
# The configuration file contains all information for the analysis of each dataset
config="../configurations/allprojects.config"

# The following projects are in the config file (accessable via #SBATCH --array=xx above):
# "CHEESE_PRJEB58160" (--array=1-3), "NANOMOTIF_PRJEB74343" (--array=4-7), "DBL_SAMPLES" (--array=8)

# Define the run specifications using the current array position
project_name=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $2}' ${config})
run_name=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $3}' ${config})
data_url=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $4}' ${config})
data_size=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $5}' ${config})
data_type=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $6}' ${config})
basecall_model=$(awk -v ArrayTaskID=${SLURM_ARRAY_TASK_ID} '$1==ArrayTaskID {print $7}' ${config})

echo "Project: ${project_name}. Run: ${run_name}."


###################################
##### INPPUT AND OUTPUT FILES #####


## RUN THIS SCRIPT FOR THE ADDITIONAL APPLICATION SAMPLES (samples 9-15)


## Input: Methylation profile
# Folder
METHYLATED_PROFILE_DIR="../PartD_MethylationProfiling/files/D3_FullMethylationProfile/${project_name}/${run_name}"
# File
METHYLATED_PROFILE_FULL="${METHYLATED_PROFILE_DIR}/methylated_profile_kmax12_5mC_6mA.tsv"

## Input: read taxonomies
# Folder
#RANKS_DIR="../PartE_ProfileAnnotation/files/E2_TaxonomicRanks/${project_name}/${run_name}"
RANKS_DIR="../PartE_ProfileAnnotation/files/E2b_TaxonomicRanks_keepall/${project_name}/${run_name}"
# File
TSV_TAXONOMIC_RANKS="${RANKS_DIR}/${run_name}_taxonomy_SGF.tsv"

## Input: read lengths
# Folder
READ_LENGTHS_DIR="../PartE_ProfileAnnotation/files/E3_ReadLenths/${project_name}/${run_name}"
# File
TSV_READ_LENGTHS="${READ_LENGTHS_DIR}/${run_name}_readlengths.tsv"

## Input: MGE annotations
# Folder
MGE_DIR="./files/H2_ReadAnnotationsMGEs/${run_name}"
# File
TSV_MGEs="${MGE_DIR}/${run_name}_plasmid_scores.tsv"

## Input: ARG annotations
# Folder
ARG_DIR="./files/H1_ReadAnnotationsARG/${run_name}"
# File
TSV_ARGs="${ARG_DIR}/${run_name}_blast_arg_hits.txt"


## Output: annotated profile
# Folder
PROFILE_DIR="./files/H3_CompleteProfilePerSample"
mkdir -p ${PROFILE_DIR}
ANNOTATED_PROFILE="${PROFILE_DIR}/${run_name}_completeprofile.tsv"
PROFILE_NUMPY="${PROFILE_DIR}/${run_name}_X.npy"


##############################
##### PROFILE COMPLETION ##### 
 

##### Profile annotation
echo "Starting profile annotation using the files ${METHYLATED_PROFILE_FULL}, ${TSV_TAXONOMIC_RANKS}, ${TSV_READ_LENGTHS}, ${TSV_MGEs}, ${TSV_ARGs}."
python H3_PerSampleAnnotateNormalize.py ${run_name} ${METHYLATED_PROFILE_FULL} ${TSV_TAXONOMIC_RANKS} ${TSV_READ_LENGTHS} ${TSV_MGEs} ${TSV_ARGs} ${ANNOTATED_PROFILE} ${PROFILE_NUMPY}
wait
echo "Finished profile annotation. Output in ${ANNOTATED_PROFILE} and ${PROFILE_NUMPY}."


