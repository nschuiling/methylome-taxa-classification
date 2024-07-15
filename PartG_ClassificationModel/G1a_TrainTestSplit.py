#!/usr/bin/env python3

# %% [markdown]
# # Train-Test split ("model building dataset", Table 1 in thesis)

# %% [markdown]
# ### Prepare environment, input, and output files

# %%
# Set-up environment
import sys
import polars as pl
import numpy as np
from sklearn.model_selection import train_test_split

# %%
# Set seed for reproducability
seed = 54

# %%
# Input settings and file names
tsv_profile_data = sys.argv[1]
output_folder_and_prefix = sys.argv[2]

# %%
# Output file names
# X (data) training and test
X_train_file = output_folder_and_prefix + "_Xtrain.npy"
X_test_file = output_folder_and_prefix + "_Xtest.npy"

# y (labels) training sets, for the different rank levels
y_train_file_species = output_folder_and_prefix + "_ytrain_species.npy"
y_train_file_genus = output_folder_and_prefix + "_ytrain_genus.npy"
y_train_file_family = output_folder_and_prefix + "_ytrain_family.npy"

# y (labels) test sets, for the different rank levels
y_test_file_species = output_folder_and_prefix + "_ytest_species.npy"
y_test_file_genus = output_folder_and_prefix + "_ytest_genus.npy"
y_test_file_family = output_folder_and_prefix + "_ytest_family.npy"

# file to save the full profile incl. annotationss of the test set to
tsv_test_set_df = output_folder_and_prefix + "_test_profile.tsv"

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
#del df_profile_data

# %% [markdown]
# ### Perform train-test split

# %%
# Split the data into stratified train (95%) and test (5%) sets
# The same split will be used, but the labels will be assigned at different taxonomic ranks
X_train, X_test, y_train_species, y_test_species = train_test_split(X, y_species, test_size=0.05, stratify=y_species, random_state=seed)
X_train, X_test, y_train_genus, y_test_genus = train_test_split(X, y_genus, test_size=0.05, stratify=y_species, random_state=seed)
X_train, X_test, y_train_family, y_test_family = train_test_split(X, y_family, test_size=0.05, stratify=y_species, random_state=seed)


# ADDED LATER, BUT NOT (successfully) USED]# The test dataset profile (polars version) will later be saved based on the indexes of the train-test split
# New lines to add before the train-test split
#df_profile_data = df_profile_data.with_columns(pl.Series("row_idx", np.arange(df_profile_data.shape[0])))
#X_train, X_test, idx_train, idx_test = train_test_split(
#    X, np.arange(len(y_species)), test_size=0.05, stratify=y_species, random_state=seed)
# Obtain test set version of dataframe
# New line to create the test set version of the original dataframe
#df_test_set = df_profile_data.filter(pl.col("row_idx").is_in(idx_test))
#df_test_set = df_profile_data[idx_test]
# Drop the row index column as it's no longer needed
#df_test_set = df_test_set.drop("row_idx")
# New line to save the test set version of the original dataframe
#df_test_set.write_csv(tsv_test_set_df, include_header=True, separator="\t")
#print(f"Saved the test set version of the original dataframe to file: {tsv_test_set_df}")


# %%
# Clean to free up memory
del X
del y_species
del y_genus
del y_family

# %% [markdown]
# ### Save the training, validation, and test data

# %%
# X train and test
np.save(X_train_file, X_train)
np.save(X_test_file, X_test)
print(f"Saved the data (X) to files: {X_train_file}, {X_test_file}")

# y train
np.save(y_train_file_species, y_train_species)
np.save(y_train_file_genus, y_train_genus)
np.save(y_train_file_family, y_train_family)
print(f"Saved the training labels (y) to files: {y_train_file_species}, {y_train_file_genus}, and {y_train_file_family}")

# y test
np.save(y_test_file_species, y_test_species)
np.save(y_test_file_genus, y_test_genus)
np.save(y_test_file_family, y_test_family)
print(f"Saved the test labels (y) to files: {y_test_file_species}, {y_test_file_genus}, and {y_test_file_family}")


# %% [markdown]
# ### Number of reads in training and test sets

# %%
# Nr of train reads (will be the same at all ranks)
print("Nr of train reads:", len(y_train_species))
# Nr of test reads (will be the same at all ranks)
print("Nr of test reads:", len(y_test_species))
