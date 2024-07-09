#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=medium
#SBATCH --time=24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem-per-cpu=8GB

# Save errors and logs
#SBATCH --output=./slurmlog/B2-slurm-%j.out
#SBATCH --error=./slurmlog/B2-slurm-%j.err

# Use this simple command to check that your sbatch settings are working
/usr/bin/scontrol show job -d "$SLURM_JOB_ID"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartB_ReferenceCollection"

## Input: nt_prok data located in the databases directory
# Folder
DATABASE_DIRECTORY="./databases"
# File
NCBI_NTPROK_FA="${DATABASE_DIRECTORY}/nt_prok.fsa"

## Output: indexed database
# File
NCBI_NTPROK_MMI="${DATABASE_DIRECTORY}/nt_prok.mmi"


####################################################
##### INDEX THE NCBI REFERENCE DATASET nt_prok #####

## Index the nt_prok reference database
echo "Starting Minimap2 indexing of nt_prok fasta: ${NCBI_NTPROK_FA}."
srun "./software/minimap2/minimap2" -x map-ont -t 30 -d ${NCBI_NTPROK_MMI} ${NCBI_NTPROK_FA}
wait
echo "Minimap2 nt_prok database indexing completed. Result: ${NCBI_NTPROK_MMI}."

echo "DONE."
