#!/usr/bin/env python3

# %% [markdown]
# # Script for plotting of pre-calculated cluster data

# %%
# Utilities
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import polars as pl
import numpy as np
import pickle
import sys

# %% [markdown]
# ### Load data

# %%
cluster_type = sys.argv[1]
scaler_type = sys.argv[2]
output_folder = sys.argv[3]
cluster_data_file = sys.argv[4]
tree_node_orders_pkl = sys.argv[5]

# %%
output_prefix = f"{output_folder}/{cluster_type}_{scaler_type}"

# %%
cluster_data = pd.read_csv(cluster_data_file, index_col=0)

# %%
# Load the orders of the taxa (in line with the trees)
with open(tree_node_orders_pkl, 'rb') as file:
    tree_node_orders = pickle.load(file)

species_order = tree_node_orders["species"]
genus_order = tree_node_orders["genus"]
family_order = tree_node_orders["family"]

# %% [markdown]
# ### Sort dataframe by tree order

# %%
cluster_data['true_species'] = cluster_data['true_species'].str.replace(
    "[", " ").str.replace("]", " ").str.replace("_", " ")

# %%
# Sort
sorter_index = dict(zip(species_order, range(len(species_order))))
cluster_data['sort_column'] = cluster_data['true_species'].map(sorter_index)
cluster_data.sort_values(by="sort_column", ascending=True).drop("sort_column", axis=1)

# %% [markdown]
# ### Plot function

# %%
def plot_clusters(cluster_data, algorithm, rank, png_name, sorted_labels, fig_size=(15, 12)):

    true_labels_column = f"true_{rank}"
    n_labels = cluster_data[true_labels_column].nunique()

    # Plot t-SNE clusters
    plt.figure(figsize=fig_size)
    sns.scatterplot(x='0', y='1' , hue=true_labels_column, data=cluster_data, alpha=0.9, s=8, palette='tab20b') #tab10
    plt.xlabel(f"{algorithm.upper()} Component 1")
    plt.ylabel(f"{algorithm.upper()} Component 2")
    
    # Sort legend (by tree order)
    handles, labels = plt.gca().get_legend_handles_labels()
    sorted_handles_labels = sorted(zip(handles, labels), key=lambda x: sorted_labels.index(x[1]) if x[1] in sorted_labels else float('inf'))
    sorted_handles, sorted_labels = zip(*sorted_handles_labels)
    plt.legend(sorted_handles, sorted_labels, bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0,
               title=rank.capitalize(), frameon=False, ncol=1, markerscale=3)
    
    # Adjust layout
    plt.tight_layout()
    plt.savefig(png_name, bbox_inches='tight')
    #plt.show()
    plt.close()

# %%
def plot_clusters_by_abundance(cluster_data, algorithm, rank, ntop, png_prefix, sorted_labels):

    true_labels_column = f"true_{rank}"

    # Get the 20 most common taxa
    top_taxa = list(cluster_data[true_labels_column].value_counts().nlargest(ntop).index)

    # Filter data for the top 20 taxa and the rest
    top_taxa_data = cluster_data[cluster_data[true_labels_column].isin(top_taxa)]
    rest_taxa_data = cluster_data[~cluster_data[true_labels_column].isin(top_taxa)]

    # Create a plot for both the top 20 and the other taxa
    plot_clusters(top_taxa_data, algorithm, rank, f"{png_prefix}_top{ntop}.png", sorted_labels, (12, 12))
    plot_clusters(rest_taxa_data, algorithm, rank, f"{png_prefix}_rest{ntop}.png", sorted_labels, (12, 12))

# %%
# Plot clustering
for rank, sorted_labels in [("species", species_order),  ("genus", genus_order), ("family", family_order)]:
    png_name = f"{output_prefix}_{rank}"
    sns.set(style="white", font_scale=1.3)
    plot_clusters(cluster_data, cluster_type, rank, f"{png_name}.png", sorted_labels)
    sns.set(style="white", font_scale=1.2)
    plot_clusters_by_abundance(cluster_data, cluster_type, rank, 33, png_name, sorted_labels)

