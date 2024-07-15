#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=00:30:00   # 00:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=150GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X

# Save errors and logs
#SBATCH --output=./slurmlog/H1-slurm-%A_%a.out
#SBATCH --error=./slurmlog/H1-slurm-%A_%a.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####


# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartH_ModelApplication"

# Load necessary modules and virtual environments
module use /opt/insy/modulefiles
module use /opt/insy/modules/DBL/modulefiles

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

## Input: Reads
# For single sample reads (validation/application samples 8-15)
#READS_FASTA="../PartA_DataCollection/files/A5_QCFilteredBasecalls/${project_name}/${run_name}/${run_name}_analysis.fasta"
# For multiple samples reads (reads from the holdout test set)
READS_FASTA="./files/H0_HoldoutReads/holdout_test_reads.fasta"  # Comment away to use single sample
run_name="HOLDOUT_TEST"                                         # Comment away to use single sample

## Input: Resistance database
RESISTANCE_DB="./resistance/nucleotide_fasta_protein_homolog_model.fasta"

## Output: ARG annotations
ARG_OUT_DIR="./files/H1_ReadAnnotationsARG/${run_name}"
mkdir -p ${ARG_OUT_DIR}
BLAST_ARG_OUT="${ARG_OUT_DIR}/${run_name}_blast_arg_90_75.txt"
HITS_ARG_OUT="${ARG_OUT_DIR}/${run_name}_blast_arg_90_75_hits.txt"


##############################
##### PROFILE COMPLETION ##### 

# For high yield samples: -perc_identity 0.9 -qcov_hsp_perc 0.75
# For low yield samples: -perc_identity 0.8 -qcov_hsp_perc 0.6
 
# Blast the reads against the ARG database
echo "Starting BLAST search of reads against ARG database."
srun blastn -db ${RESISTANCE_DB} -query ${READS_FASTA} \
-perc_identity 0.9 -qcov_hsp_perc 0.75 -outfmt 7 \
-out ${BLAST_ARG_OUT}
echo "Finished BLAST search."

# Create a hits output file
echo "Starting hits annotation from BLAST search results."
srun cat ${BLAST_ARG_OUT} | awk '/hits found/{getline;print}' | grep -v "#" | awk '{print $1,$2}' > ${HITS_ARG_OUT}
echo "Finished hits annotation."

echo "DONE." 
