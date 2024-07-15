#!/usr/bin/env python3

# %% [markdown]
# # Combine the application dataframes (profiles with annotations) with the taxonomic predictions made on them, to prepare for evaluation

# %%
import sys
import polars as pl
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report

# %% [markdown]
# ### Define input files

# %%
tsv_application_profiles = sys.argv[1]
tsv_mge_probabilities = sys.argv[2]
tsv_arg_hits = sys.argv[3]
pickle_taxon_dictionaries = sys.argv[4]
tsv_plasmids_or_args = sys.argv[5]
npy_predictions_folder = sys.argv[6]
npy_predictions_suffix = sys.argv[7]

# %%
npy_RF_genus_predictions = f"{npy_predictions_folder}/random_forest_genus_ypred{npy_predictions_suffix}"
npy_RF_species_predictions = f"{npy_predictions_folder}/random_forest_species_ypred{npy_predictions_suffix}"
npy_SVM_genus_predictions = f"{npy_predictions_folder}/svc_linear_genus_ypred{npy_predictions_suffix}"
npy_SVM_species_predictions = f"{npy_predictions_folder}/svc_linear_species_ypred{npy_predictions_suffix}"

# %% [markdown]
# ### Load the profile and annotation data

# %%
df_application_profiles = pl.read_csv(tsv_application_profiles, separator='\t', has_header=True)
print(df_application_profiles.shape)
print(df_application_profiles.head())


# %%
# Load the MGE annotations as Polars dataframe
if tsv_mge_probabilities != "none":
    df_mge_probabilities = pl.read_csv(tsv_mge_probabilities, separator='\t', has_header=False)
    df_mge_probabilities.columns = ["read_id", "mge_score"]
    print(df_mge_probabilities.head())
    
    # %%
    # Load the ARG annotations as Polars dataframe
    df_arg_hits = pl.read_csv(tsv_arg_hits, separator=' ', has_header=False)
    df_arg_hits.columns = ["read_id", "arg_gene"]
    print(df_arg_hits.head())
    
    # Join the dataframes by their read_id
    # Each read now has all analysis information associated with it
    df_application_profiles = df_application_profiles.join(df_arg_hits, on="read_id", how="left").join(df_mge_probabilities, on="read_id", how="left")
    print(df_application_profiles.head())
    
    #df_application_profiles


# %%
# Define the column types in the complete profile DataFrame
annotation_columns = pl.col("read_id", "species_id", "genus_id", "family_id", "sequencing_run", "read_length", "methylation_count", "mge_score", "arg_gene")
profile_columns = pl.col("*").exclude("read_id", "species_id", "genus_id", "family_id", "sequencing_run", "read_length", "methylation_count", "mge_score", "arg_gene")
prediction_columns = pl.col("RF_genus_pred", "RF_species_pred", "SVM_species_pred", "SVM_genus_pred")


# Optimize the data types of the raw data to reduce memory usage
df_application_profiles = df_application_profiles.select(annotation_columns, profile_columns.cast(pl.Float32))


# %% [markdown]
# ### Load dictionaries to map taxonomic ids to names

# %%
# Load the dictionaries from the file
with open(pickle_taxon_dictionaries, 'rb') as f:
    taxon_dicts = pickle.load(f)
species_dict = taxon_dicts['species_dict']
genus_dict = taxon_dicts['genus_dict']
family_dict = taxon_dicts['family_dict']

# %% [markdown]
# ### Predictions

# %%
RF_species_predictions = np.load(npy_RF_species_predictions)
RF_genus_predictions = np.load(npy_RF_genus_predictions)
SVM_species_predictions = np.load(npy_SVM_species_predictions)
SVM_genus_predictions = np.load(npy_SVM_genus_predictions)

# %%
# Add the npy dataframes as columns
df_application_profiles = df_application_profiles.with_columns(RF_species_pred=RF_species_predictions, RF_genus_pred=RF_genus_predictions,
                                                               SVM_species_pred=SVM_species_predictions, SVM_genus_pred=SVM_genus_predictions)
print(df_application_profiles)

# %%
df_application_profiles = df_application_profiles.with_columns(species_id = pl.col("species_id").replace(species_dict),
                                     genus_id = pl.col("genus_id").replace(genus_dict),
                                     family_id = pl.col("family_id").replace(family_dict),
                                     RF_genus_pred = pl.col("RF_genus_pred").replace(genus_dict),
                                     RF_species_pred = pl.col("RF_species_pred").replace(species_dict),
                                     SVM_species_pred = pl.col("SVM_species_pred").replace(species_dict),
                                     SVM_genus_pred = pl.col("SVM_genus_pred").replace(genus_dict))

# %%
df_application_profiles

# %% [markdown]
# ### Keep only the reads with a plasmid or ARG annotation

# %%
df_plasmids_or_args = df_application_profiles.filter((pl.col("arg_gene").is_not_null()) | (pl.col("mge_score") > 0.9))
print(df_plasmids_or_args.shape)
print(df_plasmids_or_args.head())

# %%
df_plasmids_or_args.write_csv(tsv_plasmids_or_args, include_header=True, separator="\t")
