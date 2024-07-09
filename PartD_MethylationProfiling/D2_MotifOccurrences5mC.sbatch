#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/D2-5mC-slurm-%A_%a.out
#SBATCH --error=./slurmlog/D2-5mC-slurm-%A_%a.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartD_MethylationProfiling"

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate motifcollection

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

## Input: methylated regions in which motifs will be searched
# Folder
METHYLATED_REGIONS_DIR="./files/D1_ModkitMethylatedRegions/${project_name}/${run_name}"
# Files
METHYLATED_REGIONS_TABLE_5mC="${METHYLATED_REGIONS_DIR}/${run_name}_methylatedregions_5mC.tsv"
METHYLATED_REGIONS_TABLE_6mA="${METHYLATED_REGIONS_DIR}/${run_name}_methylatedregions_6mA.tsv"

## Input: motifs to be searched and integer-motif dictionary
# Folder
MOTIFSEARCH_DIR="../PartC_MotifIdentification/files/C4_MotifIntegers"
# Files
set_motif_integers="${MOTIFSEARCH_DIR}/SearchMotifIntegers_5mC_6mA.set"
dict_motif_integers="${MOTIFSEARCH_DIR}/SearchMotifIntegers_5mC_6mA.dict"

## Output: motifs (integer-represented) found in each read
# Folder
METHYLATED_MOTIFS_DIR="./files/D2_MethylatedMotifs/${project_name}/${run_name}"
mkdir -p ${METHYLATED_MOTIFS_DIR}
# Files
METHYLATED_INTEGERS_5mC="${METHYLATED_MOTIFS_DIR}/methylated_integers_kmax12_5mC.tsv"
METHYLATED_PROFILE_5mC="${METHYLATED_MOTIFS_DIR}/methylated_profile_kmax12_5mC.tsv"


####################################################
##### SEARCHING METHYLATED 5mC MOTIFS IN READS #####

# Find motif occurrences in the reads
echo "Starting 5mC integer-based motif searching in methylated regions, using ${METHYLATED_REGIONS_TABLE_5mC} and ${set_motif_integers}."
python D2a_MotifFinding.py ${METHYLATED_REGIONS_TABLE_5mC} ${set_motif_integers} ${METHYLATED_INTEGERS_5mC} 
wait
echo "Finished 5mC integer-based motif searching. Results in ${METHYLATED_INTEGERS_5mC}."

# Create count vectors (methylation profiles) based on the motif occurrences
echo "Starting 5mC motif-occurrence profiling, using ${METHYLATED_INTEGERS_5mC} and ${dict_motif_integers}."
python D2b_MotifProfiling.py ${METHYLATED_INTEGERS_5mC} ${dict_motif_integers} ${METHYLATED_PROFILE_5mC} 
wait
echo "Finished 5mC motif profiling. Results in ${METHYLATED_PROFILE_5mC}."

echo "DONE."
