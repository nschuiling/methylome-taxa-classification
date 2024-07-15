#!/usr/bin/env python3

# %% [markdown]
# # Classifier Test Set Evaluation Plots

# %%
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve
import numpy as np
import pickle
import sys


# %%
rank = sys.argv[1]               # 'species' or 'genus'
classifier = sys.argv[2]       # 'svc_linear' or 'random_forest'
test_performance_folder = sys.argv[3] 
holdout_folder = sys.argv[4] 
independent_folder = sys.argv[5] 
pickle_taxon_dictionaries = sys.argv[6] 
output_folder = sys.argv[7] 



# Taxon true labels: holdout test set
y_true_holdout_file = f"{holdout_folder}/Top50NormalizedProfile_ytest_{rank}.npy"
# Taxon true labels: independent test set
y_true_independent_file = f"{independent_folder}/ZYMOMOCK_DBL_y_{rank}.npy"

# Input: Predictions and evaluation results
y_pred_holdout_file = f"{test_performance_folder}/{classifier}_{rank}_ypred_holdout.npy"
y_pred_independent_file = f"{test_performance_folder}/{classifier}_{rank}_ypred_independent.npy"
json_evaluation_output_holdout = f"{test_performance_folder}/{classifier}_{rank}_evaluation_holdout.json"
json_evaluation_output_independent = f"{test_performance_folder}/{classifier}_{rank}_evaluation_independent.json"

# Output;: Folder to save the output figures to
output_folder_prefix = f"{output_folder}/{classifier}_{rank}"


# %% [markdown]
# ### Load the taxon true labels and predictions

# %%
# Load the holdout labels and predictions
y_true_holdout = np.load(y_true_holdout_file)
y_pred_holdout = np.load(y_pred_holdout_file)

# Load the independent labels and predictions
y_true_independent = np.load(y_true_independent_file)
y_pred_independent = np.load(y_pred_independent_file)

# %% [markdown]
# ### Load the evaluation scores

# %%
def load_json_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

# %%
def parse_json_data(data):

    # Load the overall evaluation scores
    overall_scores = data['overall_scores']

    # Load the per-class evaluation scores
    per_class_scores = data['per_class_scores']
    per_class_scores.pop("accuracy", None)
    per_class_scores.pop("weighted avg", None)
    per_class_scores.pop('macro avg', None)
    
    # Format the overall scores in a dataframe
    overall_scores_flat = {'metric': [], 'score': []}
    for metric, score in overall_scores.items():
        overall_scores_flat['metric'].append(metric)
        overall_scores_flat['score'].append(score)
    overall_df = pd.DataFrame(overall_scores_flat)
    
    # Format the per-class scores in a dataframe
    per_class_scores_flat = {'class': [], 'metric': [], 'score': []}
    for class_id, metrics in per_class_scores.items():
        for metric, score in metrics.items():
            per_class_scores_flat['class'].append(class_id)
            per_class_scores_flat['metric'].append(metric)
            per_class_scores_flat['score'].append(score)
    per_class_df = pd.DataFrame(per_class_scores_flat)
    
    return overall_df, per_class_df

# %%
# Load the evaluation results for the holdout test set
holdout_evaluation = load_json_data(json_evaluation_output_holdout)
df_overall_scores_holdout, df_per_class_scores_holdout = parse_json_data(holdout_evaluation)

# %%
print(df_overall_scores_holdout)

# %%
# Load the evaluation results for the holdout test set
independent_evaluation = load_json_data(json_evaluation_output_independent)
df_overall_scores_independent, df_per_class_scores_independent = parse_json_data(independent_evaluation)

# %%
print(df_overall_scores_independent)

# %% [markdown]
# ### Use the dictionaries to map taxon id's to names

# %%
# Load the dictionaries from the file
with open(pickle_taxon_dictionaries, 'rb') as f:
    taxon_dicts = pickle.load(f)
species_dict = taxon_dicts['species_dict']
genus_dict = taxon_dicts['genus_dict']
family_dict = taxon_dicts['family_dict']

# Species and genus level models were trained
if rank == "species":
    rank_dict = species_dict
elif rank == "genus":
    rank_dict = genus_dict

# %%
def add_taxonomic_labels(data, species_dict, genus_dict, family_dict):
    
    # Change the labels to the string versions (instead of ids)
    # It add labels based on the ranks present in the data (in this case only one)
    data.loc[:,"class"] = data.loc[:,"class"].apply(int)
    data.loc[:,"class"] = data.loc[:,"class"].map(species_dict).fillna(data["class"])
    data.loc[:,"class"] = data.loc[:,"class"].map(genus_dict).fillna(data["class"])
    data.loc[:,"class"] = data.loc[:,"class"].map(family_dict).fillna(data["class"])

    return data

# %%
df_per_class_scores_holdout = add_taxonomic_labels(df_per_class_scores_holdout, species_dict, genus_dict, family_dict)

# %%
df_per_class_scores_independent = add_taxonomic_labels(df_per_class_scores_independent, species_dict, genus_dict, family_dict)

# %%
#list(df_per_class_scores_holdout["class"].unique())
', '.join(map(str, list(df_per_class_scores_holdout["class"].unique())))

# %% [markdown]
# ### Plot per-class precision, with the nr of reads present in the test set

# %%
from matplotlib.lines import Line2D

def precision_numreads_plot(precision, support, png_file):

    fig_width = len(precision['class'].unique())/3
    # Create a figure and a set of subplots
    fig, ax1 = plt.subplots(figsize=(fig_width, 3.5))

    # Plot the bar plot with hue using Seaborn
    sns.barplot(x=precision['class'], y=precision['score'], color="#7AB", data=precision, ax=ax1) #, color="light_blue")

    # Set the labels for the first y-axis
    ax1.set_ylabel('Precision')
    ax1.set_xlabel(f'{rank.capitalize()}')
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=90)

    # Create a secondary y-axis
    ax2 = ax1.twinx()

    # Plot the number of reads on the secondary y-axis
    sns.barplot(x=precision['class'], y=support["score"], color="black", data=precision, ax=ax2, width=0.3)

    # Set the labels for the secondary y-axis
    ax2.set_ylabel('Number of reads in test set')

    # Plot the legend
    precision_legend = Line2D([0], [0], color="#7AB", lw=4, label="Precision")
    reads_legend = Line2D([0], [0], color="black", lw=4, label="Number of reads in test set")
    ax1.legend(handles=[precision_legend, reads_legend], loc='upper right')

    plt.savefig(png_file, bbox_inches='tight')

    # Show the plot
    plt.show()

# %%
precision_holdout = df_per_class_scores_holdout[(df_per_class_scores_holdout["metric"]=="precision")].reset_index(drop=True).sort_values(by="score", ascending=False)
support_holdout = df_per_class_scores_holdout[(df_per_class_scores_holdout["metric"] == "support")].reset_index(drop=True)

png_file = f"{output_folder_prefix}_precision_numreads_holdout.png"
precision_numreads_plot(precision_holdout, support_holdout, png_file)

# %%
precision_independent = df_per_class_scores_independent[(df_per_class_scores_independent["metric"]=="precision")].reset_index(drop=True).sort_values(by="score", ascending=False)
support_independent = df_per_class_scores_independent[(df_per_class_scores_independent["metric"] == "support")].reset_index(drop=True)
png_file = f"{output_folder_prefix}_precision_numreads_independent.png"
precision_numreads_plot(precision_independent, support_independent, png_file)

# %%
# To calculate the mean for all non-0 precisions
precision_independent[(precision_independent["score"] != 0)]["score"].mean()

# %% [markdown]
# ### Plot a confusion matrix

# %%
from matplotlib.colors import LogNorm, Normalize

def plot_confusion_matrix(y_true, y_pred, label_mapping, scored_classes, png_file):

    # Map the labels to their names
    y_true_mapped = [label_mapping[label] for label in y_true]
    y_pred_mapped = [label_mapping[label] for label in y_pred]
    
    true_classes = [c for c in scored_classes if c in y_true_mapped]

    # Create a figure
    figure_width = len(scored_classes)/2
    figure_height = len(true_classes)/2 * 0.8
    cm = confusion_matrix(y_true_mapped, y_pred_mapped, labels=scored_classes)
    cm = cm[~np.all(cm == 0, axis=1)]
    plt.figure(figsize=(figure_width, figure_height))
    sns.heatmap(cm, xticklabels=scored_classes, yticklabels=true_classes, cmap="gray_r", annot_kws={"fontsize":7},
                annot=True, fmt='d', norm=LogNorm(), linewidths=0.5, linecolor="#7AB", clip_on=False, square=True) # cbar_kws={"aspect":80}, )
    plt.ylabel(f'True {rank}')
    plt.xlabel(f'Predicted {rank}')
    plt.savefig(png_file, bbox_inches='tight')
    plt.show()


# %%
y_true_holdout_list = y_true_holdout.flatten().tolist()
y_pred_holdout_list = y_pred_holdout.flatten().tolist()
ordered_classes = precision_holdout["class"].unique()

png_file = f"{output_folder_prefix}_confusion_matrix_holdout.png"
true_classes = [c for c in ordered_classes if c in y_true_holdout_list]
plot_confusion_matrix(y_true_holdout_list, y_pred_holdout_list, rank_dict, ordered_classes, png_file)

# %%
y_true_independent_list = y_true_independent.flatten().tolist()
y_pred_independent_list = y_pred_independent.flatten().tolist()
ordered_classes = precision_independent["class"].unique()

png_file = f"{output_folder_prefix}_confusion_matrix_independent.png"
plot_confusion_matrix(y_true_independent_list, y_pred_independent_list, rank_dict, ordered_classes, png_file)

# %% [markdown]
# ### Create per-class tables for in Overleaf/Latex

# %%
df_per_class_scores_holdout["score"] = df_per_class_scores_holdout["score"].round(3)
df_per_class_scores_independent["score"] = df_per_class_scores_independent["score"].round(3)

# %%
def latex_table(pd_df):
    # Pivot the DataFrame
    pivot_df = pd_df.pivot(index='class', columns='metric', values='score')

    # Sort the columns to the desired order
    pivot_df = pivot_df[['precision', 'recall', 'f1-score', 'support']]
    pivot_df = pivot_df.sort_values("precision", ascending=False)

    # Fill NaN with placeholder or zeros
    pivot_df = pivot_df.fillna('NaN')

    # Function to format the row
    def format_row(row):
        return f"{row.name} & {row['precision']} & {row['recall']} & {row['f1-score']} & {int(row['support']) if row['support'] != 'NaN' else 'NaN'}\\\\"

    # Generate the formatted table
    C = [format_row(row) for _, row in pivot_df.iterrows()]
    #formatted_rows = ' & '.join(formatted_rows) + '\\\\'


    return '\n'.join(C)

# %%
print(latex_table(df_per_class_scores_holdout))

# %%
print(latex_table(df_per_class_scores_independent))


