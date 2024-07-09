#!/bin/sh

# Bash script instead of Sbatch script (less resources needed)

################################################################
##### SET-UP ENVIRONMENT AND INPUT (USER/PROJECT-SPECIFIC) #####

# Set working directory
cd "/tudelft.net/staff-umbrella/abeellabstudents/mnmschuiling/PartB_ReferenceCollection"


##############################################
##### DEFINE INPUT AND OUTPUT FILE PATHS #####

## Input: download link
REBASE_URL="http://rebase.neb.com/rebase/rebase_methylase_recseqs.txt"

## Output: REBASE motifs
# Folder
REBASE_DIR="./databases"
mkdir -p ${REBASE_DIR}
# Files
REBASE_FILE="${REBASE_DIR}/$(basename ${REBASE_URL})"
REBASE_5C_MOTIFS="${REBASE_DIR}/rebase_5C_motifs.tsv"
REBASE_6A_MOTIFS="${REBASE_DIR}/rebase_6A_motifs.tsv"


##############################################
##### CREATE REBASE MOTIF REFERENCE FILE #####

## Download the REBASE methylation recognition sequences
# DONE on 17 May 2024: obtaining the database version of 04/29/2024
echo "Downloading REBASE motifs from: ${REBASE_URL}."
wget ${REBASE_URL} -P ${REBASE_DIR} --user-agent="Mozilla"
echo "REBASE motifs downloaded to: ${REBASE_FILE}."

## Extract the motifs relevant for further analysis:
# Those concerning 5mC or 6mA methylation, with minimum lenth 4bp
# Keep the modified position for later analyses
python B4_ReformatRebase.py ${REBASE_FILE} ${REBASE_5C_MOTIFS} ${REBASE_6A_MOTIFS}

## Quick checks on the motif files
# How many motifs are there?
echo "Number of 5C motifs: $(wc -l < ${REBASE_5C_MOTIFS})"
echo "Number of 6A motifs: $(wc -l < ${REBASE_6A_MOTIFS})"
# What are the minimum and maximum motif lengths?
awk -F'\t' '{print length($1)}' ${REBASE_5C_MOTIFS} | sort -n | \
awk 'NR==1 {print "Shortest 5C motif length:", $1} END {print "Longest 5C motif length:", $1}'
awk -F'\t' '{print length($1)}' ${REBASE_6A_MOTIFS} | sort -n | \
awk 'NR==1 {print "Shortest 6A motif length:", $1} END {print "Longest 6A motif length:", $1}'

echo "DONE."

## Findings:
#Number of 5C motifs: 112
#Number of 6A motifs: 6409
#Shortest 5C motif length: 4
#Longest 5C motif length: 8
#Shortest 6A motif length: 4
#Longest 6A motif length: 22
