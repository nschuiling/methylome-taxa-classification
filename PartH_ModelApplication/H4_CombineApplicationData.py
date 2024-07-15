#!/usr/bin/env python3

# %% [markdown]
# # Script to combine the complete profiles from different application samples into one "application dataset"

# %%
import sys
import polars as pl
import pickle
import numpy as np

# %%
# Output combined profile
tsv_combined = sys.argv[1]
# Output numpy profile
numpy_profile = sys.argv[2]
# Input files
input_files = sys.argv[3:]
#input_files = sys.argv[3]   # In case of just one validation sample


# %%
# Loop over the files, load them as polars dataframes, and append each below the other
df_all_samples = pl.DataFrame()
for file in input_files:
    print("File: ", file)
    df_one_sample = pl.read_csv(file, separator='\t', has_header=True)
    print("Shape of this sample's df: ", df_one_sample.shape)
    df_all_samples = pl.concat([df_all_samples, df_one_sample])
# For just the one validation sample nr 8 (comment the above away)
#df_all_samples = pl.read_csv(input_files, separator='\t', has_header=True)

print("Some rows from the final combined profile: ")
print(df_all_samples)
print("Shape of all samples df: ", df_all_samples.shape)
df_all_samples.write_csv(tsv_combined, separator='\t', include_header=True)


# %% 
# Create numpy dataframes for application in model
profile_columns = pl.col("*").exclude("read_id", "taxonomic_id", "species_id", "genus_id", "family_id", "sequencing_run", "read_length", "methylation_count", "mge_score", "arg_gene")
X = df_all_samples.select(profile_columns).to_numpy()


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