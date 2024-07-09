#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=4GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/A2-slurm-%A_%a.out
#SBATCH --error=./slurmlog/A2-slurm-%A_%a.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartA_DataCollection"

# Load necessary modules and virtual environments
module use /opt/insy/modulefiles
module use /opt/insy/modules/DBL/modulefiles
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate fast5pod5

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

## Input: Downloaded data files
# Input folder
DOWNLOADS_FOLDER="files/A1_DataDownloads/${project_name}/${run_name}/"

## Output: Downloaded data files
# Input folder
POD5_FOLDER="files/A2_Pod5Files/${project_name}/${run_name}"
mkdir -p "${POD5_FOLDER}"


#######################################################
##### CONVERT FAST5 TO POD5 FILES FOR BASECALLING #####

# The downloaded raw data comes in two different types: fast5 and pod5
# The datatypes have been specified in the configuration file
# For basecalling we need pod5 formatted data collected in one parent folder
echo "The raw data is of the type: ${data_type}."

# If the datatype is pod5 already: basecalling will be performed from the downloads folder
# This way we prevent duplicate storage
if [[ "$data_type" = "pod5" ]]; then
  echo "No need to create or collect files, basecalling will be done from the downloads folder."

# If the datatype is fast5: find all fast5 files and convert them to pod5
# The relative directory structure of the original downloads file is maintained
elif [[ "$data_type" = "fast5" ]]; then
  echo "Converting all fast5 files from the dowloads folder to pod5 format. Downloads folder: ${DOWNLOADS_FOLDER}"
  srun find "${DOWNLOADS_FOLDER}" -type f -name "*.fast5" \
  -exec pod5 convert fast5 {} --output "${POD5_FOLDER}" --one-to-one "${DOWNLOADS_FOLDER}" \;
  echo "Completed fast5 to pod5 conversion. Files in ${POD5_FOLDER}."
fi

echo "DONE."
