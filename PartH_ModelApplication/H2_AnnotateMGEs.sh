#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

# See 'man sbatch' for more information on setting the parameters)

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=04:00:00   # 00:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=150GB

# To run multiple jobs with different parameters:
#SBATCH --array=8                                  # 1-x for x tasks, 1-x%y for only y tasks at a time

# Save errors and logs
#SBATCH --output=./slurmlog/H2-slurm-%A_%a.out     # name of output log. %A is SLURM_ARRAY_JOB_ID and %a is SLURM_ARRAY_TASK_ID
#SBATCH --error=./slurmlog/H2-slurm-%A_%a.err      # name of error log. %A is SLURM_ARRAY_JOB_ID and %a is SLURM_ARRAY_TASK_ID

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e

################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

#array=8

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartH_ModelApplication"

# Load necessary modules and virtual environments
module use /opt/insy/modulefiles
module use /opt/insy/modules/DBL/modulefiles
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate plasclass

# The data consists of multiple samples for different projects
# The configuration file contains all information for the analysis of each dataset
config="../configurations/allprojects.config"

# The following projects are in the config file (accessable via #SBATCH --array=xx above):
# "CHEESE_PRJEB58160" (--array=1-3), "NANOMOTIF_PRJEB74343" (--array=4-7), "DBL_SAMPLES" (--array=8)

# Define the run specifications using the current array position
project_name=$(awk -v ArrayTaskID=${array} '$1==ArrayTaskID {print $2}' ${config})
run_name=$(awk -v ArrayTaskID=${array} '$1==ArrayTaskID {print $3}' ${config})
data_url=$(awk -v ArrayTaskID=${array} '$1==ArrayTaskID {print $4}' ${config})
data_size=$(awk -v ArrayTaskID=${array} '$1==ArrayTaskID {print $5}' ${config})
data_type=$(awk -v ArrayTaskID=${array} '$1==ArrayTaskID {print $6}' ${config})
basecall_model=$(awk -v ArrayTaskID=${array} '$1==ArrayTaskID {print $7}' ${config})

echo "Project: ${project_name}. Run: ${run_name}."


###################################
##### INPPUT AND OUTPUT FILES #####

## Input: Reads
# For single sample reads (validation/application samples 8-15)
#READS_FASTA="../PartA_DataCollection/files/A5_QCFilteredBasecalls/${project_name}/${run_name}/${run_name}_analysis.fasta"
# For multiple samples reads (reads from the holdout test set)
READS_FASTA="./files/H0_HoldoutReads/holdout_test_reads.fasta"  # Comment away to use single sample
run_name="HOLDOUT_TEST"                                         # Comment away to use single sample

## Output: ARG annotations
MGE_OUT_DIR="./files/H2_ReadAnnotationsMGEs/${run_name}"
mkdir -p ${MGE_OUT_DIR}
FILE_MGE_OUT="${MGE_OUT_DIR}/${run_name}_plasmid_scores.tsv"


##############################
##### PROFILE COMPLETION ##### 
 
# Perform plpasmid scoring
echo "Starting plasmid scoring."
python "./mgeclassification/PlasClass/classify_fasta.py" -f ${READS_FASTA} -o ${FILE_MGE_OUT} -p 2
echo "Finished plasmid scoring."

echo "DONE." 

