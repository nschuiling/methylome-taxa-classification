#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=6
#SBATCH --mem=60GB

# Save errors and logs
#SBATCH --output=./slurmlog/H0-slurm-%j.out 
#SBATCH --error=./slurmlog/H0-slurm-%j.err    

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_JOB_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####


# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartH_ModelApplication"

module use /opt/insy/modulefiles
module use /opt/insy/modules/DBL/modulefiles
module load cuda/12.0
module load devtoolset/8
module load intel/oneapi

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate seqkit


######################################################
##### DEFINE INPUT AND OUTPUT FILES AND SETTINGS #####

# THIS WAS AN ATTEMPT TO USE THE HOLD-OUT READS FOR APPLICATION ANALYSIS
# THE MODEL HAD ALREADY BEEN TRAINED ON THE REST OF THE DATA, SO IT WAS ESSENTIAL TO USE THE EXACT TEST SET THAT WAS PREVIOUSLY CREATED
# HOWEVER: IT DID NOT WORK OUT TO MATCH BACK THE TEST SET READS TO THE CORRECT READS/IDS

# Define directory for output
OUT_DIR="./files/H0_HoldoutReads"
mkdir -p ${OUT_DIR}

# Read ids of the test set
TEST_TSV="../PartG_ClassificationModel/files/G1_TrainTestData/Top50NormalizedProfile_test_profile.tsv"
TEST_READ_IDs="${OUT_DIR}/holdout_test_read_ids.txt"

# Get the read ids from the first column
# `tail -n +2` is used to skip the header row
cut -d $'\t' -f 1 ${TEST_TSV} | tail -n +2 > ${TEST_READ_IDs}

# Fasta files of the samples
FASTA_DIR="../PartA_DataCollection/files/A5_QCFilteredBasecalls"
EL2W_ERR11004357="${FASTA_DIR}/CHEESE_PRJEB58160/EL2W_ERR11004357/EL2W_ERR11004357_analysis.fasta"
OM2_ERR11168802="${FASTA_DIR}/CHEESE_PRJEB58160/OM2_ERR11168802/OM2_ERR11168802_analysis.fasta"
WH1M_ERR11007628="${FASTA_DIR}/CHEESE_PRJEB58160/WH1M_ERR11007628/WH1M_ERR11007628_analysis.fasta"
ZYMO_ERR13034758="${FASTA_DIR}/NANOMOTIF_PRJEB74343/ZYMO_ERR13034758/ZYMO_ERR13034758_analysis.fasta"
HUMGUT_ERR13033930="${FASTA_DIR}/NANOMOTIF_PRJEB74343/HUMGUT_ERR13033930/HUMGUT_ERR13033930_analysis.fasta"
FULL_FASTA="${OUT_DIR}/samples1-5_all_reads.fasta"

# Combine the fasta files into one big file
srun cat ${EL2W_ERR11004357} ${OM2_ERR11168802} ${WH1M_ERR11007628} ${ZYMO_ERR13034758} ${HUMGUT_ERR13033930} > ${FULL_FASTA}

# Fasta file with test set sequences
TEST_FASTA="${OUT_DIR}/holdout_test_reads.fasta"

srun seqkit grep -f ${TEST_READ_IDs} ${FULL_FASTA} -o ${TEST_FASTA}

rm ${FULL_FASTA}

echo "DONE."

