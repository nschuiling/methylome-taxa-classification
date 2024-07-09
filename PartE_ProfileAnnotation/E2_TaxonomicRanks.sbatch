#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=00:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=20GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/E2-slurm-%A_%a.out
#SBATCH --error=./slurmlog/E2-slurm-%A_%a.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartE_ProfileAnnotation"

# Load necessary modules and virtual environments
module use /opt/insy/modulefiles
module use /opt/insy/modules/DBL/modulefiles
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate taxoniq

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

## Input: taxonomic annotation of reads from the MEGAN-LR pipeline
# Folder
TAXONOMY_DIR="./files/E1_TaxonomicAnnotation/${project_name}/${run_name}"
# Files
MEGAN_RMA="${TAXONOMY_DIR}/${run_name}_minimap2megan.rma"
MEGAN_INFO="${TAXONOMY_DIR}/${run_name}_minimap2megan.tsv"


## Output: files with read annotations at Family, Species, and Genus rank
# Folder
RANKS_DIR="./files/E2_TaxonomicRanks/${project_name}/${run_name}"
mkdir -p ${RANKS_DIR}
# Files
TSV_TAXONOMIC_RANKS="${RANKS_DIR}/${run_name}_taxonomy_SGF.tsv"
DICT_SPECIES="${RANKS_DIR}/${run_name}_species_dict.tsv"
DICT_GENUS="${RANKS_DIR}/${run_name}_genus_dict.tsv"
DICT_FAMILY="${RANKS_DIR}/${run_name}_family_dict.tsv"
KRONA_CHART="${RANKS_DIR}/${run_name}_krona_chart.krona.html"


##############################
##### TAXONOMIC ANALYSIS #####


## In this version, ONLY reads with at least a family rank annotation are kept


## Complete taxonomic annotation file with different ranks
echo "Starting annotations of family, genus, and species id's. Using: ${MEGAN_INFO}."
python E2_TaxonomicRanks.py ${MEGAN_INFO} ${TSV_TAXONOMIC_RANKS} ${DICT_SPECIES} ${DICT_GENUS} ${DICT_FAMILY}
wait
echo "Finished taxonomic rank annotations. Results in: ${TSV_TAXONOMIC_RANKS}."


## Create a Krona chart of the annotated reads
# https://training.galaxyproject.org/training-material/topics/microbiome/tutorials/taxonomic-profiling/tutorial.html#visualization-of-taxonomic-assignment
# https://docs.csc.fi/apps/krona/
echo "Creating a Krona chart of the annotated reads. Using: ${TSV_TAXONOMIC_RANKS}."
ktImportTaxonomy -q 1 -t 2 -s 0 -o ${KRONA_CHART} ${TSV_TAXONOMIC_RANKS} 
wait
echo "Finished Krona chart. Result: ${KRONA_CHART}."


echo "DONE."