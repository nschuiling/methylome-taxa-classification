#!/usr/bin/env python3

# %% [markdown]
# # Calculate all motif integers

# %% [markdown]
# ### Prepare environment, input, and output files

# %%
# Load libraries
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import product
import Bio.Data.IUPACData as bdi
import ast
from matplotlib.pyplot import xticks
from numpy import size

# Define colors for plotting
fill_color = "darkgrey"
line_color = "black"

# %%
# Input files: 5mC and 6mA motifs
tsv_motifs_5mC = sys.argv[1]
tsv_motifs_6mA = sys.argv[2]
input_files = [tsv_motifs_5mC, tsv_motifs_6mA]
# Names for output figures
png_motiflengths_sidebyside = sys.argv[3]
png_motiflengths_vertical = sys.argv[4]
# Names for output files
dict_motif_integers = sys.argv[5]
set_motif_integers = sys.argv[6]

# Titles for motif length distributions
title_5mC = 'Distribution of 5mC motif lengths'
title_6mA = 'Distribution of 6mA motif lengths'

# %% [markdown]
# ### Plot motif length distribution

# %%
def plot_motif_length_distribution(ax, motif_tsv, plot_title):
    # Read the TSV file
    df = pd.read_csv(motif_tsv, sep='\t')

    # Extract the motifs and calculate their lengths
    df['motif_length'] = df.iloc[:, 0].apply(len)

    # Calculate the median motif length
    median_length = df['motif_length'].median()

    # Plot the distribution of motif lengths
    sns.histplot(df['motif_length'], bins=range(1, df['motif_length'].max() + 1), ax=ax, color=fill_color)
    ax.axvline(median_length, color=line_color, linestyle='--', label=f'{int(median_length)}')
    ax.set_title(plot_title)
    ax.set_xlabel('Motif length (bases)')
    ax.set_ylabel('Frequency')
    ax.legend()

    # Set x-ticks
    max_length = df['motif_length'].max()
    ax.set_xticks(range(1, max_length + 1, 3))
    

# %%
def plot_side_by_side(input_file_1, input_file_2, title_1, title_2, png_path):
    # Create a figure with two subplots arranged horizontally
    fig, axs = plt.subplots(1, 2, figsize=(20, 6), sharey=True)

    # Plot the motif length distributions in the subplots
    plot_motif_length_distribution(axs[0], input_file_1, title_1)
    plot_motif_length_distribution(axs[1], input_file_2, title_2)

    # Ensure the subplots have the same y-axis
    plt.tight_layout()
    plt.savefig(png_path)
    #plt.show()

# %%
def plot_vertical(input_file_1, input_file_2, title_1, title_2, png_path):
    # Create a figure with two subplots arranged vertically
    fig, axs = plt.subplots(2, 1, figsize=(4, 10), gridspec_kw={'height_ratios': [1, 2]}, sharex=True)

    # Plot the motif length distributions in the subplots
    plot_motif_length_distribution(axs[0], input_file_1, title_1)
    plot_motif_length_distribution(axs[1], input_file_2, title_2)

    # Ensure the subplots have the same x-axis
    plt.tight_layout()
    plt.savefig(png_path)
    #plt.show()


# %%
plot_side_by_side(tsv_motifs_5mC, tsv_motifs_6mA, title_5mC, title_6mA, png_motiflengths_sidebyside)

# %%
plot_vertical(tsv_motifs_5mC, tsv_motifs_6mA, title_5mC, title_6mA, png_motiflengths_vertical)


# %% [markdown]
# ### DNA-to-integer settings and function

# %%
# Define the DNA to integer mapping
dna = {"A": 0, "C": 1, "T": 2, "G": 3, "-": 4, "a": 5, "c": 6}
middle_index = 21  # 0-based index for the middle base in a 44 bp sequence
kmax = 12          # maximum motif length to be analysed

# %%
def extend_ambiguous_dna(ambiguous_motif):
    """Return a list of all possible sequences given an ambiguous DNA motif."""
    d = bdi.ambiguous_dna_values
    return list(map("".join, product(*map(d.get, ambiguous_motif))))


# %%
def lower_case_methylation(motif, position):
    """Return the motif with the methylated base as lower case letter."""
    if motif[position] == 'C' or motif[position] == 'A':
        return motif[:position] + motif[position].lower() + motif[position+1:]
    else:
        return motif

# %% [markdown]
# ### Calculate integer values for motifs

# %%
# Function to create a k-mer integer value
def create_kmer_integer(kmer):
    """Function to assign a unique integer to each unique kmer.
    Values are calculated based on kmax (e.g. 12) length kmers.
    If kmers are shorter they will get padded with gaps."""
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
def calculate_motif_integers(input_files):
    """Function to calculate the integer values for motifs and store them in a dictionary."""
    motif_dict = {}
    all_motifs = set()
    for input_file in input_files:
        with open(input_file, 'r') as input:
            next(input)  # Skip the header
            for line in input:
                # Extract the motif and the methylation position
                ambiguous_motif, meth_position = line.strip().split('\t')
                if len(ambiguous_motif) > kmax:
                    continue
                meth_position = int(meth_position)
                # Expand the ambiguous/consensus motif into it's non-amibguous version
                expanded_motifs = extend_ambiguous_dna(ambiguous_motif)
                ambiguous_motif_string = lower_case_methylation(ambiguous_motif, meth_position)
                # Format each of the exanded motifs (a string and an integer version)
                for motif in expanded_motifs:
                    motif_string = lower_case_methylation(motif, meth_position)
                    motif_integer = create_kmer_integer(motif_string)
                    if motif_integer not in motif_dict:
                        motif_dict[motif_integer] = set()
                    motif_dict[motif_integer].add(ambiguous_motif_string)
                    all_motifs.add(motif_integer)
    return motif_dict, all_motifs


# %%
# Calculate motif integers
motif_integers_dict, all_motifs = calculate_motif_integers(input_files)

# %%
motif_integers_dict

# %%
all_motifs

# %% [markdown]
# ### Analyse and save the data

# %%
# Save the motif dictionary to a file
with open(dict_motif_integers, 'w') as output:
    output.write(str(motif_integers_dict)) # Convert dict to string and write to file

# %%
# Save the motif set to a file
with open(set_motif_integers, 'w') as output:
    output.write(str(all_motifs))  # Convert set to string and write to file

