#!/usr/bin/env python3

# %% [markdown]
# # Profile Taxonomic Annotation

# %% [markdown]
# ### Prepare environment, input, and output files

# %%
# Set-up environment
import sys
import polars as pl

# %%
# Define input and output files
tsv_methylation_profile = sys.argv[1]
tsv_taxonomy = sys.argv[2]
tsv_read_lengths = sys.argv[3]
tsv_annotated = sys.argv[4]
run_name = sys.argv[5]

# %% [markdown]
# ### Load data (use Polars for efficiency)

# %%
# Load the methylation profile .tsv file as polars DataFrame
df_methylation_profile = pl.read_csv(tsv_methylation_profile, separator='\t', has_header=True)
df_methylation_profile.head()

# %%
# Load the read taxonomies as polars Dataframe
df_taxonomy = pl.read_csv(tsv_taxonomy, separator='\t')
df_taxonomy = df_taxonomy.with_columns(sequencing_run=pl.lit(run_name))
# For the analysis we only want to keep the reads with annotation at species level
# We can also run analyses at genus/family level, but we want to use the same reads
df_taxonomy = df_taxonomy.filter(pl.col("species_id").is_not_null())
print("Nr of reads with an annotation at species level: ", len(df_taxonomy))
print(df_taxonomy.head())

# %%
# Load the read lengths as Polars dataframe
df_read_lengths = pl.read_csv(tsv_read_lengths, separator='\t')
print(df_read_lengths.head())

# %% [markdown]
# ### Merge dataframes (use Polars for efficiency)

# %%
# Join the dataframes by their read_id
# Each read now has all analysis information associated with it
df_annotated = df_taxonomy.join(df_read_lengths, on="read_id").join(df_methylation_profile, on="read_id")
print(df_annotated.head())

# %%
# Check whether there are any reads without taxonomic id, read length, or profile
# There should not be any
print("Nr of reads in the final df without taxonomic_id: ", df_annotated['taxonomic_id'].null_count())
print("Nr of reads in the final df without read_length: ", df_annotated['read_length'].null_count())
print("Nr of reads in the final df without methylation_count: ", df_annotated['methylation_count'].null_count())

# %% [markdown]
# ### Save the annotated file

# %%
df_annotated.write_csv(tsv_annotated, include_header=True, separator="\t")
