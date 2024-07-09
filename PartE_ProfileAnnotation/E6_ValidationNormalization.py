#!/usr/bin/env python3

# %% [markdown]
# # Normalize and filter the validation/application datasets (individually)

# %%
import sys
import polars as pl
import pickle

# %%
# Take a list of input files from sys.argv
tsv_annotated = sys.argv[1]
list_top50_species = sys.argv[2]
tsv_normalized_top50 = sys.argv[3]

# %%
# Load the annotated profile (validation / application sample) as polars dataframe
df_annotated = pl.read_csv(tsv_annotated, separator='\t', has_header=True)
print(f"Nr of reads in annotated profile: {df_annotated.shape[0]}")

# %%
# Load the top 50 species list
with open(list_top50_species, 'rb') as f:
    most_freq_species = pickle.load(f)


# %%
# Define the column types in the complete profile DataFrame
annotation_columns = pl.col("read_id", "species_id", "genus_id", "family_id", "sequencing_run", "read_length", "methylation_count")
profile_columns = pl.col("*").exclude("read_id", "taxonomic_id", "species_id", "genus_id", "family_id", "sequencing_run", "read_length", "methylation_count")


# %%
# Normalize the profile by read length
df_normalized = df_annotated.select(annotation_columns, profile_columns / pl.col("read_length")*1000)
df_normalized.head()


# %%
# Filter and save the normalzied dataframe
df_normalized_top50 = df_normalized.filter((pl.col("species_id").is_in(most_freq_species)))
df_normalized_top50.write_csv(tsv_normalized_top50, include_header=True, separator="\t")
print(f"Nr of reads in normalized top50 profile: {df_normalized_top50.shape[0]}")