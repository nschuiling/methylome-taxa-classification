#!/usr/bin/env python3

# %% [markdown]
# # Find methylated motifs through kmer-integer searching

# %% [markdown]
# ### Prepare environment, input, and output files

# %%
# Load libraries
import sys
from itertools import product
import Bio.Data.IUPACData as bdi
import ast

# %%
## Input files
# Methylated regions in which motifs will be searched
tsv_methylated_regions = sys.argv[1]
# Set of motifs to be searched
set_motif_integers = sys.argv[2]
## Output file
# Motifs (integer-represented) found in each read
tsv_methylated_integers = sys.argv[3]

# %% [markdown]
# ### Load the integer representations of the motifs to be searched

# %%
# Load the set of integers representing the motifs of interest
with open(set_motif_integers, 'r') as input:
    motif_set = ast.literal_eval(input.read())

# %%
motif_set

# %% [markdown]
# ### DNA-to-integer settings and function

# %%
# Define the DNA to integer mapping
dna = {"A": 0, "C": 1, "T": 2, "G": 3, "-": 4, "a": 5, "c": 6}
middle_index = 21  # 0-based index for the middle base in a 44 bp sequence
kmax = 12 # (adjusted) length of the k-mers

# %%
# Function to expand consensus sequences into their unambiguous versions
def extend_ambiguous_dna(ambiguous_motif):
    """Return a list of all possible sequences given an ambiguous DNA motif."""
    d = bdi.ambiguous_dna_values
    return list(map("".join, product(*map(d.get, ambiguous_motif))))

# %%
# Function to create a motif string representation with lower case methylated base
def lower_case_methylation(motif, position):
    """Return the motif with the methylated base as lower case letter."""
    if motif[position] == 'C' or motif[position] == 'A':
        return motif[:position] + motif[position].lower() + motif[position+1:]
    else:
        return motif

# %% [markdown]
# ### Calculate integer-representations of methylated motifs in each read

# %%
# Function to create a k-mer integer value
def create_kmer_integer(kmer):
    """Function to assign a unique integer to each unique kmer.
    Values are calculated based on kmax (e.g. 12) length kmers.
    If kmers are shorter they will get end gaps."""
    kmer_integer = 0
    exp = kmax - 1
    for letter in kmer:
        kmer_integer += (dna[letter] * 7**exp)
        exp -= 1
    # Pad the rest of the positions with the gap character ('-')
    while exp >= 0:
        kmer_integer += (dna['-'] * 7**exp)
        exp -= 1
    return kmer_integer

# %%
# Function to extract all k-mers overlapping the middle base and compute their integer values
def extract_all_kmer_integers(sequence):
    kmer_integers = set()
    # Iterate over all possible kmers
    for k in range(4, kmax+1):
        start_range = max(0, middle_index - k + 1)
        end_range = min(len(sequence), middle_index + 1)
        # For each k-mer, extract the integer
        for start_pos in range(start_range, end_range):
            end_pos = start_pos + k
            kmer = sequence[start_pos:end_pos]
            kmer_integer = create_kmer_integer(kmer)
            kmer_integers.add(kmer_integer)
    kmer_motif_integers = kmer_integers.intersection(motif_set)
    return kmer_motif_integers

# %%
def find_motifs_in_reads(input_file, output_file):
    """Function to create a kmer profile for each read in the input file.
    It iterates over all rows (methylated regions) in a .tsv file, and returns a vector for each read."""

    # Open both the input and the output file
    with open(output_file, 'w') as output:
        with open(input_file, 'r') as input:
            
            # Write the header of the output file
            #kmer_integers = ["kmer_"+str(i + 1) for i in range(247)]
            #vector_header = "read_id" + "\t" + "\t".join(kmer_integers)
            #output.write(vector_header + "\n")

            read_id = ""
            read_integers = []
            read_regions = 0

            # Iterate over the lines in the input file
            for line in input:
                new_read_id, _, methylated_region = line.rstrip().split('\t')
                
                # Change the middle base to lowercase
                methylated_region = lower_case_methylation(methylated_region, middle_index)
                kmer_motif_integers = extract_all_kmer_integers(methylated_region)
                kmer_motif_integers = list(kmer_motif_integers)

                # The methylated regions per read are split over multiple lines
                # Check if the read ID has changed
                if new_read_id == read_id:
                    read_integers.extend(kmer_motif_integers)
                    read_regions += 1
                else:
                    # If the read ID changed, write the previous read ID and vector to the output file
                    if read_id:
                        output.write(read_id + "\t" + str(read_regions) + "\t" + str(read_integers) + "\n")
                    # Reset the read ID to the new read
                    # Initialize the vector for the new read, using the current methylated region
                    read_id = new_read_id
                    read_integers = kmer_motif_integers
                    read_regions = 1

            # Write the last read to the output file
            if read_id:
                output.write(read_id + "\t" + str(read_regions) + "\t" + str(read_integers) + "\n")



# %%
find_motifs_in_reads(tsv_methylated_regions, tsv_methylated_integers)

# 7 minutes for 80mb 5mC methylation file
