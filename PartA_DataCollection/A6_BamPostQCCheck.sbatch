#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=12
#SBATCH --mem=20GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/A6-slurm-%A_%a.out
#SBATCH --error=./slurmlog/A6-slurm-%A_%a.err

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
module load FastQC
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate nanoplot

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

## Input: QC-filtered basecalled bam file
# Folder
QC_FILTERED_DIR="./files/A5_QCFilteredBasecalls/${project_name}/${run_name}"
# File
ANALYSIS_BAM="${QC_FILTERED_DIR}/${run_name}_analysis.bam"

## Output: QC-checks of basecalls
# Folder
QC_CHECK_DIR="./files/A6_PostQCCheckBasecalls/${project_name}/${run_name}"
mkdir -p ${QC_CHECK_DIR}


###############################################################
##### QUALITY CONTROL PLOTTING OF POST-FILTERED .BAM FILES #####

## Nanoplot quality control
echo "Starting Nanoplot quality control."
srun NanoPlot -o "${QC_CHECK_DIR}/nanoplot" \
         -p "${run_name}_" \
         --tsv_stats --huge --verbose -t 10 \
         --N50 \
         --font_scale 1.5 \
         --title "${run_name}" \
         -c "seagreen" \
         --info_in_report \
         --ubam ${ANALYSIS_BAM}
wait
echo "Finished Nanoplot quality control. Output in ${QC_CHECK_DIR}/nanoplot."

## FastQC quality control
echo "Starting FastQC quality control."
srun fastqc -t 10 -o ${QC_CHECK_DIR} ${ANALYSIS_BAM}
wait

# Unzipping gives errors (which are okay, but will stop this script).
# So perform unzipping manually
echo "Manually unzip the FastQC results and remove the zipped file."
echo "Unzip command: unzip ${QC_CHECK_DIR}/${run_name}_analysis_fastqc.zip -d ${QC_CHECK_DIR}"
echo "And then: rm ${QC_CHECK_DIR}/${run_name}_fastqc.zip"

echo "DONE."
