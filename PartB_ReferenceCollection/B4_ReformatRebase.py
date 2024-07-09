#!/usr/bin/env python3

import re
import sys

# Define the input and output files
input_file = sys.argv[1]
output_file_5C = sys.argv[2]
output_file_6A = sys.argv[3]

# Define a function to parse the downloaded REABSE motifs file
# Extract motifs by type (5mC vs 6mA) and length
def extract_motifs(input_file, meth_type, min_length):
    motifs = []
    with open(input_file, 'r') as file:
        content = file.read()
        # Identify all entries (motifs), which are split by a double new line in the file
        entries = re.split(r'\n\n', content)
        for entry in entries:
            if f'<meth_type>{meth_type}' in entry:
                
                # For each motif, extract the sequence and the methylated base position
                rec_seq = re.search(r'<rec_seq>([^<]+)', entry)
                meth_base = re.search(r'<meth_base>([^<]+)', entry)
                if rec_seq and meth_base:
                    motif = rec_seq.group(1).strip()
                    base = meth_base.group(1).strip()
                    
                    # Save motifs with a length above the minimum
                    if len(motif) >= min_length and base.isdigit():
                        # Subtract 1 to get indexes starting at 0 instead of 1
                        base = int(base) - 1
                        motifs.append((motif, base))
    return motifs

# Extract 6mA motifs and write to a TSV file
motifs_6A = extract_motifs(input_file, '6', 4)
with open(output_file_6A, 'w') as file:
    file.write("motif\tmeth_position\n")
    for motif, base in motifs_6A:
        file.write(f"{motif}\t{base}\n")
print(f"Unique 6A-methylation recognition sequences with length >= 4bp extracted from REBASE to: {output_file_6A}.")

# Extract 5mC motifs and write to a TSV file
motifs_5C = extract_motifs(input_file, '5', 4)
with open(output_file_5C, 'w') as file:
    file.write("motif\tmeth_position\n")
    for motif, base in motifs_5C:
        file.write(f"{motif}\t{base}\n")
print(f"Unique 5C-methylation recognition sequences with length >= 4bp extracted from REBASE to: {output_file_5C}.")
