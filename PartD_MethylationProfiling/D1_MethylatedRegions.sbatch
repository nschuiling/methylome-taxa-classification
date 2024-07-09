#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=120GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/D1-slurm-%A_%a.out
#SBATCH --error=./slurmlog/D1-slurm-%A_%a.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartD_MethylationProfiling"

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

# Input: QC-filtered basecalled bam and fastq files
# Folder
QC_FILTERED_DIR="../PartA_DataCollection/files/A5_QCFilteredBasecalls/${project_name}/${run_name}"
# Files
ANALYSIS_BAM="${QC_FILTERED_DIR}/${run_name}_analysis.bam"
ANALYSIS_FA="${QC_FILTERED_DIR}/${run_name}_analysis.fasta"

## Output: methylated sequence regions
# Folder
METHYLATED_REGIONS_DIR="./files/D1_ModkitMethylatedRegions/${project_name}/${run_name}"
mkdir -p ${METHYLATED_REGIONS_DIR}
# Folder for intermediate files
TMP_DIR="${METHYLATED_REGIONS_DIR}/tmp"
mkdir -p ${TMP_DIR}
# Intermediate files
MODKIT_CALLS_TABLE="${TMP_DIR}/${run_name}_modkit_calls.tsv"
METHYLATED_BASES_TABLE_6mA="${TMP_DIR}/${run_name}_modkit_6mA.tsv"
METHYLATED_BASES_TABLE_5mC="${TMP_DIR}/${run_name}_modkit_5mC.tsv"
# Output files
METHYLATED_REGIONS_TABLE_6mA="${METHYLATED_REGIONS_DIR}/${run_name}_methylatedregions_6mA.tsv"
METHYLATED_REGIONS_TABLE_5mC="${METHYLATED_REGIONS_DIR}/${run_name}_methylatedregions_5mC.tsv"
METHYLATED_REGIONS_FASTA_6mA="${METHYLATED_REGIONS_DIR}/${run_name}_methylatedregions_6mA.fasta"
METHYLATED_REGIONS_FASTA_5mC="${METHYLATED_REGIONS_DIR}/${run_name}_methylatedregions_5mC.fasta"


##############################################################
##### EXTRACT BASE MODIFICATION DATA, K-MERS, AND MOTIFS #####

## Run Modkit to extract the methylated bases and surrounding kmers
echo "Starting methylation calling of run ${run_name}, using file ${ANALYSIS_BAM}."
srun "./software/modkit_v0.2.6_centos7_x86_64/modkit" extract --force \
  --ignore-index --ignore-implicit --kmer-size 44 --filter-threshold 0.7 --ignore "h" \
  -t 10 \
  --read-calls ${MODKIT_CALLS_TABLE} ${ANALYSIS_BAM} null
wait
echo "Modkit calls table created:"
head ${MODKIT_CALLS_TABLE}


## Filter modifications by presence/type and probability
echo "Filtering 5mC methylated bases."
srun awk -v kmersize=44 '($12 != "-" && $12 != "call_code") && $16 == "C" && $18 == "false" && length(gensub("-", "", "g", $15)) == kmersize' ${MODKIT_CALLS_TABLE} > ${METHYLATED_BASES_TABLE_5mC}
wait
# 6mA
echo "Filtering 6mA methylated bases."
srun awk -v kmersize=44 '($12 != "-" && $12 != "call_code") && $16 == "A" && $18 == "false" && length(gensub("-", "", "g", $15)) == kmersize' ${MODKIT_CALLS_TABLE} > ${METHYLATED_BASES_TABLE_6mA}
wait
echo "Done filtering methylated bases by type."


# Observe the filtered output table
echo "Filtered Modkit methylated bases table (5mC):"
head ${METHYLATED_BASES_TABLE_5mC}
echo "Filtered Modkit methylated bases table (6mA):"
head ${METHYLATED_BASES_TABLE_6mA}


## Keep only specific columns: read id, forward_read_position of methylated base, k-mer sequence region   
# 5mC
echo "Keeping only necessary columns for 5mC methylated bases."
srun cut -f 1,2,15 ${METHYLATED_BASES_TABLE_5mC} \
| sort -t$'\t' -k1 \
| awk 'BEGIN {FS="\t"; OFS="\t"} {print $1, $2, $3}' \
> ${METHYLATED_REGIONS_TABLE_5mC}
wait
# 6mA
echo "Keeping only necessary columns for 6mA methylated bases."
srun cut -f 1,2,15 ${METHYLATED_BASES_TABLE_6mA} \
| sort -t$'\t' -k1 \
| awk 'BEGIN {FS="\t"; OFS="\t"} {print $1, $2, $3}' \
> ${METHYLATED_REGIONS_TABLE_6mA}
wait
echo "Done creating final methylated regions tables."


## Observe final .tsv output
echo "Final methylated regions table (6mA):"
head ${METHYLATED_REGIONS_TABLE_6mA}
echo "Final methylated regions table (5mC):"
head ${METHYLATED_REGIONS_TABLE_5mC}


## Create .fasta formatted files of the methylated regions
# Read ids are combined with the methylated position: readid_methposition
# 5mC
echo "Creating a fasta formatted file of 5mC methylated regions."
awk 'BEGIN {FS="\t"} {print ">"$1"_"$2"\n"$3}' ${METHYLATED_REGIONS_TABLE_5mC} > ${METHYLATED_REGIONS_FASTA_5mC}
echo "Fasta formatted file of 5mC methylated regions created: ${METHYLATED_REGIONS_FASTA_5mC}."
# 6mA
echo "Creating a fasta formatted file of 6mA methylated regions."
awk 'BEGIN {FS="\t"} {print ">"$1"_"$2"\n"$3}' ${METHYLATED_REGIONS_TABLE_6mA} > ${METHYLATED_REGIONS_FASTA_6mA}
echo "Fasta formatted file of 6mA methylated regions created: ${METHYLATED_REGIONS_FASTA_6mA}."


## Remove no longer needed intermediate files
rm -r ${TMP_DIR}
echo "Removed temporary files."
echo "Finished methylation region extraction of run ${run_name}."


echo "DONE."
