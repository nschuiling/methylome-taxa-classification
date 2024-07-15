#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=00:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=500GB

# Save errors and logs
#SBATCH --output=./slurmlog/F4b-slurm-%j.out     
#SBATCH --error=./slurmlog/F4b-slurm-%j.err

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_JOB_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartF_ExplorationPreprocessing"

# Load necessary modules and virtual environments
module use /opt/insy/modulefiles
module use /opt/insy/modules/DBL/modulefiles
module load cuda/12.0
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate dataexploration


######################################################
##### DEFINE INPUT AND OUTPUT FILES AND SETTINGS #####

## Type of cluster data to plot
scaling="noscaling"  # "noscaling" or "robust_scaled" or 
cluster_type="umap"   # "pca" or "umap"

## Input: the clustering data
# Folder
CLUSTERS_DIR="./files/F4_Clustering"
# File 
CLUSTER_FILE="${CLUSTERS_DIR}/Top50_${scaling}_${cluster_type}.csv"

## Input: labels of the data, sorted in order of the taxonomic trees
TREE_ORDER="./files/F2_TaxonomyDictsTrees/tree_orders_dict.pkl"

## Output: folder to save figures to
PLOTS_DIR="./files/F4b_ClusteringPlots"
mkdir -p ${PLOTS_DIR}


###########################################
##### CREATE (MODIFIED) CLUSTER PLOTS #####

echo "Creating clustering plots for pre-clustered data ${CLUSTER_FILE}."
python F4b_ClusterPlots.py ${cluster_type} ${scaling} ${PLOTS_DIR} ${CLUSTER_FILE} ${TREE_ORDER}

wait
echo "Results in ${PLOTS_DIR}."
echo "DONE."
