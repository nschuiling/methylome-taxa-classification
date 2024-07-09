#!/usr/bin/env python3

# %% [markdown]
# # Merge 5mC and 6mA motif profiles

# %% [markdown]
# ### Prepare environment, input, and output files

# %%
# Load libraries
import sys
import polars as pl

# %%
# Define input files
tsv_methylated_profile_5mC = sys.argv[1]
tsv_methylated_profile_6mA = sys.argv[2]
# Define output file
tsv_methylated_profile_merged = sys.argv[3]

# %% [markdown]
# ### Load the methylation profiles

# %%
def load_profile(tsv_methylated_profile):
    """Function to load the motif counts profile into a polars DataFrame."""
    return pl.read_csv(tsv_methylated_profile, separator='\t', has_header=True)

# %%
# Load the profiles
df_methylated_profile_5mC = load_profile(tsv_methylated_profile_5mC)
df_methylated_profile_6mA = load_profile(tsv_methylated_profile_6mA)

# %%
df_methylated_profile_5mC.head()

# %%
df_methylated_profile_6mA.head()

# %% [markdown]
# ### Merge the methylation profiles

# %%
def merge_and_sum_profiles(df_5mC, df_6mA):
    """Function to merge two DataFrames by appending them and summing the values for overlapping read IDs."""
    
    # Append the DataFrames
    combined_df = pl.concat([df_5mC, df_6mA], how="vertical")
    # Group by 'read_id' and sum the values
    combined_df = combined_df.group_by("read_id", maintain_order=True).sum()
        
    return combined_df

# %%
# Create the combined profile
combined_profile_5mC_6mA = merge_and_sum_profiles(df_methylated_profile_5mC, df_methylated_profile_6mA)

# %%
combined_profile_5mC_6mA.head()


# %%
# Save the combined methylation profile
combined_profile_5mC_6mA.write_csv(tsv_methylated_profile_merged, include_header=True, separator="\t")
