#!/usr/bin/env python3

# %% [markdown]
# # Combine the complete profiles from different samples

# %%
import sys
import polars as pl
import pickle

# %%
# Take a list of input files from sys.argv
tsv_all_samples_combined = sys.argv[1]
tsv_normalized_data = sys.argv[2]
tsv_normalized_top50 = sys.argv[3]
tsv_combined_profile_top50 = sys.argv[4]
list_top50_species = sys.argv[5]
list_all_motifs = sys.argv[6]
input_files = sys.argv[7:]

# %%
# Loop over the files, load them as polars dataframes, and append each below the other
df_all_samples = pl.DataFrame()
for file in input_files:
    print("File: ", file)
    df_one_sample = pl.read_csv(file, separator='\t', has_header=True)
    print("Shape of this sample's df: ", df_one_sample.shape)
    df_all_samples = pl.concat([df_all_samples, df_one_sample])

print("Some rows from the final combined profile: ")
print(df_all_samples)
print("Shape of all samples' df: ", df_all_samples.shape)


# %%
# Save the combined data
df_all_samples.write_csv(tsv_all_samples_combined, separator='\t', include_header=True)


# %%
# Also save a normalized version of the profile
# Define the column types in the complete profile DataFrame
annotation_columns = pl.col("read_id", "species_id", "genus_id", "family_id", "sequencing_run", "read_length", "methylation_count")
profile_columns = pl.col("*").exclude("read_id", "taxonomic_id", "species_id", "genus_id", "family_id", "sequencing_run", "read_length", "methylation_count")
# Normalize the profile by read length
df_normalized = df_all_samples.select(annotation_columns, profile_columns / pl.col("read_length")*1000)
df_normalized.head()

df_normalized.write_csv(tsv_normalized_data, separator='\t', include_header=True)

# %%
# Create a version with only the top 50 most common species for both dataframes

# Analyse only the top 100 species
nr_taxa = 50

# Calculate overall species counts and get the top nr_taxa
overall_species_counts = (
    df_all_samples
    .group_by("species_id")
    .agg(pl.len().alias('count'))
    .sort('count', descending=True)
    .head(nr_taxa)
)

# Show the counts of the most frequent species
most_freq_species = overall_species_counts[0:nr_taxa, "species_id"]
most_freq_species = list(most_freq_species)
print(most_freq_species)


# %%
# Filter and save the normalzied dataframe
df_normalized_top50 = df_normalized.filter((pl.col("species_id").is_in(most_freq_species)))
df_normalized_top50.write_csv(tsv_normalized_top50, include_header=True, separator="\t")
del df_normalized_top50
del df_normalized

# Filter and save the non-normalized dataframe
df_combined_profile_top50 = df_all_samples.filter((pl.col("species_id").is_in(most_freq_species)))
df_combined_profile_top50.write_csv(tsv_combined_profile_top50, include_header=True, separator="\t")


# %%
# Save lists of the top50 species ids and all the motifs (in order) for later usage
# Top 50 species
with open(list_top50_species, 'wb') as f:
    pickle.dump(most_freq_species, f)

# All motifs
motif_list = list(df_combined_profile_top50.select(profile_columns).columns)
with open(list_all_motifs, 'wb') as f:
    pickle.dump(motif_list, f)
