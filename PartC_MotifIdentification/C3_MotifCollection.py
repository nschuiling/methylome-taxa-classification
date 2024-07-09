#!/usr/bin/env python3

# %% [markdown]
# # Explore overlap between REBASE and Nanomotifs

# %%
import sys  
from matplotlib import pyplot as plt
from matplotlib_venn import venn2
import seaborn as sns
import pandas as pd

# Set seaborn style
sns.set_style("whitegrid")
# Set seaborn color palette
sns.set_palette("GnBu")

# %%
# Input file paths
modification_type = sys.argv[1]
all_nanomotifs_path = sys.argv[2]
rebase_motifs_path = sys.argv[3]
# Output file paths
nonrebase_nanomotifs_path = sys.argv[4]
overlap_rebase_nanomotifs_path = sys.argv[5]
rebase_and_nanomotifs_path = sys.argv[6]
motif_overlap_venn_png_path = sys.argv[7]
motif_overlap_venn_png_path_filtered = sys.argv[8]


# %%
# Function to read in the motifs from a TSV file
def read_motif_tsv_file(path):
    df = pd.read_csv(path, sep='\t')
    df['meth_position'] = df['meth_position'].astype('int64')
    return set(zip(df['motif'], df['meth_position']))

# %%
# Read in the motif sets
nanomotifs_motifs = read_motif_tsv_file(all_nanomotifs_path)
rebase_motifs = read_motif_tsv_file(rebase_motifs_path)

# %%
print(modification_type, " Nanomotifs: ")
print(nanomotifs_motifs)

# %%
print(modification_type, " REBASE motifs: ")
print(rebase_motifs)

# %%
# Function to compare the REBASE motifs with the Nanomotifs
def compare_motifs(rebase_motifs, nanomotifs_motifs):
    unique_rebase = rebase_motifs - nanomotifs_motifs
    unique_nanomotifs = nanomotifs_motifs - rebase_motifs
    motif_intersection = rebase_motifs & nanomotifs_motifs

    return list(unique_rebase), list(unique_nanomotifs), list(motif_intersection)


# %%
# Compare REBASE and Nanomotifs
unique_rebase, unique_nanomotifs, motif_intersection = compare_motifs(rebase_motifs, nanomotifs_motifs)

# %%
# Print the number of unique and overlapping motifs
print("Nr of overlapping REBASE and Nanomotifs motifs:", len(motif_intersection))
print("Nr of REBASE motifs, not in the Nanomotifs:", len(unique_rebase))
print("Nr of Nanomotifs motifs, not in the REBASE motifs:", len(unique_nanomotifs))


# %% [markdown]
# ### Create a Venn diagram for the overlap REBASE-Nanomotif

# %%
# Function to create a Venn diagram of the motifs
from tkinter import font

def create_venn(nr_unique_rebase, nr_unique_nanomotifs, nr_motif_intersection, modification_type, png_path):
    plt.rcParams.update({'font.size': 14})
    venn2(subsets = (nr_unique_rebase, nr_unique_nanomotifs, nr_motif_intersection),
          set_labels = (f'{modification_type} REBASE motifs', f'{modification_type} Nanomotifs'),
          set_colors=("#1f78b4", "#33a02c"))
    # Add title
    plt.tight_layout()
    plt.savefig(png_path)
    #plt.show()
    plt.close()
    return

# %%
# Create venn diagram
create_venn(len(unique_rebase), len(unique_nanomotifs), len(motif_intersection), modification_type,
            motif_overlap_venn_png_path)


# %%
# Function to save the unique motifs to a tsv file
def save_motifs_to_tsv(motifs, filepath):
    with open(filepath, 'w') as f:
        f.write("motif\tmeth_position\n")
        for motif, meth_position in motifs:
            f.write(f"{motif}\t{meth_position}\n")
    return

# %%
# Save the unique and overlapping motifs for further analysis
save_motifs_to_tsv(unique_nanomotifs, nonrebase_nanomotifs_path)
save_motifs_to_tsv(motif_intersection, overlap_rebase_nanomotifs_path)

# %%
# Also save the combination: rebase motifs and nanomotifs
rebase_and_nanomotifs = rebase_motifs | nanomotifs_motifs
save_motifs_to_tsv(rebase_and_nanomotifs, rebase_and_nanomotifs_path)



# %% [markdown]
# ### Create a venn diagram for the length-filtered motifs

# %%
# Function to create a Venn diagram of the motifs (length-filtered version)
def create_length_filtered_venn(nr_unique_rebase, nr_unique_nanomotifs, nr_motif_intersection, modification_type, png_path):
    plt.rcParams.update({'font.size': 14})
    venn2(subsets = (nr_unique_rebase, nr_unique_nanomotifs, nr_motif_intersection),
          set_labels = (f'Length-filtered \n {modification_type} REBASE motifs', f'Length-filtered \n {modification_type} Nanomotifs'),
          set_colors=("#7570b3", "#1b9e77")) 
    # Add title
    plt.tight_layout()
    plt.savefig(png_path)
    #plt.show()
    plt.close()
    return

# %%
unique_rebase = [m for m in unique_rebase if 3<len(m[0])<13]
unique_nanomotifs = [m for m in unique_nanomotifs if 3<len(m[0])<13]
motif_intersection = [m for m in motif_intersection if 3<len(m[0])<13]

# %%
create_length_filtered_venn(len(unique_rebase), len(unique_nanomotifs), len(motif_intersection), 
                            modification_type, motif_overlap_venn_png_path_filtered)
