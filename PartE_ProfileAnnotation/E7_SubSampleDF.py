#!/usr/bin/env python3

# Load libraries
import sys
import polars as pl

# Define file names
tsv_fulldata = sys.argv[1]
tsv_subsetdata = sys.argv[2]

# Load data
df_fulldata = pl.read_csv(tsv_fulldata, separator='\t', has_header=True)

# Create a subset with only 1000000 reads
df_subsetdata = df_fulldata.sample(n=1000000, seed=54321)
del df_fulldata

# Save the subset
df_subsetdata.write_csv(tsv_subsetdata, include_header=True, separator="\t")
