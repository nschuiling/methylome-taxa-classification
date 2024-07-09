#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=1GB

# Save errors and logs
#SBATCH --output=./slurmlog/B3-slurm-%j.out
#SBATCH --error=./slurmlog/B3-slurm-%j.err

# Use this simple command to check that your sbatch settings are working
/usr/bin/scontrol show job -d "$SLURM_JOB_ID"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartB_ReferenceCollection"

## Input: download link
MEGAN_LINK="https://software-ab.cs.uni-tuebingen.de/download/megan6/megan-nucl-Feb2022.db.zip"

## Output: database saved to directory
# Folder
DATABASE_DIRECTORY="./databases"
mkdir -p ${DATABASE_DIRECTORY}
# File
MEGAN_FILE=$(basename "$MEGAN_LINK")


############################################
##### DOWNLOAD MEGAN REFERENCE DATASET #####

## Background information/references
# DIAMOND-MEGAN protocol: https://link.springer.com/protocol/10.1007/978-1-0716-3072-3_6
# Megan download info: https://software-ab.cs.uni-tuebingen.de/download/megan6/welcome.html

## Download and unzip Megan mapping database
wget ${MEGAN_LINK} -P ${DATABASE_DIRECTORY}
unzip -q "${DATABASE_DIRECTORY}/${MEGAN_FILE}" -d ${DATABASE_DIRECTORY}

echo "DONE."

## Errors occured during the running of this script (slurmlog "./slurmlog/slurm_9853091.err")
# Therefore manually downloaded the megan map (done on 25 March 2024)

## For the analysis later on, the MEGAN6 "meganizer program" must also be installed
# Downloaded on 26 March from https://unitc-my.sharepoint.com/:f:/g/personal/iijhu01_cloud_uni-tuebingen_de/EvXxoL8mF9NAi5I_brpxg4MBUC-WdcOxMB2ufGzNIRB0OQ?e=Z6h7da