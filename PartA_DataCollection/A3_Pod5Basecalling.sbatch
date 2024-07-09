#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=medium 
#SBATCH --time=12:00:00         # adjust depending on the dataset size
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=4GB
#SBATCH --gres=gpu:1            # basecalling requires a gpu

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/A3-slurm-%A_%a.out
#SBATCH --error=./slurmlog/A3-slurm-%A_%a.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Measure GPU usage of your job (initialization)
previous=$(/usr/bin/nvidia-smi --query-accounted-apps='gpu_utilization,mem_utilization,max_memory_usage,time' --format='csv' | /usr/bin/tail -n '+2') 
/usr/bin/nvidia-smi

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartA_DataCollection"

# Load necessary modules and virtual environments
module use /opt/insy/modulefiles
module use /opt/insy/modules/DBL/modulefiles
module load cuda/12.0
module list

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

## Input: Pod5 files (raw Nanopore data)
# The location of the files depends on their original format
if [[ "$data_type" = "pod5" ]]; then
  echo "Original data was of the type pod5. Basecalling happens from the files in the downloads folder."
  POD5_FOLDER="./files/A1_DataDownloads/${project_name}/${run_name}"
elif [[ "$data_type" = "fast5" ]]; then
  echo "Original data was of the type fast5. Basecalling happens from the files in the converted pod5 folder."
  POD5_FOLDER="./files/A2_Pod5Files/${project_name}/${run_name}"
fi

# Output: Basecalled .bam files
# Folder
BAM_FOLDER="./files/A3_BamBasecalls/${project_name}/${run_name}"
mkdir -p ${BAM_FOLDER}
# File
BAM_FILE="${BAM_FOLDER}/${run_name}.bam"


###################################################################
##### PERFORM BASECALLING AND METHYLATION CALLING WITH DORADO #####

echo "Starting basecalling of run ${run_name}. Using the pod5 folder: ${POD5_FOLDER}."

## Call bases and modifications with dorado
# Models compatible with the data were downloaded from dorado and rerio (see comments at the bottom of this script)
# The models to be used per dataset are specified in the .config file and used below
if [[ "$basecall_model" = "dorado" ]]; then
  echo "Performing base and modification calling with the 5khz models retrieved from Dorado."
  srun "./software/dorado-0.6.2-linux-x64/bin/dorado" basecaller --verbose --batchsize 1020 --recursive \
    --modified-bases-models "./software/dorado-0.6.2-linux-x64/models/dna_r10.4.1_e8.2_400bps_sup@v4.3.0_5mC_5hmC@v1/","./software/dorado-0.6.2-linux-x64/models/dna_r10.4.1_e8.2_400bps_sup@v4.3.0_6mA@v2/" \
     "./software/dorado-0.6.2-linux-x64/models/dna_r10.4.1_e8.2_400bps_sup@v4.3.0/" ${POD5_FOLDER} > ${BAM_FILE}
elif [[ "$basecall_model" = "rerio" ]]; then
  echo "Performing base and modification calling with the 4khz models retrieved from Rerio."
  srun "./software/dorado-0.6.2-linux-x64/bin/dorado" basecaller --verbose --batchsize 1020 --recursive \
    --modified-bases-models "./software/rerio/dorado_models/res_dna_r10.4.1_e8.2_400bps_sup@v4.0.1_5mC@v2/","./software/rerio/dorado_models/res_dna_r10.4.1_e8.2_400bps_sup@v4.0.1_6mA@v2/" \
    "./software/rerio/dorado_models/res_dna_r10.4.1_e8.2_400bps_sup@v4.0.1/" ${POD5_FOLDER} > ${BAM_FILE}
fi
wait
echo "Basecalling of run ${run_name} completed, results in file: ${BAM_FILE}."


## Check the results
# Check the sizes of the pre-basecalling (pod5) and post-basecalling (bam) files
pod5size=$(du -sh ${POD5_FOLDER})
bamsize=$(du -sh ${BAM_FILE})
echo "Size of the pod5 files = ${pod5size}. Size of the basecalled bam file = ${bamsize}."

echo "DONE."
      
# Check GPU usage of the job for resource optimization
/usr/bin/nvidia-smi --query-accounted-apps='gpu_utilization,mem_utilization,max_memory_usage,time' --format='csv' | /usr/bin/grep -v -F "$previous"


#######################################
##### PREPARATION FOR THIS SCRIPT #####

## To run this script the following had to be downloaded:
# Dorado (https://github.com/nanoporetech/dorado)
# Dorado models for base- and modificationcalling (dorado download)
# Rerio models for base- and modificationcalling (https://github.com/nanoporetech/rerio)

## Rerio models were downloaded as follows:
# cd ./software
# git clone https://github.com/nanoporetech/rerio
# rerio/download_model.py "rerio/dorado_models/res_dna_r10.4.1_e8.2_400bps_sup@v4.0.1_url"
# rerio/download_model.py "rerio/dorado_models/res_dna_r10.4.1_e8.2_400bps_sup@v4.0.1_5mC@v2_url"
# rerio/download_model.py "rerio/dorado_models/res_dna_r10.4.1_e8.2_400bps_sup@v4.0.1_6mA@v2_url"
# rerio/download_model.py "rerio/dorado_models/res_dna_r10.4.1_e8.2_400bps_sup@2023-09-22_bacterial-methylation_url"

## To ensure that each run is basecalled with the correct models, the condition (dorado / rerio) is specified in the config file
# To (double) check chemistry and flow cells of a dataset, this command can be used: pod5 inspect debug ${POD5_FILE}
