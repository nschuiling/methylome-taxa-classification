#!/usr/bin/env python3

# %% [markdown]
# # Profile exploration plots

# %% [markdown]
# ### Prepare environment, input, and output files

# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import polars as pl
import numpy as np
import sys
import pickle

# %%
tsv_nreads = sys.argv[1]
tsv_complete_profile = sys.argv[2]
png_prefix = sys.argv[3]
pickle_taxon_dictionaries = sys.argv[4]


# %%
# Colorscheme info (color blind friendly!): https://packages.tesselle.org/khroma/articles/tol.html

one_color = "#6699CC"
color_per_sample = {
    "EL2W_ERR11004357": "#AA3377",  # Purple
    "WH1M_ERR11007628": "#66CCEE",  # Cyan
    "OM2_ERR11168802": "#228833",  # Green
    "ZYMO_ERR13034758": "#4477AA",  # Blue
    "HUMGUT_ERR13033930": "#EE6677",  # Red
}

# %% [markdown]
# ### Load the data

# %%
# Read the nreads TSV file into a pandas DataFrame
df_nreads = pd.read_csv(tsv_nreads, sep='\t')

# %% [markdown]
# # Load the dictionaries for mapping taxonomic id's to taxonomic names

# %%
# Load the dictionaries from the file
with open(pickle_taxon_dictionaries, 'rb') as f:
    taxon_dicts = pickle.load(f)
species_dict = taxon_dicts['species_dict']
genus_dict = taxon_dicts['genus_dict']
family_dict = taxon_dicts['family_dict']

# %%
# Load the complete profile .tsv file as polars DataFrame
df_complete_profile = pl.read_csv(tsv_complete_profile, separator='\t', has_header=True)

# %%
print("Total nr of reads: ", df_complete_profile.shape[0])
print("Nr of columns: ", df_complete_profile.shape[1])

# %%
# Define the column types in the complete profile DataFrame
annotation_columns = pl.col("read_id", "species_id", "genus_id", "family_id", "sequencing_run", "read_length", "methylation_count")
profile_columns = pl.col("*").exclude("read_id", "taxonomic_id", "species_id", "genus_id", "family_id", "sequencing_run", "read_length", "methylation_count")


# %% [markdown]
# ### Plot the number of reads at different stages of the analysis

# %%
# Melt the DataFrame for easier plotting with seaborn
df_nreads_melted = df_nreads.melt(id_vars=['run_name'],
                                  value_vars=['basecalled_reads', 'filtered_reads', 'profiled_reads', 'taxon_reads', 'species_reads', 'top50_reads'],
                                  var_name='analysis_stage', value_name='count')

# Define a name for the png
png_nreads = png_prefix + "_nreads_by_sample_and_stage.png"

# Prepare the sample-based color palette for plotting
palette = [color_per_sample[sample] for sample in df_nreads['run_name']]

# Create the bar plot
plt.figure(figsize=(20, 8))
sns.barplot(data=df_nreads_melted, x='analysis_stage', y='count', hue='run_name', palette=color_per_sample)
plt.xlabel(None)
plt.xticks(ticks=[0, 1, 2, 3, 4, 5], labels=['Base-called', 'QC-filtered', 'Methylation profiled', 'Taxonomically annotated', 'Annotated at the Species level', 'Part of the top 50 Species'])
plt.ylabel('Number of reads')
plt.legend(title='Sample name')
plt.savefig(png_nreads, bbox_inches='tight')
plt.show()

# %% [markdown]
# ### Plot the Species abundance in the data

# %%
def plot_abundances_samples(df_complete_profile, max_plot_taxa, rank, taxon_dict, png_taxon_counts_colored_by_sample):

    # Define the column to focus on
    rank_id_column = rank + "_id"

    # Calculate overall species counts and get the top nr_taxa
    total_taxon_counts = (
        df_complete_profile
        .group_by(rank_id_column)
        .agg(pl.len().alias('count'))
        .sort('count', descending=True)
        .head(max_plot_taxa)
    )

    # Filter the DataFrame to include only the top species
    plot_taxon_ids = total_taxon_counts[rank_id_column]
    max_plot_taxa = len(plot_taxon_ids)
    taxonomy_filtered_profile = df_complete_profile.filter(pl.col(rank_id_column).is_in(plot_taxon_ids))

    # Group by sequencing_run and taxonomic ID
    # Count the number of reads for each taxonomic ID
    taxon_counts_persample = (
        taxonomy_filtered_profile
        .group_by(['sequencing_run', rank_id_column])
        .agg(pl.len().alias('count'))
        .sort(['count', 'sequencing_run'], descending=True)
    )

    # Convert to pandas DataFrame for plotting
    taxon_counts_pd = taxon_counts_persample.to_pandas()
    # Ensure the order is by overall frequency
    taxon_counts_pd[rank_id_column] = pd.Categorical(taxon_counts_pd[rank_id_column], categories=plot_taxon_ids.to_list(), ordered=True)

    # Pivot the data to get sequencing_run as columns and rank_id_column as rows
    pivot_df = taxon_counts_pd.pivot(index=rank_id_column, columns='sequencing_run', values='count')
    # Fill NaN values with 0 for plotting
    pivot_df = pivot_df.fillna(0)

    # Define color per sequencing run
    sequencing_runs = pivot_df.columns
    colors = [color_per_sample[sample] for sample in sequencing_runs]

    # Define labels per taxon
    taxa = pivot_df.index
    taxa_labels = [taxon_dict[taxon] for taxon in taxa]

    # Plotting
    pivot_df.plot(kind='bar', stacked=True, figsize=(20, 10), color=colors)
    plt.yscale('log')
    plt.xlabel(f"{rank.title()} name")
    plt.xticks(ticks=range(len(taxa_labels)), labels = taxa_labels, rotation=90)
    plt.ylabel("Number of reads (log scale)")
    plt.title(f"Taxonomic distribution of the top {max_plot_taxa} most common {rank.title()}")
    plt.tight_layout()
    plt.savefig(png_taxon_counts_colored_by_sample, bbox_inches='tight')
    plt.show()

# %%
max_plot_taxa = 50
rank = "species"
rank_dict = species_dict
png_taxon_counts_colored_by_sample = png_prefix + "_top50_species_counts_colored_by_sample.png"
plot_abundances_samples(df_complete_profile, max_plot_taxa, rank, rank_dict, png_taxon_counts_colored_by_sample)

# %%
max_plot_taxa = 50
rank = "genus"
rank_dict = genus_dict
png_taxon_counts_colored_by_sample = png_prefix + "_top50_genus_counts_colored_by_sample.png"
plot_abundances_samples(df_complete_profile, max_plot_taxa, rank, rank_dict, png_taxon_counts_colored_by_sample)

# %%
max_plot_taxa = 50
rank = "family"
rank_dict = family_dict
png_taxon_counts_colored_by_sample = png_prefix + "_top50_family_counts_colored_by_sample.png"
plot_abundances_samples(df_complete_profile, max_plot_taxa, rank, rank_dict, png_taxon_counts_colored_by_sample)

# %%
def plot_abundances_samples(df_complete_profile, max_plot_taxa, rank, taxon_dict, png_taxon_counts_colored_by_sample):
    
    if rank == "species":
        x_cut_a = 500000
        x_cut_b = 800000
        x_max = 950000
    elif rank == "genus":
        x_cut_a = 500000
        x_cut_b = 800000
        x_max = 950000
    else:
        x_cut_a = 500000
        x_cut_b = 1000000
        x_max = 1800000
    
    # Define the column to focus on
    rank_id_column = rank + "_id"

    # Calculate overall species counts and get the top nr_taxa
    total_taxon_counts = (
        df_complete_profile
        .group_by(rank_id_column)
        .agg(pl.len().alias('count'))
        .sort('count', descending=False)
        .head(max_plot_taxa)
    )

    # Filter the DataFrame to include only the top species
    plot_taxon_ids = total_taxon_counts[rank_id_column]
    max_plot_taxa = len(plot_taxon_ids)
    taxonomy_filtered_profile = df_complete_profile.filter(pl.col(rank_id_column).is_in(plot_taxon_ids))

    # Group by sequencing_run and taxonomic ID
    # Count the number of reads for each taxonomic ID
    taxon_counts_persample = (
        taxonomy_filtered_profile
        .group_by(['sequencing_run', rank_id_column])
        .agg(pl.len().alias('count'))
        .sort(['count', 'sequencing_run'], descending=False)
    )

    # Convert to pandas DataFrame for plotting
    # %%
    # Convert to pandas DataFrame for plotting
    taxon_counts_pd = taxon_counts_persample.to_pandas()
    # Ensure the order is by overall frequency
    taxon_counts_pd[rank_id_column] = pd.Categorical(taxon_counts_pd[rank_id_column], categories=plot_taxon_ids.to_list(), ordered=True)

    # Pivot the data to get sequencing_run as columns and rank_id_column as rows
    pivot_df = taxon_counts_pd.pivot(index=rank_id_column, columns='sequencing_run', values='count')
    # Fill NaN values with 0 for plotting
    pivot_df = pivot_df.fillna(0)

    # Define color per sequencing run
    sequencing_runs = pivot_df.columns
    colors = [color_per_sample[sample] for sample in sequencing_runs]

    # Define labels per taxon
    taxa = pivot_df.index
    taxa_labels = [taxon_dict[taxon] for taxon in taxa]
    height = len(taxa_labels)//2.5

    # Plotting with broken x-axis
    fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True, figsize=(15, height), width_ratios=[5,1])
    fig.subplots_adjust(wspace=0.05)  # adjust space between axes

    # Plot the same data on both axes
    pivot_df.plot(kind='barh', stacked=True, ax=ax1, color=colors, legend=False)
    pivot_df.plot(kind='barh', stacked=True, ax=ax2, color=colors, legend=False)

    # Zoom in / limit the view to different portions of the data
    ax1.set_xlim(0, x_cut_a)  # most of the data
    ax2.set_xlim(x_cut_b, x_max)  # outliers only

    # Hide the spines between ax and ax2
    ax1.spines['right'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax1.yaxis.tick_left()
    ax2.yaxis.tick_right()
    ax2.tick_params(labelright=False)  # don't put tick labels at the right

    # Create diagonal lines at the break points
    d = .5  # proportion of vertical to horizontal extent of the slanted line
    kwargs = dict(marker=[(-d, -1), (d, 1)], markersize=12,
                  linestyle="none", color='k', mec='k', mew=1, clip_on=False)
    ax1.plot([1, 1], [0, 1], transform=ax1.transAxes, **kwargs)
    ax2.plot([0, 0], [0, 1], transform=ax2.transAxes, **kwargs)

    # Set labels and title
    ax1.set_ylabel(f"{rank.title()} name")
    ax1.set_yticks(range(len(taxa_labels)))
    ax1.set_yticklabels(taxa_labels)
    ax1.set_xlabel("Number of reads")

    # Save and show the plot
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(png_taxon_counts_colored_by_sample, bbox_inches='tight')
    plt.show()


# %%
max_plot_taxa = 50
rank = "species"
rank_dict = species_dict
png_taxon_counts_colored_by_sample = png_prefix + "_top50_species_counts_colored_by_sample_vertical.png"
plot_abundances_samples(df_complete_profile, max_plot_taxa, rank, rank_dict, png_taxon_counts_colored_by_sample)

# %%
max_plot_taxa = 50
rank = "genus"
rank_dict = genus_dict
png_taxon_counts_colored_by_sample = png_prefix + "_top50_genus_counts_colored_by_sample_vertical.png"
plot_abundances_samples(df_complete_profile, max_plot_taxa, rank, rank_dict, png_taxon_counts_colored_by_sample)

# %%
max_plot_taxa = 50
rank = "family"
rank_dict = family_dict
png_taxon_counts_colored_by_sample = png_prefix + "_top50_family_counts_colored_by_sample_vertical.png"
plot_abundances_samples(df_complete_profile, max_plot_taxa, rank, rank_dict, png_taxon_counts_colored_by_sample)

# %% [markdown]
# ### Plot the distribution of total motif occurrences

# %%
motif_sums = df_complete_profile.select(profile_columns).sum()
motif_sums = motif_sums.to_pandas()
print(motif_sums)

# %%
motifs_sorted = motif_sums.sort_values(by=0, axis='columns', ascending=False)
print(motifs_sorted)

# %%
# Plot the distribution of motif sums
png_motif_frequency_distribution = png_prefix + "_motif_frequency_distribution.png"
plt.figure(figsize=(20, 6))
sns.histplot(motif_sums.iloc[0], bins=100, color=one_color)
plt.yscale('log')
plt.ylabel('Frequency (log scale)')
plt.xlabel('Total motif occurrence over all reads and samples (including all motifs)')
plt.savefig(png_motif_frequency_distribution, bbox_inches='tight')
plt.show()

# %%
motifs_sorted.iloc[0,0:-1000]

# %%
# Plot the distribution of motif sums, excluding the 10% most frequent motifs
png_motif_frequency_distribution_excl10 = png_prefix + "_motif_frequency_distribution_excluding10%mostfreq.png"
plt.figure(figsize=(20, 6))
sns.histplot(motifs_sorted.iloc[0,418:], bins=300, color=one_color)
plt.yscale('log')
plt.ylabel('Frequency (log scale)')
plt.xlabel('Total motif occurrence over all reads and samples (excluding the 10% most frequent motifs)')
plt.savefig(png_motif_frequency_distribution_excl10, bbox_inches='tight')
plt.show()

# %% [markdown]
# ### Basic statistics on motif occurrences

# %%
# Calculate some basic statistics of the motif sums, e.g. mean, median, etc.
print("Summary statistics of total motif occurrences: ")
print(motif_sums.iloc[0].describe())


# %% [markdown]
# ### Plot the least/most/median frequent motifs

# %%
def plot_motifs_with_frequencies(motifs_sorted, n_motifs, freq, png_frequent_motifs):

    # Select the top n_motifs most frequent motifs
    if freq == "most":
        selected_motifs = motifs_sorted.iloc[0,:n_motifs]
        fig_width = 6
    elif freq == "least":
        selected_motifs = motifs_sorted.iloc[0,-n_motifs:]
        fig_width = 6
    elif freq == "median":
        middle_index = len(motifs_sorted.iloc[0]) // 2
        lower_index = middle_index - n_motifs // 2
        upper_index = middle_index + n_motifs // 2
        selected_motifs = motifs_sorted.iloc[0, middle_index - n_motifs // 2 : middle_index + n_motifs // 2]
        fig_width = 6
    else:
        print("Invalid frequency. Please choose 'most', 'least' or 'median'.")

    # Plot the top n_motifs most frequent motifs
    plt.figure(figsize=(fig_width, 8))
    sns.barplot(x=selected_motifs.values, y=selected_motifs.index, color=one_color)
    plt.xlabel('Frequency')
    plt.ylabel('Motif')
    plt.savefig(png_frequent_motifs, bbox_inches='tight')
    plt.show()

# %%
png_frequent_motifs = png_prefix + "_20motifs_with_frequencies_most_frequent.png"
plot_motifs_with_frequencies(motifs_sorted, 20, "most", png_frequent_motifs)

# %%
png_frequent_motifs = png_prefix + "_20motifs_with_frequencies_median_frequent.png"
plot_motifs_with_frequencies(motifs_sorted, 20, "median", png_frequent_motifs)

# %%
png_frequent_motifs = png_prefix + "_20motifs_with_frequencies_least_frequent.png"
plot_motifs_with_frequencies(motifs_sorted, 20, "least", png_frequent_motifs)

# %% [markdown]
# ### Plot the distribution of taxonomic frequencies

# %%
def plot_taxonomic_frequency_distribution(df_complete_profile, taxonomy, png_taxa_frequency_distribution):

    # Select the taxonomic column
    taxonomic_column = taxonomy + "_id"
    
    # Count the number of unique taxonomies
    num_taxon = df_complete_profile.select(taxonomic_column).unique().shape[0]
    print(f'Number of {taxonomy}: {num_taxon}')

    # Calculate the frequency of each species
    taxon_counts = df_complete_profile.select(taxonomic_column).to_series().value_counts()
    taxon_counts = taxon_counts.to_pandas()

    # Plot the distribution of species frequencies
    plt.figure(figsize=(10, 6))
    sns.histplot(taxon_counts['count'], bins=num_taxon, color=one_color)
    plt.yscale('log')
    plt.ylabel('Frequency (log scale)')
    plt.xlabel(f'Total {taxonomy.title()} occurrence over all reads and samples')
    plt.savefig(png_taxa_frequency_distribution, bbox_inches='tight')
    plt.show()


# %%
png_taxa_frequency_distribution = png_prefix + "_species_frequency_distribution.png"
plot_taxonomic_frequency_distribution(df_complete_profile, "species", png_taxa_frequency_distribution)

# %%
png_taxa_frequency_distribution = png_prefix + "_genus_frequency_distribution.png"
plot_taxonomic_frequency_distribution(df_complete_profile, "genus", png_taxa_frequency_distribution)

# %%
png_taxa_frequency_distribution = png_prefix + "_family_frequency_distribution.png"
plot_taxonomic_frequency_distribution(df_complete_profile, "family", png_taxa_frequency_distribution)

# %% [markdown]
# ### Read statistics and distributions

# %%
per_read_statistics_columns = pl.col("read_length",
                                     "methylation_count", "normalized_methylation_count",
                                     "n_unique_motifs", "normalized_n_unique_motifs",
                                     "average_n_unique_motifs_per_methylated_site")

# %%
# Add normalized methylation counts
df_profile_w_stats = df_complete_profile.with_columns(
    normalized_methylation_count=pl.col("methylation_count")/pl.col("read_length")*1000)

# Add nr of unique motifs per read
n_unique_motifs_per_read = df_complete_profile.select(
    profile_columns).transpose().select(pl.all()!=0).sum().transpose()["column_0"].alias("n_unique_motifs")
df_profile_w_stats = df_profile_w_stats.with_columns(n_unique_motifs_per_read)

# Add normalized nr of unique motifs per read
df_profile_w_stats = df_profile_w_stats.with_columns(
    normalized_n_unique_motifs=pl.col("n_unique_motifs")/pl.col("read_length")*1000)

# Average nr of motifs per methylated sites
df_profile_w_stats = df_profile_w_stats.with_columns(
    average_n_unique_motifs_per_methylated_site=pl.col("n_unique_motifs")/pl.col("methylation_count"))

# %%
descr_stats_table = df_profile_w_stats.select(per_read_statistics_columns).describe()
print(descr_stats_table)

# %%
# Plot the distribution of:
# Read length
png_read_lengths = png_prefix + "_read_lengths.png"
plt.figure(figsize=(8, 6))
sns.histplot(data=df_profile_w_stats, x="read_length", color=one_color, log_scale=True)
plt.ylabel('Frequency')
plt.xlabel(f'Read length (number of bases per read)')
plt.savefig(png_read_lengths, bbox_inches='tight')
plt.show()

# %%
# Plot the distribution of:
# Methylation counts
png_methylation_counts = png_prefix + "_methylation_counts.png"
plt.figure(figsize=(8, 6))
sns.histplot(data=df_profile_w_stats, x="methylation_count", color=one_color, log_scale=True)
plt.ylabel('Frequency')
plt.xlabel(f'Number of methylated sites per read')
plt.savefig(png_methylation_counts, bbox_inches='tight')
plt.show()

# %%
# Plot the distribution of:
# Normalized methylation counts
png_normalized_methylation_counts = png_prefix + "_normalized_methylation_counts.png"
plt.figure(figsize=(8, 6))
sns.histplot(data=df_profile_w_stats, x="normalized_methylation_count", color=one_color) #, log_scale=True)
plt.ylabel('Frequency')
plt.xlabel(f'Number of methylated sites per 1000 bases per read')
plt.savefig(png_normalized_methylation_counts, bbox_inches='tight')
plt.show()

# %%
# Plot the distribution of:
# Nr of unique motifs per read
png_n_unique_motifs = png_prefix + "_n_unique_motifs.png"
plt.figure(figsize=(8, 6))
sns.histplot(data=df_profile_w_stats, x="n_unique_motifs", color=one_color) #, log_scale=True)
plt.ylabel('Frequency')
plt.xlabel(f'Number of unique motifs per read')
plt.savefig(png_n_unique_motifs, bbox_inches='tight')
plt.show()

# %%
# Plot the distribution of:
# Nr of unique motifs added per 1000 bases per read
png_normalized_n_unique_motifs = png_prefix + "_normalized_n_unique_motifs.png"
plt.figure(figsize=(8, 6))
sns.histplot(data=df_profile_w_stats, x="normalized_n_unique_motifs", color=one_color) #, log_scale=True)
plt.ylabel('Frequency')
plt.xlabel(f'Number of unique motifs added per 1000 bases per read')
plt.savefig(png_normalized_n_unique_motifs, bbox_inches='tight')
plt.show()

# %%
# Plot the distribution of:
# Nr of unique motifs added per 1000 bases per read
png_average_n_unique_motifs_per_methylated_site = png_prefix + "_average_n_unique_motifs_per_methylated_site.png"
plt.figure(figsize=(8, 6))
sns.histplot(data=df_profile_w_stats, x="average_n_unique_motifs_per_methylated_site", color=one_color) #, log_scale=True)
plt.ylabel('Frequency')
plt.xlabel(f'Number of unique motifs added for each methylated site')
plt.savefig(png_average_n_unique_motifs_per_methylated_site, bbox_inches='tight')
plt.show()

# %% [markdown]
# ### Motif statistics

# %%
per_motif_statistics_columns = pl.col("median_norm_motif_occurrence",
                                      "mean_norm_motif_occurrence",
                                      "min_norm_motif_occurrence",
                                      "max_norm_motif_occurrence")

# %%
df_profile_w_motif_stats = df_complete_profile.select(profile_columns).transpose()

# %%
median = df_profile_w_motif_stats.transpose().median().transpose()["column_0"].alias("median_norm_motif_occurrence")
mean = df_profile_w_motif_stats.transpose().mean().transpose()["column_0"].alias("mean_norm_motif_occurrence")
min = df_profile_w_motif_stats.transpose().min().transpose()["column_0"].alias("min_norm_motif_occurrence")
max = df_profile_w_motif_stats.transpose().max().transpose()["column_0"].alias("max_norm_motif_occurrence")

# %%
df_profile_w_motif_stats = df_profile_w_motif_stats.with_columns(median, mean, min, max)

# %%
descr_stats_table_motifs = df_profile_w_motif_stats.select(per_motif_statistics_columns).describe()
print(descr_stats_table_motifs)


