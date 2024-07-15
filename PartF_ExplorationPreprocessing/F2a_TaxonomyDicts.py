#!/usr/bin/env python3

# %% [markdown]
# # Create id-name dictionaries for all species (and genera, families) in the data

import taxoniq
import pickle
import sys
import polars as pl
import pandas

tsv_complete_profile = sys.argv[1]
pickle_dictionaries = sys.argv[2]

# Load the complete profile .tsv file as polars DataFrame
df_complete_profile = pl.read_csv(tsv_complete_profile, separator='\t', has_header=True)

# %% [markdown]
# ### Create a dictionary to map taxon IDs to taxon names

# %%
# Species annotations (id to name dictionary)
species_dict = {}
unique_species = df_complete_profile.select(["species_id"]).unique().to_pandas()["species_id"]
for species in unique_species:
    tax = taxoniq.Taxon(species)
    name = tax.scientific_name
    species_dict[species] = name


# %%
# Genus annotations (id to name dictionary)
genus_dict = {}
unique_genus = df_complete_profile.select(["genus_id"]).unique().to_pandas()["genus_id"]
for genus in unique_genus:
    tax = taxoniq.Taxon(genus)
    name = tax.scientific_name
    genus_dict[genus] = name

# %%
# Family annotations (id to name dictionary)
family_dict = {}
unique_family = df_complete_profile.select(["family_id"]).unique().to_pandas()["family_id"]
for family in unique_family:
    tax = taxoniq.Taxon(family)
    name = tax.scientific_name
    family_dict[family] = name
    

# Save the dictionaries together to a file
with open(pickle_dictionaries, 'wb') as f:
    pickle.dump({'species_dict': species_dict, 'genus_dict': genus_dict, 'family_dict': family_dict}, f)
