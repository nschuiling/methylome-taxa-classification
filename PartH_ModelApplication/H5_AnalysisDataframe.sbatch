#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=00:05:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=40GB

# Save errors and logs
#SBATCH --output=./slurmlog/H5-slurm-%j.out 
#SBATCH --error=./slurmlog/H5-slurm-%j.err    

# Check that the sbatch settings are working
/usr/bin/scontrol show job -d "${SLURM_JOB_ID}"

# Exit immediately if a command fails
set -e


################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####


# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartH_ModelApplication"

# Load necessary modules and virtual environments
source /opt/insy/miniconda/3.11/etc/profile.d/conda.sh
conda activate methylationprofiling


######################################################
##### DEFINE INPUT AND OUTPUT FILES AND SETTINGS #####

OUTPUT_DIR="./files/H5_AnalysisDataframes"
mkdir -p ${OUTPUT_DIR}


### SELECT BY COMMENTING / CHANGING THE DATASET ORDER
### Data has been pre-processed similarly, but in different files because of the training/validation/application stages


# APPLICATION DATA (samples 9-15, combined) --> all species with prok annotation, ARGs with 80% identity 60% setting
tsv_application_profiles="./files/H4_CombinedApplicationProfiles/ApplicationSamples9-15_profiles_combined_normalized.tsv"
tsv_mge_probabilities="none"
tsv_arg_hits="none"
pickle_taxon_dictionaries="../PartF_ExplorationPreprocessing/files/F2_TaxonomyDicts/Samples1-5_dictionaries.tsv"
tsv_plasmids_or_args="${OUTPUT_DIR}/test_application_predictions_args_mges.tsv"
npy_predictions_folder="./files/H4b_ApplicationPredictions"
npy_predictions_suffix=".npy"


# VALIDATION DATA (sample 8) --> top50 species, args with 90% identity 75% setting
tsv_application_profiles="../PartE_ProfileAnnotation/files/E6_ValidationApplicationProfiles/DBL_SAMPLES/ZYMOMOCK_DBL/ZYMOMOCK_DBL_normalized_top50.tsv"
tsv_mge_probabilities="./files/H2_ReadAnnotationsMGEs/ZYMOMOCK_DBL/ZYMOMOCK_DBL_plasmid_scores.tsv"
tsv_arg_hits="./files/H1_ReadAnnotationsARG/ZYMOMOCK_DBL/ZYMOMOCK_DBL_blast_arg_90_75_hits.txt"
pickle_taxon_dictionaries="../PartF_ExplorationPreprocessing/files/F2_TaxonomyDicts/Samples1-5_dictionaries.tsv"
tsv_plasmids_or_args="${OUTPUT_DIR}/test_independent_predictions_args_mges.tsv"
npy_predictions_folder="../PartG_ClassificationModel/files/G6_TestSetsPerformance"
npy_predictions_suffix="_independent.npy"

# HOLDOUT TEST DATA (5% subset from samples 1-5) -> top50 species, args with 90% identity 75% setting
tsv_application_profiles="../PartG_ClassificationModel/files/G1_TrainTestData/Top50NormalizedProfile_test_profile.tsv"
tsv_mge_probabilities="./files/H2_ReadAnnotationsMGEs/HOLDOUT_TEST/HOLDOUT_TEST_plasmid_scores.tsv"
tsv_arg_hits="./files/H1_ReadAnnotationsARG/HOLDOUT_TEST/HOLDOUT_TEST_blast_arg_90_75_hits.txt"
pickle_taxon_dictionaries="../PartF_ExplorationPreprocessing/files/F2_TaxonomyDicts/Samples1-5_dictionaries.tsv"
tsv_plasmids_or_args="${OUTPUT_DIR}/test_holdout_predictions_args_mges.tsv"
npy_predictions_folder="../PartG_ClassificationModel/files/G6_TestSetsPerformance"
npy_predictions_suffix="_holdout.npy"


########################
##### RUN ANALYSIS #####

python H5_AnalysisDataframe.py ${tsv_application_profiles} ${tsv_mge_probabilities} ${tsv_arg_hits} ${pickle_taxon_dictionaries} ${tsv_plasmids_or_args} ${npy_predictions_folder} ${npy_predictions_suffix}

echo "DONE."



