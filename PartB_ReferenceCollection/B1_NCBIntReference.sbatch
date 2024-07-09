#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=long
#SBATCH --time=48:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem-per-cpu=8GB

# Save errors and logs
#SBATCH --output=./slurmlog/B1-slurm-%j.out
#SBATCH --error=./slurmlog/B1-slurm-%j.err

# Use this simple command to check that your sbatch settings are working
/usr/bin/scontrol show job -d "$SLURM_JOB_ID"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartB_ReferenceCollection"

# Load necessary modules and virtual environments
module use /opt/insy/modulefiles
module use /opt/insy/modules/DBL/modulefiles


###################################################
##### DOWNLOAD NCBI REFERENCE DATASET nt_prok #####

## Download command instructions:
# https://www.ncbi.nlm.nih.gov/sites/books/NBK569856/

# The databases should be downloaded into the databases directory
DATABASE_DIRECTORY="./databases/"
cd ${DATABASE_DIRECTORY}

# Download the dataset (DONE ON 29 March)
srun update_blastdb.pl --decompress nt_prok
wait

# Create a .fasta version of the dataset
NCBI_NTPROK_FA="../nt_prok.fsa"
srun blastdbcmd -db nt_prok -entry all -out ${NCBI_NTPROK_FA} 

echo "DONE."