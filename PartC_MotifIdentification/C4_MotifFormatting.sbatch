#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=00:15:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16GB

# Save errors and logs
#SBATCH --output=./slurmlog/C4-slurm-%j.out
#SBATCH --error=./slurmlog/C4-slurm-%j.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_JOB_ID}"

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
conda activate motifcollection


##############################################
##### DEFINE INPUT AND OUTPUT FILE PATHS #####

## Input: .tsv files with 5mC and 6mA motifs
# Files
tsv_motifs_5mC="./files/C3_CollectedMotifs/AllMotifs_REBASE_and_Nanomotifs_5mC.tsv"
tsv_motifs_6mA="./files/C3_CollectedMotifs/AllMotifs_REBASE_and_Nanomotifs_6mA.tsv"

## Output: motifs formatted as integers
# Folder
MOTIFSEARCH_DIR="./files/C4_MotifIntegers"
mkdir -p ${MOTIFSEARCH_DIR}
# Figures
png_motiflengths_sidebyside="${MOTIFSEARCH_DIR}/MotifLengths_sidebyside.png"
png_motiflengths_vertical="${MOTIFSEARCH_DIR}/MotifLengths_vertical.png"
# Files
dict_motif_integers="${MOTIFSEARCH_DIR}/SearchMotifIntegers_5mC_6mA.dict"
set_motif_integers="${MOTIFSEARCH_DIR}/SearchMotifIntegers_5mC_6mA.set"


################################################
##### PREPARING MOTIFS FOR SEARCH IN READS #####

echo "Starting motif-to-integer mapping for efficient motif searching."
python C4_MotifIntegers.py ${tsv_motifs_5mC} ${tsv_motifs_6mA} ${png_motiflengths_sidebyside} ${png_motiflengths_vertical} ${dict_motif_integers} ${set_motif_integers}
wait
echo "Finished motif-to-integer mapping. Results in ${dict_motif_integers} and ${set_motif_integers}."

echo "DONE."
