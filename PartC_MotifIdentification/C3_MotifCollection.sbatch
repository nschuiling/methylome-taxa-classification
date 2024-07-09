#!/bin/sh

####################################################
##### REQUEST SBATCH RESOURCES (TASK-SPECIFIC) #####

#SBATCH --partition=general
#SBATCH --qos=short
#SBATCH --time=00:15:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4GB

# Save errors and logs
#SBATCH --output=./slurmlog/C3-slurm-%j.out
#SBATCH --error=./slurmlog/C3-slurm-%j.err

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

## Input: Methylation motifs
# REBASE database motifs
REBASE_5C_MOTIFS="../PartB_ReferenceCollection/databases/rebase_5C_motifs.tsv"
REBASE_6A_MOTIFS="../PartB_ReferenceCollection/databases/rebase_6A_motifs.tsv"
# Nanomotif-identified methylation motifs (all samples combined)
ALL_NANOMOTIFS_5mC_DIR="./files/C2_ModkitNanomotifs/AllNanomotifs_5mC"
ALL_NANOMOTIFS_6mA_DIR="./files/C2_ModkitNanomotifs/AllNanomotifs_6mA"


## Output: all Nanomotifs from different samples, combined with REBASE motifs
# Folder
COLLECTED_MOTIFS_DIR="./files/C3_CollectedMotifs"
mkdir -p ${COLLECTED_MOTIFS_DIR}
# Files for the Nanomotifs identified in all samples combined
ONLY_NANOMOTIFS_5mC_TSV="${COLLECTED_MOTIFS_DIR}/OnlyNanomotifs_5mC.tsv"
ONLY_NANOMOTIFS_6mA_TSV="${COLLECTED_MOTIFS_DIR}/OnlyNanomotifs_6mA.tsv"
# Files for Nanomotifs NOT present in REBASE
NONREBASE_NANOMOTIFS_5mC_TSV="${COLLECTED_MOTIFS_DIR}/NonREBASE_Nanomotifs_5mC.tsv"
NONREBASE_NANOMOTIFS_6mA_TSV="${COLLECTED_MOTIFS_DIR}/NonREBASE_Nanomotifs_6mA.tsv"
# Files for Nanomotifs that ARE present in REBASE
OVERLAP_REBASE_NANOMOTIFS_5mC_TSV="${COLLECTED_MOTIFS_DIR}/OverlapREBASE_Nanomotifs_5mC.tsv"
OVERLAP_REBASE_NANOMOTIFS_6mA_TSV="${COLLECTED_MOTIFS_DIR}/OverlapREBASE_Nanomotifs_6mA.tsv"
# Files for the all REBASE and Nanomotif motifs combined
REBASE_AND_NANOMOTIFS_5mC_TSV="${COLLECTED_MOTIFS_DIR}/AllMotifs_REBASE_and_Nanomotifs_5mC.tsv"
REBASE_AND_NANOMOTIFS_6mA_TSV="${COLLECTED_MOTIFS_DIR}/AllMotifs_REBASE_and_Nanomotifs_6mA.tsv"
REBASE_AND_NANOMOTIFS_5mC_FASTA="${COLLECTED_MOTIFS_DIR}/AllMotifs_REBASE_and_Nanomotifs_5mC.fasta"
REBASE_AND_NANOMOTIFS_6mA_FASTA="${COLLECTED_MOTIFS_DIR}/AllMotifs_REBASE_and_Nanomotifs_6mA.fasta"

## Output: Venn diagrams of REBASE-Nanomotif overlap
VENN_DIAGRAM_5mC="${COLLECTED_MOTIFS_DIR}/5mC_Motifs_Venn.png"
VENN_DIAGRAM_6mA="${COLLECTED_MOTIFS_DIR}/6mA_Motifs_Venn.png"
VENN_DIAGRAM_5mC_filtered="${COLLECTED_MOTIFS_DIR}/5mC_Motifs_Venn_filtered.png"
VENN_DIAGRAM_6mA_filtered="${COLLECTED_MOTIFS_DIR}/6mA_Motifs_Venn_filtered.png"


######################################################
##### COMBINING MOTIFS FROM NANOMOTIF AND REBASE #####

## Create one .tsv file combining all Nanomotifs identified in different samples
# Motifs have already been sorted and filtered for minimum length 4

# 5mC
# Combine 5mC TSV files, remove headers, sort, and keep unique motifs
cat ${ALL_NANOMOTIFS_5mC_DIR}/*.tsv | sort | uniq > ${ONLY_NANOMOTIFS_5mC_TSV}.tmp
grep -v -e 'motif' ${ONLY_NANOMOTIFS_5mC_TSV}.tmp > ${ONLY_NANOMOTIFS_5mC_TSV}.tmp2
# Add the header to the sorted unique motifs
{
    echo -e "motif\tmeth_position"
    cat ${ONLY_NANOMOTIFS_5mC_TSV}.tmp2
} > ${ONLY_NANOMOTIFS_5mC_TSV}
# Remove the temporary files
rm ${ONLY_NANOMOTIFS_5mC_TSV}.tmp ${ONLY_NANOMOTIFS_5mC_TSV}.tmp2

# 6mA
# Combine 6mA TSV files, remove headers, sort, and keep unique
cat ${ALL_NANOMOTIFS_6mA_DIR}/*.tsv | sort | uniq > ${ONLY_NANOMOTIFS_6mA_TSV}.tmp
grep -v -e 'motif' ${ONLY_NANOMOTIFS_6mA_TSV}.tmp > ${ONLY_NANOMOTIFS_6mA_TSV}.tmp2
# Add the header to the sorted unique motifs
{
    echo -e "motif\tmeth_position"
    cat ${ONLY_NANOMOTIFS_6mA_TSV}.tmp2
} > ${ONLY_NANOMOTIFS_6mA_TSV}
# Remove the temporary files
rm ${ONLY_NANOMOTIFS_6mA_TSV}.tmp ${ONLY_NANOMOTIFS_6mA_TSV}.tmp2


## Use a python script to compare the REBASE and Nanomotifs
# Create venn diagrams of the overlap
# Create .tsv files with the (non-)overlapping motifs

# 5mC
echo "Starting motif comparison for 5mC motifs, using the files ${ONLY_NANOMOTIFS_5mC_TSV} and ${REBASE_5C_MOTIFS}."
python C3_MotifCollection.py "5mC" ${ONLY_NANOMOTIFS_5mC_TSV} ${REBASE_5C_MOTIFS} ${NONREBASE_NANOMOTIFS_5mC_TSV} ${OVERLAP_REBASE_NANOMOTIFS_5mC_TSV} ${REBASE_AND_NANOMOTIFS_5mC_TSV} ${VENN_DIAGRAM_5mC} ${VENN_DIAGRAM_5mC_filtered}
wait
echo "Finished motif comparison for 5mC motifs. Overlapping motifs in: ${OVERLAP_REBASE_NANOMOTIFS_5mC_TSV}. Unique Nanomotifs in: ${NONREBASE_NANOMOTIFS_5mC_TSV}. REBASE motifs plus newly identied Nanomotifs in: ${REBASE_AND_NANOMOTIFS_5mC_TSV}."

# 6mA
echo "Starting motif comparison for 6mA motifs, using the files ${ONLY_NANOMOTIFS_6mA_TSV} and ${REBASE_6A_MOTIFS}."
python C3_MotifCollection.py "6mA" ${ONLY_NANOMOTIFS_6mA_TSV} ${REBASE_6A_MOTIFS} ${NONREBASE_NANOMOTIFS_6mA_TSV} ${OVERLAP_REBASE_NANOMOTIFS_6mA_TSV} ${REBASE_AND_NANOMOTIFS_6mA_TSV} ${VENN_DIAGRAM_6mA} ${VENN_DIAGRAM_6mA_filtered}
wait
echo "Finished motif comparison for 6mA motifs. Overlapping motifs in: ${OVERLAP_REBASE_NANOMOTIFS_6mA_TSV}. Unique Nanomotifs in: ${NONREBASE_NANOMOTIFS_6mA_TSV}. REBASE motifs plus newly identied Nanomotifs in: ${REBASE_AND_NANOMOTIFS_6mA_TSV}."


## Quick checks on the motif files
# How many motifs are there?
echo "Number of 5C motifs (REBASE and Nanomotifs): $(wc -l < ${REBASE_AND_NANOMOTIFS_5mC_TSV})"
echo "Number of 6A motifs (REBASE and Nanomotifs): $(wc -l < ${REBASE_AND_NANOMOTIFS_6mA_TSV})"
# What are the minimum and maximum motif lengths?
awk -F'\t' '{print length($1)}' ${REBASE_AND_NANOMOTIFS_5mC_TSV} | sort -n | \
awk 'NR==1 {print "Shortest 5C motif length:", $1} END {print "Longest 5C motif length:", $1}'
awk -F'\t' '{print length($1)}' ${REBASE_AND_NANOMOTIFS_6mA_TSV} | sort -n | \
awk 'NR==1 {print "Shortest 6A motif length:", $1} END {print "Longest 6A motif length:", $1}'

echo "DONE."
