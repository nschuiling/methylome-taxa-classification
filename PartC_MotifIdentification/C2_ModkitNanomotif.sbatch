#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=medium
#SBATCH --time=12:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=12
#SBATCH --mem=100GB

# This script is run for each dataset separately
# The datasets are specified in the configuration file and retrieved via a slurm job array
# Replace X by the indexes of the dataset to analyse (from .config file)
#SBATCH --array=X                                    

# Save errors and logs
#SBATCH --output=./slurmlog/C2-slurm-%A_%a.out
#SBATCH --error=./slurmlog/C2-slurm-%A_%a.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartC_MotifIdentification"

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

## Input: MetaFlye assembly and Contig-Read map
# Input folder
ASSEMBLY_DIR="./files/C1_MetaflyeAssembly/${project_name}/${run_name}"
# Input file paths
ASSEMBLY_FASTA="${ASSEMBLY_DIR}/assembly.fasta"  # automatic naming
CONTIG_READ_BAM="${ASSEMBLY_DIR}/${run_name}_contigreadmap.bam"

## Nanomotif output
# Output folder
MOTIF_DIR="./files/C2_ModkitNanomotifs/${project_name}/${run_name}"
mkdir -p ${MOTIF_DIR}
# Output file paths
PILEUP_BED="${MOTIF_DIR}/${run_name}_modkitpileup.bed"
NANOMOTIF_DIR="${MOTIF_DIR}/${run_name}_nanomotif"
NANOMOTIF_TSV="${NANOMOTIF_DIR}/motifs.tsv" # automatic naming

## Reformatted Nanomotif motifs, collected into one folder with all samples
ALL_NANOMOTIFS_5mC="./files/C2_ModkitNanomotifs/AllNanomotifs_5mC"
ALL_NANOMOTIFS_6mA="./files/C2_ModkitNanomotifs/AllNanomotifs_6mA"
mkdir -p ${ALL_NANOMOTIFS_5mC}
mkdir -p ${ALL_NANOMOTIFS_6mA}
NANOMOTIF_5mC_TSV="${ALL_NANOMOTIFS_5mC}/${project_name}_${run_name}_nanomotifs_5mC.tsv"
NANOMOTIF_6mA_TSV="${ALL_NANOMOTIFS_6mA}/${project_name}_${run_name}_nanomotifs_6mA.tsv"


##################################################
##### METHYLATION ANALYSIS AND MOTIF FINDING #####

## Perform methylation pile up using Modkit
# Ignore "h" (5hmC) modification calls, since not all basecalling models were able to call this
# Use a filter threshold of 0.7 (recommended by Nanomotif)
echo "Starting methylation pileup. Using Modkit on file ${CONTIG_READ_BAM}."
srun "./software/modkit_v0.2.6_centos7_x86_64/modkit" pileup --max-depth 1000000000 -t 10 \
  --filter-threshold 0.7 --ignore "h" --only-tabs ${CONTIG_READ_BAM} ${PILEUP_BED}
wait
echo "Finished methylation pileup, results in: ${PILEUP_BED}."


## Perform motif discovery using Nanomotif
# Thresholds are set a bit less strict than the default --> motifs for later analysis
# Search frame size was set based on the largest REBASE motif having length 22
echo "Starting motif finding with Nanomotif, using: ${ASSEMBLY_FASTA} and ${PILEUP_BED}."
conda activate nanomotif
srun nanomotif find-motifs --out ${NANOMOTIF_DIR} \
  --threshold_methylation_general 0.5 \
  --threshold_methylation_confident 0.5 \
  --threshold_valid_coverage 3 \
  --minimum_kl_divergence 0.05 \
  --search_frame_size 44 \
  -v -t 10 \
  ${ASSEMBLY_FASTA} ${PILEUP_BED}
wait
echo "Completed motif finding with Nanomotif, results in: ${NANOMOTIF_DIR}."


## Separate motifs by type and save into tsv files
echo "Starting the extraction of Nanomotif-identified motifs to a tsv file."
# Set the column names in both files
echo -e "motif\tmeth_position" > ${NANOMOTIF_5mC_TSV}
echo -e "motif\tmeth_position" > ${NANOMOTIF_6mA_TSV}
# Fill the methylation motif .tsv files with the motifs that are long enough (>4 bases)
awk 'NR>1 && length($2)>=4 {print $2, $3, $4}' ${NANOMOTIF_TSV} | while read -r motif methpos methtype; do
    if [ "$methtype" = "m" ]; then
        echo -e "$motif\t$methpos" >> ${NANOMOTIF_5mC_TSV}
    elif [ "$methtype" = "a" ]; then
        echo -e "$motif\t$methpos" >> ${NANOMOTIF_6mA_TSV}
    fi
done
echo "Nanomotif motifs extracted from TSV file and saved to separate tsv files based on their type: ${NANOMOTIF_5mC_TSV} and ${NANOMOTIF_6mA_TSV}."


## Sort the motifs and keep only the unique ones
# Preserve the header
echo "Starting filtering and sorting of unique motifs."
{
    head -n 1 ${NANOMOTIF_5mC_TSV}
    tail -n +2 ${NANOMOTIF_5mC_TSV} | sort -u
} > ${NANOMOTIF_5mC_TSV}_sorted
echo "5mC motifs filtered and sorted in: ${NANOMOTIF_5mC_TSV}_sorted."

{
    head -n 1 ${NANOMOTIF_6mA_TSV}
    tail -n +2 ${NANOMOTIF_6mA_TSV} | sort -u
} > ${NANOMOTIF_6mA_TSV}_sorted
echo "6mA motifs filtered and sorted in: ${NANOMOTIF_6mA_TSV}_sorted."


## Replace the original files with the sorted ones
mv ${NANOMOTIF_5mC_TSV}_sorted ${NANOMOTIF_5mC_TSV}
mv ${NANOMOTIF_6mA_TSV}_sorted ${NANOMOTIF_6mA_TSV}
echo "Final results saved in ${NANOMOTIF_5mC_TSV} and ${NANOMOTIF_6mA_TSV}."

echo "Completed Nanomotif motif identification."
echo "DONE."
