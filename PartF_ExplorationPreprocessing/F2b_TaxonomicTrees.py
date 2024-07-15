#!/usr/bin/env python3

# %% [markdown]
# # Draw taxonomic tree with all species (and genera, families) in the data

# %%
# Set-up environment
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from Bio import Phylo
from io import StringIO
import taxoniq
import pickle
from ete3 import Tree
import sys

# %%
output_prefix = sys.argv[1]
list_top50_species = sys.argv[2]

# %% [markdown]
# ### Load all species in the data (top 50) and obtain their phylogenetic paths

# %%
# Load the top 50 species list (i.e. all species in the training data)
with open(list_top50_species, 'rb') as f:
    most_freq_species = pickle.load(f)

# %%
# Function to get taxonomic path for each species ID
def get_taxonomic_path(species_id):
    species = taxoniq.Taxon(species_id)
    name = f"{species.scientific_name}"
    path = [f"{t.scientific_name}" for t in species.ranked_lineage]
    return path

# %%
# Function to prepare taxonomic data
def prepare_taxonomic_paths(species_ids):
    taxonomic_paths = []
    for species_id in species_ids:
        path = get_taxonomic_path(species_id)
        taxonomic_paths.append((path))
    return taxonomic_paths

# %%
paths = prepare_taxonomic_paths(most_freq_species)
print(paths)

# %%
# Check whether all paths have the same length
print(np.unique([len(t) for t in paths]))

# %% [markdown]
# ### Create a tree structure

# %%
# Initialize the tree
tree_structure = Tree(name="Root")

# Add paths to the tree
for path in paths:
    node = tree_structure
    #path = path[start:]
    for element in reversed(path):
        element = element.replace(" ", "_")
        if element in [child.name for child in node.children]:
            node = node&element
        else:
            node = node.add_child(name=element)

# %%
print(tree_structure)

# %% [markdown]
# ### Tree to newick format

# %%
# Full tree (species -> root) including all internal nodes
full_newick_tree = tree_structure.write(format=8)
print(full_newick_tree)

# Species level tree without internal nodes
newick_tree_species = tree_structure.write(format=9)
print(newick_tree_species)

# Genus level tree without internal nodes
for leaf in tree_structure:
    leaf.delete(prevent_nondicotomic=False)
newick_tree_genus = tree_structure.write(format=9)
print(newick_tree_genus)

# Family level tree without internal nodes
for leaf in tree_structure:
    leaf.delete(prevent_nondicotomic=False)
newick_tree_family = tree_structure.write(format=9)
print(newick_tree_family)

# %%
# Save all tree versions

with open(f'{output_prefix}/full_newick_tree.pkl', 'wb') as file: 
    pickle.dump(full_newick_tree, file)

with open(f'{output_prefix}/newick_tree_species.pkl', 'wb') as file: 
    pickle.dump(newick_tree_species, file) 

with open(f'{output_prefix}/newick_tree_genus.pkl', 'wb') as file: 
    pickle.dump(newick_tree_genus, file) 

with open(f'{output_prefix}/newick_tree_family.pkl', 'wb') as file: 
    pickle.dump(newick_tree_family, file)

# %% [markdown]
# ### Plot the tree

# %%
def plot_newick_tree(newick_tree, fig_width, fig_height, tree_png):

    # Initialize the plot
    plt.rcParams["lines.linewidth"] = 1
    fig = plt.figure(figsize=(fig_width, fig_height), dpi=100)
    ax = fig.add_subplot(1, 1, 1)

    # Format the tree for plotting
    tree_phylo = Phylo.read(StringIO(newick_tree), "newick")

    # Set color preferences and draw the tree
    tree_phylo.root.color = "gray"
    Phylo.draw(tree_phylo, axes=ax, label_func=lambda x: x.name, do_show=False) #, label_colors=lambda x: "blue")
    ax.axis('off')
    
    # Adjusting the space between the subplots
    plt.tight_layout()
    plt.savefig(tree_png, bbox_inches='tight')
    # Showing the figure
    plt.show()


# %%
full_tree_png = f"{output_prefix}/full_tree.png"
plot_newick_tree(full_newick_tree, 16, 24, full_tree_png)

# %%
species_tree_png = f"{output_prefix}/species_tree.png"
plot_newick_tree(newick_tree_species, 6, 17, species_tree_png)

# %%
genus_tree_png = f"{output_prefix}/genus_tree.png"
plot_newick_tree(newick_tree_genus, 4, 10, genus_tree_png)

# %%
family_tree_png = f"{output_prefix}/family_tree.png"
plot_newick_tree(newick_tree_family, 4, 7, family_tree_png)

# %% [markdown]
# ### Retrieve a tree-sorted list of taxonomies

# %%
def get_newick_tree_node_orders(newick_tree):

    # Define the tree to make it searchable
    tree_phylo = Phylo.read(StringIO(newick_tree), "newick")

    # List of species
    taxa_nodes = [tip.name for tip in tree_phylo.get_terminals()]
    taxa_list = [node.replace("_", " ") for node in taxa_nodes]
    print(taxa_list)

    return taxa_list


# %%
species_node_order = get_newick_tree_node_orders(newick_tree_species)

# %%
genus_node_order = get_newick_tree_node_orders(newick_tree_genus)

# %%
family_node_order = get_newick_tree_node_orders(newick_tree_family)

# %%
tree_node_orders = {"species":species_node_order,
                    "genus":genus_node_order,
                    "family":family_node_order}

# %%
with open(f"{output_prefix}/tree_orders_dict.pkl", 'wb') as file:
    pickle.dump(tree_node_orders, file)


# %%
# To load the dictionary elsewhere
#with open(f"{output_prefix}/tree_orders_dict.pkl", 'rb') as file:
#    tree_node_orders = pickle.load(file)

