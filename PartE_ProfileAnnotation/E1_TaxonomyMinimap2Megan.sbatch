#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=long
#SBATCH --time=72:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=60
#SBATCH --mem=500GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/E1-slurm-%A_%a.out
#SBATCH --error=./slurmlog/E1-slurm-%A_%a.err

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
source /opt/insy/miniconda/3.9/etc/profile.d/conda.sh
conda activate samtools

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
QC_FILTERED_DIR="../PartA_DataCollection/files/A5_QCFilteredBasecalls/${project_name}/${run_name}"
# File
ANALYSIS_FA="${QC_FILTERED_DIR}/${run_name}_analysis.fasta"

## Input: reference database (NCBI nt prokaryotes and megan map)
# Folder
DATABASE_DIRECTORY="../PartB_ReferenceCollection/databases"
# Databases
NCBI_NTPROK_MMI="${DATABASE_DIRECTORY}/nt_prok.mmi"
MEGAN_MAP="${DATABASE_DIRECTORY}/megan-nucl-Feb2022.db"

## Output: taxonomic annotations per read
# Folder
TAXONOMY_DIR="./files/E1_TaxonomicAnnotation/${project_name}/${run_name}"
mkdir -p ${TAXONOMY_DIR}
# Folder for intermediate files
TMP_DIR="${TAXONOMY_DIR}/tmp"
mkdir -p ${TMP_DIR}
# Intermediate files
ALL_READS_SAM="${TMP_DIR}/${run_name}_minimap2allreads.sam"
ALIGNED_SAM="${TMP_DIR}/${run_name}_minimap2aligned.sam"
# Output files
MEGAN_RMA="${TAXONOMY_DIR}/${run_name}_minimap2megan.rma"
MEGAN_INFO="${TAXONOMY_DIR}/${run_name}_minimap2megan.tsv"


############################################################
##### MINIMAP2-MEGAN TAXONOMIC CLASSIFICATION OF READS #####

## Info:
# MEGAN-LR with minimap2: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9749362/
# https://github.com/PacificBiosciences/pb-metagenomics-tools/blob/master/docs/Tutorial-Taxonomic-Profiling-Minimap-Megan.md
# https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-022-05103-0#:~:text=the%20online%20documentation.-,MEGAN%2DLR%2Dnuc,-A%20streamlined%20workflow


## Run Minimap2 aligner
echo "Starting Minimap2 alignment of reads (${ANALYSIS_FA}) to NCBI nt_prok database (${NCBI_NTPROK_MMI})."
srun "./software/minimap2/minimap2" \
  -a -t 58 -N 100 --sam-hit-only \
  --split-prefix "${TMP_DIR}/tmp_split" \
  ${NCBI_NTPROK_MMI} ${ANALYSIS_FA} > ${ALIGNED_SAM}
wait
echo "Minimap2 alignment of ${RUN_FASTQ} to ${NCBI_NTPROK_MMI} succesful. Results in ${ALIGNED_SAM}."


## Run MEGAN sam2rma to perform taxonomic annotation
## Command/parameter breakdown:
# sam2rma: command for computing an .rma file from a .sam file
# -i ${ALIGNED_SAM}: input .sam file (from Minimap2 alignment)
# -r ${RUN_FASTQ}: reads file (original input to Minimap2)
# -o ${MEGAN_RMA}: output .rma file
# --longReads: analysis of long reads
# -alg longReads: specify taxonomic assignment LCA algorithm as the long reads algorithm
# -t 30: use 30 threats
# -mdb ${MEGAN_MAP}: MEGAN mapping database file
echo "Starting Megan sam2rma conversion."
srun "./software/megan/tools/sam2rma" \
  -i ${ALIGNED_SAM} -r ${ANALYSIS_FA} -o ${MEGAN_RMA} \
  --longReads -alg longReads -t 30 -mdb ${MEGAN_MAP}
wait
echo "Completed the sam2rma conversion. Results in ${MEGAN_RMA}."


## Run MEGAN rma2info to extract taxonomic annotation per read
## Command/parameter breakdown:
# rma2info: command for .rma file analysis
# -i ${MEGAN_RMA}: input .rma file (from step above)
# -o ${MEGAN_INFO}: output .tsv file
# -r2c Taxonomy: output read-to-class assignments
# -mro -r: only use major taxonomic ranks and report the assigned rank
# OPTIONAL: [-n true] to output names instead of taxonomic id's
echo "Starting Megan rma2info conversion."
srun "./software/megan/tools/rma2info" \
  -i ${MEGAN_RMA} -o ${MEGAN_INFO} -r2c Taxonomy -mro -r
wait
echo "Completed the rma2info conversion. Results in ${MEGAN_INFO}."


## Add column names to the final output
echo "Formatting the output .tsv with column names."
srun echo -e "read_id\ttaxonomic_rank\ttaxonomic_id" | \
  cat - ${MEGAN_INFO} > temp && mv temp ${MEGAN_INFO}
wait
echo "Reads annotated with taxonomic ids. Results in ${MEGAN_INFO}."


## Remove temporary files manually when results are okay
echo "Finished taxonomic annotation of run ${run_name}."
echo "Check results. Temporary files can be removed using: rm -r ${TMP_DIR}"

echo "DONE."
