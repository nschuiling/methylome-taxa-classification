#!/usr/bin/env python3

# %% [markdown]
# # Obtain Numpy representations for validation and appliccation datasets

# %% [markdown]
# ### Prepare environment, input, and output files

# %%
# Set-up environment
import sys
import polars as pl
import numpy as np

# %%
# Set seed for reproducability
seed = 54

# %%
# Input settings and file names
tsv_profile_data = sys.argv[1]
output_folder_and_prefix = sys.argv[2]

# %%
# Output file names
# X (data)
X_file = output_folder_and_prefix + "_X.npy"

# y (labels), for the different rank levels
y_file_species = output_folder_and_prefix + "_y_species.npy"
y_file_genus = output_folder_and_prefix + "_y_genus.npy"
y_file_family = output_folder_and_prefix + "_y_family.npy"


# %% [markdown]
# ### Load the data (use Polars for efficiency)

# %%
# Load the data using polars for efficiency
df_profile_data = pl.read_csv(tsv_profile_data, separator='\t', has_header=True)

# %%
# Define the column types in the complete profile DataFrame
annotation_columns = pl.col("read_id", "species_id", "genus_id", "family_id", "sequencing_run", "read_length", "methylation_count")
string_annotation_columns = pl.col("read_id", "sequencing_run")
integer_annotation_columns = pl.col("species_id", "genus_id", "family_id", "read_length", "methylation_count")
profile_columns = pl.col("*").exclude("read_id", "taxonomic_id", "species_id", "genus_id", "family_id", "sequencing_run", "read_length", "methylation_count")

# %%
# Show the structure of the raw data
print(f"Raw dataframe (normalized counts of the top 50 species: \n {df_profile_data}")

# %% [markdown]
# ### Reduce memory consumption of the data (polars dataframe)

# %%
# Check the memory usage of the raw profile
print(f"Memory consumption of the raw dataframe: {df_profile_data.estimated_size(unit='mb')} mb")

# %%
# Determine the minimum and maximum value in the dataframe (to set the optimal datatype)
min_data = df_profile_data.select(profile_columns.min()).min_horizontal()[0]
max_data = df_profile_data.select(profile_columns.max()).max_horizontal()[0]
print(f"Minimum and maximum values in the methylation profile: {min_data} and {max_data}")

# %%
# Determine the minimum and maximum value in the annotation columns (to set the optimal datatype)
min_data = df_profile_data.select(integer_annotation_columns.min()).min_horizontal()[0]
max_data = df_profile_data.select(integer_annotation_columns.max()).max_horizontal()[0]
print(f"Minimum and maximum values in the annotation (integer) columns: {min_data} and {max_data}")

# %%
# Optimize the data types of the raw data to reduce memory usage
df_profile_data = df_profile_data.select(string_annotation_columns, profile_columns.cast(pl.Float32), integer_annotation_columns.cast(pl.UInt32))

# %%
# Check the memory usage of the modified profile
print(f"Memory consumption of the modified dataframe: {df_profile_data.estimated_size(unit='mb')} mb")

# %%
# Show the structure of the modified data
print(f"Modified dataframe: \n {df_profile_data}")

# %% [markdown]
# ### Define the X and y data in numpy and ensure correct (least memory) data types

# %%
# Define the X and y data from the dataframe
X = df_profile_data.select(profile_columns).to_numpy()
y_species = df_profile_data.select("species_id").to_numpy()
y_genus = df_profile_data.select("genus_id").to_numpy()
y_family = df_profile_data.select("family_id").to_numpy()

# %%
# Check and improve the memory consuption of the methylation profile (X)
# If the polars conversion already happened, the type should already be float32 and nothing changes
print(f"Memory consumption of the numpy methylation profile (X): {X.nbytes/1000000} mb")
X = X.astype('float32')  
print(f"Memory consumption of the modified numpy methylation profile (X): {X.nbytes/1000000} mb")

# %%
# Show the data (X and y)
print(f"Numpy representation of the species labels (y): {y_species}")
print(f"Numpy representation of the methylation profile (X): {X}")

# %%
del df_profile_data


# %% [markdown]
# ### Save the numpy data representations

# %%
# X
np.save(X_file, X)
print(f"Saved the data (X) to file: {X_file}.")

# y
np.save(y_file_species, y_species)
np.save(y_file_genus, y_genus)
np.save(y_file_family, y_family)
print(f"Saved the labels (y) to files: {y_file_species}, {y_file_genus}, and {y_file_family}")


# %% [markdown]
# ### Number of reads in data

# %%
# Nr of reads (will be the same at all ranks)
print("Nr of reads:", len(y_species))
