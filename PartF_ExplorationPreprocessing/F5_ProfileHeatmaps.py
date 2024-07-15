#!/usr/bin/env python3

# %% [markdown]
# # Profile heatmaps

# %% [markdown]
# ### Prepare environment, input, and output files

# %%
# Utilities
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import polars as pl
import numpy as np
import pickle
from Bio import Phylo
from io import StringIO

# %%
tsv_methylation_profile = sys.argv[1]
taxon_dicts = sys.argv[2]
tree_node_orders_pkl = sys.argv[3]
tree_folder = sys.argv[4]
output_folder = sys.argv[5]

# %%
# Load the orders of the taxa (in line with the trees)
with open(tree_node_orders_pkl, 'rb') as file:
    tree_node_orders = pickle.load(file)

species_order = tree_node_orders["species"]
genus_order = tree_node_orders["genus"]
family_order = tree_node_orders["family"]

# %%
# Load newick trees
with open(f'{tree_folder}/full_newick_tree.pkl', 'rb') as file: 
    newick_tree_full = pickle.load(file)

with open(f'{tree_folder}/newick_tree_species.pkl', 'rb') as file: 
    newick_tree_species = pickle.load(file)

with open(f'{tree_folder}/newick_tree_genus.pkl', 'rb') as file: 
    newick_tree_genus = pickle.load(file)

with open(f'{tree_folder}/newick_tree_family.pkl', 'rb') as file: 
    newick_tree_family = pickle.load(file)

# %% [markdown]
# ### Load the data

# %%
# Load the complete profile .tsv file as polars DataFrame
df_methylation_profile = pl.read_csv(tsv_methylation_profile, separator='\t', has_header=True)

# %%
print("Nr of reads: ", df_methylation_profile.shape[0])
print("Nr of columns: ", df_methylation_profile.shape[1])

# %%
# Define the column types in the complete profile DataFrame
annotation_columns = pl.col("read_id", "species_id", "genus_id", "family_id", "sequencing_run", "read_length", "methylation_count")
profile_columns = pl.col("*").exclude("read_id", "taxonomic_id", "species_id", "genus_id", "family_id", "sequencing_run", "read_length", "methylation_count")
profile_columns_list = df_methylation_profile.select(profile_columns).columns

# %%
# Load the dictionaries from the file
with open(taxon_dicts, 'rb') as f:
    taxon_dicts = pickle.load(f)
    
species_dict = taxon_dicts['species_dict']
genus_dict = taxon_dicts['genus_dict']
family_dict = taxon_dicts['family_dict']

# %%
# Align the dictionaries with the taxa lists (string formats)
def replace_characters_in_dict(input_dict):
    return {key: value.replace("[", " ").replace("]", " ").replace("_", " ") for key, value in input_dict.items()}

species_dict = replace_characters_in_dict(species_dict)
genus_dict = replace_characters_in_dict(genus_dict)
family_dict = replace_characters_in_dict(family_dict)

# %%
# Show the data
df_methylation_profile

# %%
# Map the taxonomic IDs to taxon names in a new columns
df_methylation_profile = df_methylation_profile.with_columns(species_id=pl.col('species_id').replace(species_dict),
                                                             genus_id=pl.col('genus_id').replace(genus_dict),
                                                             family_id=pl.col('family_id').replace(family_dict))

# %%
# Show the data
df_methylation_profile

# %% [markdown]
# ### Create average read profiles per taxa

# %%
# Create per-taxon mean methylation profiles
def create_taxon_average_profile(data, rank):
    rank_column = f"{rank}_id"
    data = data.group_by(rank_column).mean()
    return data

# %%
# Average profiles
average_profile_per_species = create_taxon_average_profile(df_methylation_profile, "species")
average_profile_per_genus = create_taxon_average_profile(df_methylation_profile, "genus")
average_profile_per_family = create_taxon_average_profile(df_methylation_profile, "family")
overall_average_profile = df_methylation_profile.mean()

# %%
# Example
average_profile_per_species

# %%
# Sort profiles by tree order
# Species
species_order_dict = {val: idx for idx, val in enumerate(species_order)}
average_profile_per_species = average_profile_per_species.with_columns(order=pl.col("species_id").replace(species_order_dict)).sort(pl.col("order").cast(pl.Int8)).drop("order")

# Genus
genus_order_dict = {val: idx for idx, val in enumerate(genus_order)}
average_profile_per_genus = average_profile_per_genus.with_columns(order=pl.col("genus_id").replace(genus_order_dict)).sort(pl.col("order").cast(pl.Int8)).drop("order")

# Family
family_order_dict = {val: idx for idx, val in enumerate(family_order)}
average_profile_per_family = average_profile_per_family.with_columns(order=pl.col("family_id").replace(family_order_dict)).sort(pl.col("order").cast(pl.Int8)).drop("order")


# %%
average_profile_per_species

# %%
# Function to select a number (n_motifs) of median/most frequent motifs
def select_motifs(data, n_motifs, frequency):

    # Calculate the mean frequencies for each motif over all species
    motif_frequencies = data.select(profile_columns).mean()
    # Create a list of all motifs sorted by frequency
    sorted_motifs = motif_frequencies.transpose(include_header=True, header_name="motif",
                                                    column_names=["mean_normalized_count"]).sort(by="mean_normalized_count").select("motif")
    # Select the desired number of motifs, at the desired frequency of occurrence
    if frequency == "most":
        selected_motifs = sorted_motifs[-n_motifs:]
    elif frequency == "median":
        nr_motifs = len(sorted_motifs)
        lower_index = int(nr_motifs//2-(n_motifs/2))
        upper_index = int(nr_motifs//2+(n_motifs/2))
        selected_motifs = sorted_motifs[lower_index : upper_index]

    return list(list(selected_motifs)[0])

# %%
# Function to plot the average profiles (for selected motifs) in a heatmap
def plot_average_profile_heatmap(data, rank, selected_motifs, png_name):

    # Select the motifs to show
    motif_columns = pl.col(selected_motifs)
    profile_data = data.select(motif_columns)

    # Define the taxon labels
    taxon_labels = list(data[f"{rank}_id"])

    # Create the figure
    fig_height = len(taxon_labels)//3.5 + 3
    fig_width = len(selected_motifs)//3.5 + 6
    plt.figure(figsize=(fig_width, fig_height))
    sns.heatmap(profile_data, cmap="crest_r", yticklabels=taxon_labels, xticklabels=selected_motifs)
    plt.xlabel("Motifs")
    plt.ylabel(f"{rank.capitalize()}")
    plt.tight_layout()
    plt.savefig(png_name, bbox_inches='tight')
    plt.show()

# %%
for n_motifs in [20, 30]:
    for frequency in ["median", "most"]:
        for taxonomy, average_profile in (["species", average_profile_per_species],
                                          ["genus", average_profile_per_genus],
                                          ["family", average_profile_per_family]):
            
            selected_motifs = select_motifs(average_profile, n_motifs, frequency)
            png_name = f"{output_folder}/AverageProfilePer_{taxonomy}_{frequency}{n_motifs}_Motifs.png"
            plot_average_profile_heatmap(average_profile, taxonomy, selected_motifs, png_name)

# %% [markdown]
# ### Plot tree and heatmap together

# %%
def plot_newick_tree_and_heatmap(data, rank, selected_motifs, newick_tree, png_name):


    taxon_labels = list(list(data.select(pl.col([f"{rank}_id"])))[0])
    fig_height = len(taxon_labels)//3.5 + 3
    fig_width = len(selected_motifs)//3.5 + 9
    plt.figure(figsize=(fig_width, fig_height))
    
    # Initialize plot with two subplots
    plt.rcParams["lines.linewidth"] = 1
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, fig_height), width_ratios=[1, 5])

    # Format the tree for plotting
    tree_phylo = Phylo.read(StringIO(newick_tree), "newick")
    # Set color preferences and draw the tree
    tree_phylo.root.color = "gray"
    Phylo.draw(tree_phylo, axes=ax1, label_func=lambda x: x.name, do_show=False) #, label_colors=lambda x: "blue")
    ax1.axis('off')

    # HEATMAP
    motif_columns = pl.col(selected_motifs)
    profile_data = data.select(motif_columns)
    sns.heatmap(profile_data, cmap="crest_r", xticklabels=selected_motifs,
                cbar_kws={"aspect":80}, axes=ax2, yticklabels=taxon_labels)
    plt.xlabel("Motifs")

    # Adjusting the space between the subplots
    plt.tight_layout()
    plt.savefig(png_name, bbox_inches='tight')
    # Showing the figure
    plt.show()

# %%
for n_motifs in [20, 30]:
    for frequency in ["median", "most"]:
        for taxonomy, average_profile, newick_tree in (["species", average_profile_per_species, newick_tree_species],
                                          ["genus", average_profile_per_genus, newick_tree_genus],
                                          ["family", average_profile_per_family, newick_tree_family]):
            
            selected_motifs = select_motifs(average_profile, n_motifs, frequency)
            png_name = f"{output_folder}/Tree_AverageProfilePer_{taxonomy}_{frequency}{n_motifs}_Motifs.png"
            plot_newick_tree_and_heatmap(average_profile, taxonomy, selected_motifs, newick_tree, png_name)

