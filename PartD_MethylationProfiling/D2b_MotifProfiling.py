#!/usr/bin/env python3

# %% [markdown]
# # Create counts matrix from motif-integer occurrences

# %% [markdown]
# ### Prepare environment, input, and output files

# %%
# Import libraries
import sys
import numpy as np
import ast
import csv
csv.field_size_limit(10000000)

# %%
## Input
methylated_integers_file = sys.argv[1]
motif_dictionary_file = sys.argv[2]
## Output
methylated_profile_file = sys.argv[3]

# %% [markdown]
# ### Load the integer-motif mapping

# %%
# Load the dictionary to map integers back to motifs
with open(motif_dictionary_file, 'r') as input:
    motif_dictionary = ast.literal_eval(input.read())

# %%
motif_dictionary

# %% [markdown]
# ### Create a profile of motif counts based on motif occurrences

# %%
def create_motif_profile(methylated_integers_file, motif_dictionary, unique_motifs, methylated_profile_file):
    """Function to create a motif count matrix using numpy arrays for efficiency."""
    
    # Create a map from motifs to their indices for faster access
    motif_index_map = {motif: index for index, motif in enumerate(unique_motifs)}
    num_motifs = len(unique_motifs)
    
    with open(methylated_profile_file, 'w') as output:
        # Write the header
        columns = ['read_id', 'methylation_count'] + unique_motifs
        output.write("\t".join(columns) + "\n")
        
        # Read the input file
        with open(methylated_integers_file, 'r') as input:
            reader = csv.reader(input, delimiter='\t')
            next(reader)  # Skip the header
            
            for row in reader:
                read_id, methylation_count, motif_integers_str = row
                methylation_count = int(methylation_count)
                motif_integers = ast.literal_eval(motif_integers_str)
                
                # Initialize a numpy array for motif counts
                motif_counts = np.zeros(num_motifs, dtype=int)
                
                for motif_integer in motif_integers:
                    for motif in motif_dictionary.get(motif_integer, []):
                        motif_counts[motif_index_map[motif]] += 1
                
                # Convert numpy array to string and write the row to the output file
                counts_str = "\t".join(map(str, motif_counts))
                output.write(f"{read_id}\t{methylation_count}\t{counts_str}\n")

# %%
# Load motif dictionary and compute unique motifs (columns of the profile)
unique_motifs = sorted(set(motif for motifs in motif_dictionary.values() for motif in motifs))

# %%
print("Nr of unique motifs (columns): ", len(unique_motifs))

# %%
# Create a profile of counts per motif per read
create_motif_profile(methylated_integers_file, motif_dictionary, unique_motifs, methylated_profile_file)


