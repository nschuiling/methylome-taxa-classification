#!/usr/bin/env python3

# %% [markdown]
# # Taxonomic exploration and rank completion (version in which ALL reads are kept)

# %% [markdown]
# ### Prepare environment, input, and output files

# %%
import sys
import polars as pl
import taxoniq
import numpy as np

# %%
# Define input and output files
tsv_taxonomic_ids = sys.argv[1]
tsv_all_ranks = sys.argv[2]

# %%
# Load the input TSV file into a pandas DataFrame
df_taxonomic_ids = pl.read_csv(tsv_taxonomic_ids, separator='\t', has_header=True)
df_taxonomic_ids.head()

# %% [markdown]
# ### Ensure Species, Genus, Family level annotations

# %%
# Keep only the reads for which an annotation at species, genus, or family level is available
df_FGS_ranks = df_taxonomic_ids.filter(pl.col("taxonomic_rank").is_in(["S", "G", "F"]))
df_other_ranks = df_taxonomic_ids.filter(~pl.col("taxonomic_rank").is_in(["S", "G", "F"]))
del df_taxonomic_ids

# %%
df_FGS_ranks

# %% [markdown]
# ### Fill in Family and Genus id's for all reads annotated at Species level

# %%
# Extract the reads annotated at Species level
df_S_rank = df_FGS_ranks.filter(pl.col("taxonomic_rank") == "S")
df_S_rank

# %%
# Identify all unique species
unique_species = df_S_rank.unique("taxonomic_id")
unique_species = list(unique_species["taxonomic_id"])
print("Nr of unique species at species annotation level: ", len(unique_species))
print("Unique species: ", unique_species)

# %%
species_genus_map = {}
species_family_map = {}
for species_id in unique_species:
    try:
        species = taxoniq.Taxon(species_id)
        ranks = {t.rank.name:t.tax_id for t in species.ranked_lineage}
        species_id, genus_id, family_id = ranks['species'], ranks['genus'], ranks['family']
        species_genus_map[species_id] = genus_id
        species_family_map[species_id] = family_id
    except Exception as e:
        print(f"Error processing species taxonomic_id {species_id}: {e}")
        species_genus_map[species_id], species_family_map[species_id] = None, None

print("Species-genus map: ", species_genus_map)
print("Species-family map: ", species_family_map)

# %%
df_S_rank = df_S_rank.with_columns(species_id=pl.col("taxonomic_id"))
df_S_rank = df_S_rank.with_columns(genus_id=pl.col("species_id").replace(species_genus_map),
                                   family_id=pl.col("species_id").replace(species_family_map))
df_S_rank

# %% [markdown]
# ### Fill in Family id's for all reads annotated at Genus level

# %%
# Extract the reads annotated at Species level
df_G_rank = df_FGS_ranks.filter(pl.col("taxonomic_rank") == "G")
df_G_rank

# %%
# Identify all unique species
unique_genus = df_G_rank.unique("taxonomic_id")
unique_genus = list(unique_genus["taxonomic_id"])
print("Nr of unique genus at genus annotation level: ", len(unique_genus))
print("Unique genus: ", unique_genus)

# %%
genus_family_map = {}
for genus_id in unique_genus:
    try:
        genus = taxoniq.Taxon(genus_id)
        ranks = {t.rank.name:t.tax_id for t in genus.ranked_lineage}
        genus_id, family_id = ranks['genus'], ranks['family']
        genus_family_map[genus_id] = family_id
    except Exception as e:
        print(f"Error processing genus taxonomic_id {genus_id}: {e}")
        genus_family_map[genus_id] = None
        
print("Genus-family map: ", genus_family_map)

# %%
df_G_rank = df_G_rank.with_columns(species_id=None,
                                   genus_id=pl.col("taxonomic_id"))
df_G_rank = df_G_rank.with_columns(family_id=pl.col("genus_id").replace(genus_family_map))
df_G_rank

# %% [markdown]
# ### Fill in id's for all reads annotated at Family level

# %%
# Extract the reads annotated at Family level
df_F_rank = df_FGS_ranks.filter(pl.col("taxonomic_rank") == "F")
df_F_rank

# %%
df_F_rank = df_F_rank.with_columns(species_id=None,
                                   genus_id=None,
                                   family_id=pl.col("taxonomic_id"))
df_F_rank

# OTHER ranks
df_other_ranks = df_other_ranks.with_columns(species_id=None,
                                   genus_id=None,
                                   family_id=None)

# %% [markdown]
# ### Combine the dataframes back into one dataframe

# %%
# Merge the dataframes
del df_FGS_ranks
df_all_ranks = pl.concat([df_S_rank, df_G_rank, df_F_rank, df_other_ranks])
df_all_ranks

# %%
df_all_ranks = df_all_ranks.select(pl.all().exclude("taxonomic_rank"))
#df_FGS_ranks = df_all_ranks.filter(pl.col("family_id").is_not_null())
df_all_ranks

# %%
# Save the dataframe to a TSV file
df_all_ranks.write_csv(tsv_all_ranks, include_header=True, separator="\t")
print(f"Output saved to {tsv_all_ranks}")