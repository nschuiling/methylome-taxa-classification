#!/usr/bin/env python3

# %% [markdown]
# # Profile clustering plots

# %% [markdown]
# ### Prepare environment, input, and output files

# %%
# Utilities
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import polars as pl
import numpy as np
import pickle
import sys

# Libraries for clustering
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from umap import UMAP
from sklearn.preprocessing import RobustScaler, MinMaxScaler, StandardScaler

# Extra speed
#import cuml
#from cuml import UMAP

# %%
tsv_methylation_profile = sys.argv[1]
taxon_dicts = sys.argv[2]
png_prefix = sys.argv[3]

# %%
seed = 54321


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

# Order in which to show species, genus, families (from phylogenetic tree)
species_order = ['Salmonella enterica', 'Escherichia coli', 'Psychrobacter sp. WY6', 'Psychrobacter sp. 28M-43', 'Psychrobacter sp. DAB AL43B', 'Psychrobacter sp.', 'Psychrobacter sp. P11G5', 'Psychrobacter sp. KH172YL61', 'Psychrobacter sp. KCTC 72983', 'Psychrobacter cryohalolentis', 'Psychrobacter sanguinis', 'Psychrobacter sp. G', 'Psychrobacter sp. P2G3', 'Moraxella osloensis', 'Vibrio casei', 'Vibrio algivorus', 'Pseudomonas aeruginosa', 'Halomonas titanicae', 'Brevibacterium aurantiacum', 'Glutamicibacter arilaitensis', 'Brachybacterium vulturis', 'Brachybacterium avium', 'Brachybacterium sp. P6-10-X1', 'Brachybacterium sp. Z12', 'Corynebacterium casei', 'Bifidobacterium adolescentis', 'Bifidobacterium longum', 'Collinsella aerofaciens', 'Enterococcus faecalis', 'Streptococcus thermophilus', 'Staphylococcus aureus', 'Staphylococcus equorum', 'Listeria monocytogenes', 'Faecalibacterium prausnitzii', 'Coprococcus sp. ART55/1', 'Agathobacter rectalis', 'Anaerobutyricum hallii', 'Lachnospira eligens', 'Blautia obeum', ' Ruminococcus  torques', 'Anaerostipes hadrus', 'Roseburia intestinalis', 'Roseburia hominis', 'Wujia chipingensis', 'Simiaoa sunii', 'Phascolarctobacterium sp. Marseille-Q4147', 'Segatella copri', 'Phocaeicola vulgatus', 'Parabacteroides merdae', 'Akkermansia muciniphila']
genus_order = ['Salmonella', 'Escherichia', 'Psychrobacter', 'Psychrobacter', 'Psychrobacter', 'Psychrobacter', 'Psychrobacter', 'Psychrobacter', 'Psychrobacter', 'Psychrobacter', 'Psychrobacter', 'Psychrobacter', 'Psychrobacter', 'Moraxella', 'Vibrio', 'Vibrio', 'Pseudomonas', 'Halomonas', 'Brevibacterium', 'Glutamicibacter', 'Brachybacterium', 'Brachybacterium', 'Brachybacterium', 'Brachybacterium', 'Corynebacterium', 'Bifidobacterium', 'Bifidobacterium', 'Collinsella', 'Enterococcus', 'Streptococcus', 'Staphylococcus', 'Staphylococcus', 'Listeria', 'Faecalibacterium', 'Coprococcus', 'Agathobacter', 'Anaerobutyricum', 'Lachnospira', 'Blautia', 'Mediterraneibacter', 'Anaerostipes', 'Roseburia', 'Roseburia', 'Wujia', 'Simiaoa', 'Phascolarctobacterium', 'Segatella', 'Phocaeicola', 'Parabacteroides', 'Akkermansia']
family_order = ['Enterobacterales', 'Enterobacterales', 'Moraxellales', 'Moraxellales', 'Moraxellales', 'Moraxellales', 'Moraxellales', 'Moraxellales', 'Moraxellales', 'Moraxellales', 'Moraxellales', 'Moraxellales', 'Moraxellales', 'Moraxellales', 'Vibrionales', 'Vibrionales', 'Pseudomonadales', 'Oceanospirillales', 'Micrococcales', 'Micrococcales', 'Micrococcales', 'Micrococcales', 'Micrococcales', 'Micrococcales', 'Mycobacteriales', 'Bifidobacteriales', 'Bifidobacteriales', 'Coriobacteriales', 'Lactobacillales', 'Lactobacillales', 'Bacillales', 'Bacillales', 'Bacillales', 'Eubacteriales', 'Eubacteriales', 'Eubacteriales', 'Eubacteriales', 'Eubacteriales', 'Eubacteriales', 'Eubacteriales', 'Eubacteriales', 'Eubacteriales', 'Eubacteriales', 'Eubacteriales', 'Eubacteriales', 'Acidaminococcales', 'Bacteroidales', 'Bacteroidales', 'Bacteroidales', 'Verrucomicrobiales']

# %% [markdown]
# ### Numpy version of the profile and labels

# %%
np_methylation_profile = df_methylation_profile.select(profile_columns).to_numpy()
np_methylation_profile

# %%
# Define the true labels
species_labels = [species_dict[label] for label in df_methylation_profile["species_id"].to_numpy()]
genus_labels = [genus_dict[label] for label in df_methylation_profile["genus_id"].to_numpy()]
family_labels = [family_dict[label] for label in df_methylation_profile["family_id"].to_numpy()]

# %% [markdown]
# ### Standard clustering set-up

# %%
def perform_clustering(algorithm, n_components, np_methylation_profile,
                       species_labels, genus_labels, family_labels, seed=54321):
    
    # Perform clustering dependent on the algorithm
    if algorithm == "PCA":
        pca = PCA(n_components, random_state=seed) 
        cluster_data = pd.DataFrame(pca.fit_transform(np_methylation_profile))
    elif algorithm == "UMAP":
        umap = UMAP(n_components=n_components, n_jobs=6, low_memory=True) #, random_state=seed)
        cluster_data = pd.DataFrame(umap.fit_transform(np_methylation_profile))
    elif algorithm == "t-SNE":
        tsne = TSNE(n_components=n_components, learning_rate='auto', init='random', random_state=seed)
        cluster_data = pd.DataFrame(tsne.fit_transform(np_methylation_profile))
    
    # Annotate the clusters with the true labels
    cluster_data['true_species'] = species_labels
    cluster_data['true_genus'] = genus_labels
    cluster_data['true_family'] = family_labels

    return cluster_data
    
# %%
def plot_clusters(cluster_data, algorithm, rank, png_name, sorted_labels, fig_size=(14,8)):

    true_labels_column = f"true_{rank}"

    # Plot t-SNE clusters
    plt.figure(figsize=fig_size)
    sns.scatterplot(x=0, y=1, hue=true_labels_column, data=cluster_data, alpha=0.9, s=8, palette='tab20b') #tab10
    plt.xlabel(f"{algorithm} Component 1")
    plt.ylabel(f"{algorithm} Component 2")
    
    # Sort legend
    handles, labels = plt.gca().get_legend_handles_labels()
    sorted_handles_labels = sorted(zip(handles, labels), key=lambda x: sorted_labels.index(x[1]) if x[1] in sorted_labels else float('inf'))
    sorted_handles, sorted_labels = zip(*sorted_handles_labels)
    plt.legend(sorted_handles, sorted_labels, bbox_to_anchor=(1.04, 1), loc='upper left', title=rank.capitalize(), frameon=False, ncol=1, markerscale=2)
    #plt.legend(bbox_to_anchor=(1.04, 1), loc='upper left', title=rank.capitalize(), frameon=False, ncol=1, markerscale=2)
    
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
    plot_clusters(top_taxa_data, algorithm, rank, f"{png_prefix}_top{ntop}.png", sorted_labels)
    plot_clusters(rest_taxa_data, algorithm, rank, f"{png_prefix}_rest{ntop}.png", sorted_labels)


# %% [markdown]
# ### Perform UMAP clustering

# %%
# Perform UMAP clustering
umap_data = perform_clustering("UMAP", 2, np_methylation_profile, species_labels, genus_labels, family_labels, seed=54321)
umap_data_file = f"{png_prefix}_noscaling_umap.csv"
umap_data.to_csv(umap_data_file)

# %%
# Plot UMAP clustering
for rank, sorted_labels in [("species", species_order),  ("genus", genus_order), ("family", family_order)]:
    umap_png_name = f"{png_prefix}_noscaling_umap_{rank}"
    sns.set(style="white")
    plot_clusters(umap_data, "UMAP", rank, f"{umap_png_name}.png", sorted_labels)
    sns.set(style="white", font_scale=1.2)
    plot_clusters_by_abundance(umap_data, "UMAP", rank, 20, umap_png_name, sorted_labels)

# %%
del umap_data

# %% [markdown]
# ### Perform PCA clustering

# %%
# Perform UMAP clustering
pca_data = perform_clustering("PCA", 2, np_methylation_profile, species_labels, genus_labels, family_labels, seed=54321)
pca_data_file = f"{png_prefix}_noscaling_pca.csv"
pca_data.to_csv(pca_data_file)

# %%
# Plot UMAP clustering
for rank, sorted_labels in [("species", species_order),  ("genus", genus_order), ("family", family_order)]:
    pca_png_name = f"{png_prefix}_noscaling_pca_{rank}"
    sns.set(style="white")
    plot_clusters(pca_data, "PCA", rank, f"{pca_png_name}.png", sorted_labels)
    sns.set(style="white", font_scale=1.2)
    plot_clusters_by_abundance(pca_data, "PCA", rank, 20, pca_png_name, sorted_labels)

# %%
del pca_data

# %% [markdown]
# ### Perform Robust scaling

# %%
# Scale the data using the RobustScaler
scaler = RobustScaler()
np_robust_methylation_profile = scaler.fit_transform(np_methylation_profile)

# %% [markdown]
# ### Perform UMAP clustering on scaled data

# %%
# Perform UMAP clustering
robust_umap_data = perform_clustering("UMAP", 2, np_robust_methylation_profile, species_labels, genus_labels, family_labels, seed=54321)
robust_umap_file = f"{png_prefix}_robust_scaled_umap.csv"
robust_umap_data.to_csv(robust_umap_file)

# %%
# Plot UMAP clustering
for rank, sorted_labels in [("species", species_order),  ("genus", genus_order), ("family", family_order)]:
    umap_png_name = f"{png_prefix}_robust_scaled_umap_{rank}"
    sns.set(style="white")
    plot_clusters(robust_umap_data, "UMAP", rank, f"{umap_png_name}.png", sorted_labels)
    sns.set(style="white", font_scale=1.2)
    plot_clusters_by_abundance(robust_umap_data, "UMAP", rank, 20, umap_png_name, sorted_labels)

# %%
del robust_umap_data

# %% [markdown]
# ### Perform PCA clustering

# %%
# Perform UMAP clustering
robust_pca_data = perform_clustering("PCA", 2, np_robust_methylation_profile, species_labels, genus_labels, family_labels, seed=54321)
robust_pca_file = f"{png_prefix}_robust_scaled_pca.csv"
robust_pca_data.to_csv(robust_pca_file)

# %%
# Plot UMAP clustering
for rank, sorted_labels in [("species", species_order),  ("genus", genus_order), ("family", family_order)]:
    pca_png_name = f"{png_prefix}_robust_scaled_pca_{rank}"
    sns.set(style="white")
    plot_clusters(robust_pca_data, "PCA", rank, f"{pca_png_name}.png", sorted_labels)
    sns.set(style="white", font_scale=1.2)
    plot_clusters_by_abundance(robust_pca_data, "PCA", rank, 20, pca_png_name, sorted_labels)

# %%
del robust_pca_data
del np_robust_methylation_profile


# %% [markdown]
# ### Perform Standard scaling

# %%
# Scale the data using the RobustScaler
scaler = StandardScaler()
np_standard_methylation_profile = scaler.fit_transform(np_methylation_profile)

# %% [markdown]
# ### Perform UMAP clustering on scaled data

# %%
# Perform UMAP clustering
standard_umap_data = perform_clustering("UMAP", 2, np_standard_methylation_profile, species_labels, genus_labels, family_labels, seed=54321)
standard_umap_file = f"{png_prefix}_standard_scaled_umap.csv"
standard_umap_data.to_csv(standard_umap_file)


# %%
# Plot UMAP clustering
for rank, sorted_labels in [("species", species_order),  ("genus", genus_order), ("family", family_order)]:
    umap_png_name = f"{png_prefix}_standard_scaled_umap_{rank}"
    sns.set(style="white")
    plot_clusters(standard_umap_data, "UMAP", rank, f"{umap_png_name}.png", sorted_labels)
    sns.set(style="white", font_scale=1.2)
    plot_clusters_by_abundance(standard_umap_data, "UMAP", rank, 20, umap_png_name, sorted_labels)

# %%
del standard_umap_data

# %% [markdown]
# ### Perform PCA clustering

# %%
# Perform UMAP clustering
standard_pca_data = perform_clustering("PCA", 2, np_standard_methylation_profile, species_labels, genus_labels, family_labels, seed=54321)
standard_pca_file = f"{png_prefix}_standard_scaled_pca.csv"
standard_pca_data.to_csv(standard_pca_file)

# %%
# Plot UMAP clustering
for rank, sorted_labels in [("species", species_order),  ("genus", genus_order), ("family", family_order)]:
    pca_png_name = f"{png_prefix}_standard_scaled_pca_{rank}"
    sns.set(style="white")
    plot_clusters(standard_pca_data, "PCA", rank, f"{pca_png_name}.png", sorted_labels)
    sns.set(style="white", font_scale=1.2)
    plot_clusters_by_abundance(standard_pca_data, "PCA", rank, 20, pca_png_name, sorted_labels)

# %%
del standard_pca_data
del np_standard_methylation_profile


# %% [markdown]
# ### Perform Robust scaling

# %%
# Scale the data using the MinMaxScaler
scaler = MinMaxScaler(feature_range=(0, 1))
np_minmax_methylation_profile = scaler.fit_transform(np_methylation_profile)

# %% [markdown]
# ### Perform UMAP clustering on scaled data

# %%
# Perform UMAP clustering
minmax_umap_data = perform_clustering("UMAP", 2, np_minmax_methylation_profile, species_labels, genus_labels, family_labels, seed=54321)
minmax_umap_file = f"{png_prefix}_minmax_scaled_umap.csv"
minmax_umap_data.to_csv(minmax_umap_file)

# %%
# Plot UMAP clustering
for rank, sorted_labels in [("species", species_order),  ("genus", genus_order), ("family", family_order)]:
    umap_png_name = f"{png_prefix}_minmax_scaled_umap_{rank}"
    sns.set(style="white")
    plot_clusters(minmax_umap_data, "UMAP", rank, f"{umap_png_name}.png", sorted_labels)
    sns.set(style="white", font_scale=1.2)
    plot_clusters_by_abundance(minmax_umap_data, "UMAP", rank, 20, umap_png_name, sorted_labels)

# %%
del minmax_umap_data

# %% [markdown]
# ### Perform PCA clustering

# %%
# Perform UMAP clustering
minmax_pca_data = perform_clustering("PCA", 2, np_minmax_methylation_profile, species_labels, genus_labels, family_labels, seed=54321)
minmax_pca_file = f"{png_prefix}_minmax_scaled_pca.csv"
minmax_pca_data.to_csv(minmax_pca_file)

# %%
# Plot UMAP clustering
for rank, sorted_labels in [("species", species_order),  ("genus", genus_order), ("family", family_order)]:
    pca_png_name = f"{png_prefix}_minmax_scaled_pca_{rank}"
    sns.set(style="white")
    plot_clusters(minmax_pca_data, "PCA", rank, f"{pca_png_name}.png", sorted_labels)
    sns.set(style="white", font_scale=1.2)
    plot_clusters_by_abundance(minmax_pca_data, "PCA", rank, 20, pca_png_name, sorted_labels)

# %%
del minmax_pca_data
del np_minmax_methylation_profile