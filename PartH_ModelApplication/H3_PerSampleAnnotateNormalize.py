#!/usr/bin/env python3

# %% [markdown]
# # Combine the complete profiles from different application samples

# %%
import sys
import polars as pl
import pickle
import numpy as np

# %%
# Input files from sys.argv
run_name = sys.argv[1]
tsv_methylation_profile = sys.argv[2]
tsv_taxonomy = sys.argv[3]
tsv_read_lengths = sys.argv[4]
tsv_mge_probabilities = sys.argv[5]
tsv_arg_hits = sys.argv[6]
# Output files from sys.argv
tsv_complete = sys.argv[7]
numpy_profile = sys.argv[8]


# Set seed for reproducability
seed = 54


# %% [markdown]
# ### Load data (use Polars for efficiency)

# %%
# Load the methylation profile .tsv file as polars DataFrame
df_methylation_profile = pl.read_csv(tsv_methylation_profile, separator='\t', has_header=True)


# %%
# Load the read taxonomies as polars Dataframe
df_taxonomy = pl.read_csv(tsv_taxonomy, separator='\t', has_header=True)
# Add a column with the sequencing run name
df_taxonomy = df_taxonomy.with_columns(sequencing_run=pl.lit(run_name))
print(df_taxonomy.head())


# %%
# Load the read lengths as Polars dataframe
df_read_lengths = pl.read_csv(tsv_read_lengths, separator='\t', has_header=True)
print(df_read_lengths.head())


# %%
# Load the MGE annotations as Polars dataframe
df_mge_probabilities = pl.read_csv(tsv_mge_probabilities, separator='\t', has_header=False)
df_mge_probabilities.columns = ["read_id", "mge_score"]
print(df_mge_probabilities.head())


# %%
# Load the ARG annotations as Polars dataframe
df_arg_hits = pl.read_csv(tsv_arg_hits, separator=' ', has_header=False)
df_arg_hits.columns = ["read_id", "arg_gene"]
print(df_arg_hits.head())


# %% [markdown]
# ### Merge dataframes (use Polars for efficiency)

# %%
# Join the dataframes by their read_id
# Each read now has all analysis information associated with it
df_annotated = df_taxonomy.join(df_read_lengths, on="read_id").join(
    df_arg_hits, on="read_id", how="left").join(df_mge_probabilities, on="read_id", how="left").join(df_methylation_profile, on="read_id")


# %%
# Check whether there are any reads without taxonomic id, read length, or profile
# There should not be any
print("Nr of reads in the final df without taxonomic_id: ", df_annotated['taxonomic_id'].null_count())
print("Nr of reads in the final df without read_length: ", df_annotated['read_length'].null_count())
print("Nr of reads in the final df without methylation_count: ", df_annotated['methylation_count'].null_count())


# %%
# Normalize the methylation profiles by read length
# Define the column types in the complete profile DataFrame
annotation_columns = pl.col("read_id", "species_id", "genus_id", "family_id", "sequencing_run", "read_length", "methylation_count", "mge_score", "arg_gene")
profile_columns = pl.col("*").exclude("read_id", "taxonomic_id", "species_id", "genus_id", "family_id", "sequencing_run", "read_length", "methylation_count", "mge_score", "arg_gene")
# Normalize the profile by read length
df_normalized = df_annotated.select(annotation_columns, profile_columns / pl.col("read_length")*1000)
df_normalized.head()
# Save the profile
df_normalized.write_csv(tsv_complete, separator='\t', include_header=True)


# %% 
# Create numpy dataframes for application in model
X = df_normalized.select(profile_columns).to_numpy()


# %%
# Check and improve the memory consuption of the methylation profile (X)
# If the polars conversion already happened, the type should already be float32 and nothing changes
print(f"Memory consumption of the numpy methylation profile (X): {X.nbytes/1000000} mb")
X = X.astype('float32')  
print(f"Memory consumption of the modified numpy methylation profile (X): {X.nbytes/1000000} mb")

# %%
# Show the data (X)
print(f"Numpy representation of the methylation profile (X): {X}")


# %% [markdown]
# ### Save the numpy data representation
np.save(numpy_profile, X)
print(f"Saved the data (X) to file: {numpy_profile}.")


# %% [markdown]
# ### Number of reads in data

# %%
# Nr of reads (will be the same at all ranks)
print("Nr of reads:", len(X))


###  OPTIONAL: ADD AN ANNOTATION WHETHER THE ANNOTATION CAME FROM THE TOP 50 SPECIES

# Load the top 50 species list (on which the model was trained)
#with open(list_top50_species, 'rb') as f:
#    most_freq_species = pickle.load(f)

# %%
# Create a version with only the top 50 most common species (on which the model was trained)

# Filter and save the normalzied dataframe
#df_normalized_top50 = df_normalized.filter((pl.col("species_id").is_in(most_freq_species)))
#df_normalized_top50.write_csv(tsv_normalized_top50, include_header=True, separator="\t")
#print(f"Nr of reads in normalized top50 profile: {df_normalized_top50.shape[0]}")
