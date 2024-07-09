#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=10
#SBATCH --mem-per-cpu=500MB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/A1-slurm-%A_%a.out
#SBATCH --error=./slurmlog/A1-slurm-%A_%a.err

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

## Input: Data url
# Retrieved above, from the config file

## Output: Downloaded data files
# Define a folder to save the downloadeds to
DOWNLOADS_FOLDER="./files/A1_DataDownloads/${project_name}/${run_name}"
mkdir -p "${DOWNLOADS_FOLDER}"


#############################
##### DOWNLOAD THE DATA #####

# Use aria2c to efficiently download the datasets
echo "Downloading the data for project ${project_name}, run ${run_name} from url: ${data_url}."
aria2c --file-allocation=none -x 10 -s 10 -d ${DOWNLOADS_FOLDER} ${data_url}
wait
echo "Download completed. Files in ${DOWNLOADS_FOLDER}."

# Report the size of the downloaded files
downloadsize=$(du -sh ${DOWNLOADS_FOLDER})
echo "Size of downloaded data is ${downloadsize}."

# Unzip the data
echo "Starting unzipping of files in ${DOWNLOADS_FOLDER}."
tar -xvzf "${DOWNLOADS_FOLDER}"/*.tar* --directory "${DOWNLOADS_FOLDER}"
wait
echo "Unzip completed. Files in ${DOWNLOADS_FOLDER}."

# To free up memory, the zipped data can be deleted
# Manually check, and remove with: rm "${DOWNLOADS_FOLDER}"/*.tar*
echo "Manually check whether the download and unzipping went correctly."
echo "If so: the zipped data can be deleted using: rm ${DOWNLOADS_FOLDER}/*.tar*"

echo "DONE."


# Note:
# The datasets from our lab ("DBL_SAMPLES" (--array=8-15)) were put in the folders  manually
