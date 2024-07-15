#!/usr/bin/env python3

# %% [markdown]
# # Classifier Performance Comparisons Plots and Evaluations (aggregate and per-class)

# %%
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import numpy as np
import pickle
import sys


# %%
# Input files
json_directory = sys.argv[1]
png_prefix = sys.argv[2]
pickle_taxon_dictionaries = sys.argv[3]

# Classifiers and ranks to evaluate (included in input files)
ranks = ['species', 'genus', 'family']
classifiers = ['random_model', 'naivebayes', 'knn', 'svc_linear', 'random_forest']
# Initially also tried: ['mlp', 'elastic_net', 'svc_nonlinear']

# %%
# Load the dictionaries from the file
with open(pickle_taxon_dictionaries, 'rb') as f:
    taxon_dicts = pickle.load(f)
species_dict = taxon_dicts['species_dict']
genus_dict = taxon_dicts['genus_dict']
family_dict = taxon_dicts['family_dict']

# %% [markdown]
# ### Load the scores from the JSON file

# %%
def load_json_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

# %%
def parse_json_data(data):

    # Load the overall evaluation scores
    overall_scores = data[0]['overall_scores']

    # Load the per-class evaluation scores
    per_class_scores = data[0]['per_class_scores']
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
def aggregate_scores(files):
    overall_scores_list = []
    per_class_scores_list = []
    
    for i, file in enumerate(files):
        data = load_json_data(file)
        overall_df, per_class_df = parse_json_data(data)
        overall_df["repetition"], per_class_df["repetition"] = i, i
        overall_scores_list.append(overall_df)
        per_class_scores_list.append(per_class_df)
    
    overall_combined = pd.concat(overall_scores_list)
    per_class_combined = pd.concat(per_class_scores_list)
    
    return overall_combined, per_class_combined

# %%
def process_files(directory, classifiers, ranks):
    # Define lists to combine all data for all classifiers and ranks

    overall_agg_ranks_combined_list = []
    per_class_agg_ranks_combined_list = []
    
    for classifier in classifiers:
        
        overall_agg_list = []
        per_class_agg_list = []
        for rank in ranks:
            files = glob.glob(os.path.join(directory, f"./{rank}/{classifier}/{classifier}_{rank}_*.json"))
            overall_agg, per_class_agg = aggregate_scores(files)
            overall_agg["rank"], overall_agg["classifier"] = rank, classifier
            per_class_agg["rank"], per_class_agg["classifier"] = rank, classifier

            overall_agg_list.append(overall_agg)
            per_class_agg_list.append(per_class_agg)
        
        overall_agg_ranks_combined = pd.concat(overall_agg_list)
        per_class_agg_ranks_combined = pd.concat(per_class_agg_list)
        
        overall_agg_ranks_combined_list.append(overall_agg_ranks_combined)
        per_class_agg_ranks_combined_list.append(per_class_agg_ranks_combined)
    
    overall_agg_ranks_classifiers_combined = pd.concat(overall_agg_ranks_combined_list)
    per_class_agg_ranks_classifiers_combined = pd.concat(per_class_agg_ranks_combined_list)

    return overall_agg_ranks_classifiers_combined, per_class_agg_ranks_classifiers_combined

# %%
overall_agg_ranks_classifiers_combined, per_class_agg_ranks_classifiers_combined = process_files(json_directory, classifiers, ranks)

# %%
overall_agg_ranks_classifiers_combined

# %%
per_class_agg_ranks_classifiers_combined

# %% [markdown]
# ### Map taxonomic id's to taxonomic labels

# %%
def add_taxonomic_labels(data, species_dict, genus_dict, family_dict):
    
    # Change the labels to the string versions (instead of ids)
    data.loc[:,"class"] = data.loc[:,"class"].apply(int)
    data.loc[:,"class"] = data.loc[:,"class"].map(species_dict).fillna(data["class"])
    data.loc[:,"class"] = data.loc[:,"class"].map(genus_dict).fillna(data["class"])
    data.loc[:,"class"] = data.loc[:,"class"].map(family_dict).fillna(data["class"])

    return data

# %%
per_class_agg_ranks_classifiers_combined = add_taxonomic_labels(per_class_agg_ranks_classifiers_combined, species_dict, genus_dict, family_dict)

# %%
per_class_agg_ranks_classifiers_combined

# %% [markdown]
# ### Create tables with aggregate scores (means and stds)

# %%
overall_mean_std = overall_agg_ranks_classifiers_combined.drop(['repetition'], axis=1).groupby(
    ['metric', 'rank', 'classifier']).agg(['mean', 'std']).reset_index()

# %%
def create_overall_table(overall_mean_std, metric, rank):
    table = overall_mean_std[(overall_mean_std["metric"]==metric) &
                               (overall_mean_std["rank"] == rank)]
    # sort rows by mean
    table = table.sort_values(by=('score', 'mean'), ascending=True).reset_index(drop=True)
    return table

# %%
create_overall_table(overall_mean_std, "recall_macro", "genus")

# %%
def create_overall_table(overall_mean_std, metrics, rank):
    tables = []
    
    # Filter and sort the data for each metric
    for metric in metrics:
        table = overall_mean_std[(overall_mean_std["metric"] == metric) & 
                                 (overall_mean_std["rank"] == rank)]
        
        table = table.sort_values(by=('score', 'mean'), ascending=True).reset_index(drop=True)
        table.columns = [col[0] if col[1] == '' else f'{col[1]}' for col in table.columns]
        
        # Combine mean and std into a single cell
        table[f"{metric}"] = table.apply(lambda row: f"{row['mean']:.3f} ({row['std']:.3f})", axis=1)
        
        # Keep only necessary columns
        table = table[["classifier", f"{metric}"]]
        tables.append(table)
    
    # Merge all tables on the classifier column
    final_table = tables[0]
    for t in tables[1:]:
        final_table = pd.merge(final_table, t, on="classifier")
    
    # Rename classifier column
    final_table.rename(columns={"classifier": "Classifier type"}, inplace=True)
    
    return final_table

# %%
# Metrics to choose from
overall_mean_std["metric"].unique()

# %%
# Create the table
metrics = ['precision_macro', 'recall_macro', 'f1_macro', 'accuracy', 'balanced_accuracy']
rank = "species"  # "species", "genus", "family"
table = create_overall_table(overall_mean_std, metrics, rank)
table
#print(table)

# %%
# Create the table
metrics = ['precision_macro', 'recall_macro', 'f1_macro', 'accuracy', 'balanced_accuracy']
rank = "genus"  # "species", "genus", "family"
table = create_overall_table(overall_mean_std, metrics, rank)
table
#print(table)

# %%
# Create the table
metrics = ['precision_macro', 'recall_macro', 'f1_macro', 'accuracy', 'balanced_accuracy']
rank = "family"  # "species", "genus", "family"
table = create_overall_table(overall_mean_std, metrics, rank)
table
#print(table)

# %% [markdown]
# ### Create a Latex formatted table

# %%
metrics = ['precision_macro', 'recall_macro', 'f1_macro', 'accuracy', 'balanced_accuracy']
rank = "species"  # "species", "genus", "family"
table = create_overall_table(overall_mean_std, metrics, rank)

# Mapping for classifier types to their formatted names
classifier_mapping = {
    'random_model': 'Random model',
    'naivebayes': 'Naive Bayes',
    'knn': 'K-nearest neighbours',
    'svc_linear': 'Linear SVM',
    'random_forest': 'Random forest'
}

# Function to format the row
def format_row(row):
    classifier_name = classifier_mapping[row['Classifier type']]
    formatted_values = [classifier_name]
    for col in table.columns[1:]:
        value, std = row[col].split(' ')
        formatted_value = f"{value} {std}"
        formatted_values.append(formatted_value)
    return ' & '.join(formatted_values) + '\\\\'

# Generate the formatted table
formatted_table = [format_row(row) for _, row in table.iterrows()]

# Print the formatted table
formatted_table_str = '\n'.join(formatted_table)
print(formatted_table_str)

# %% [markdown]
# ### Create per-class performance tables

# %%
per_class_mean_std = per_class_agg_ranks_classifiers_combined.drop(['repetition'], axis=1).groupby(
    ['metric', 'rank', 'classifier', 'class']).agg(['mean', 'std']).reset_index()

# %%
def create_per_class_table(per_class_mean_std, metric, classifier, rank):
    table = per_class_mean_std[(per_class_mean_std["metric"]==metric) &
                               (per_class_mean_std["classifier"]==classifier) & 
                               (per_class_mean_std["rank"] == rank)]
    return table
    

# %%
create_per_class_table(per_class_mean_std, "precision", "random_forest", "species")

# %% [markdown]
# ### Create boxplots per metric: comparing all ranks and classifiers
# 

# %%
# About colors: https://packages.tesselle.org/khroma/articles/tol.html
color_per_rank = {
    "species": "#004488",
    "genus": "#BB5566",
    "family": "#DDAA33"
}
ranks_palette=["#004488", "#BB5566", "#DDAA33"]

# %%
def boxplot_one_metric_all_ranks_and_classifiers(data, metric, png_prefix):

    png_name = f"{png_prefix}_boxplot_all_ranks_all_classifiers_{metric}.png"

    data = data[(data["metric"]==metric)]
    plt.figure(figsize=(7, 4))
    sns.boxplot(data, x="classifier", y="score", hue="rank", palette=ranks_palette)
    

    plt.xlabel("Classifier")
    plt.ylabel(f"{metric.capitalize().replace('_', ' ')}")
    
    plt.legend(loc='upper left', title="Taxonomic rank", frameon=True)

    plt.ylim([0, 1])
    plt.tight_layout()
    plt.savefig(png_name, bbox_inches='tight')
    plt.close()

# %%
boxplot_one_metric_all_ranks_and_classifiers(overall_agg_ranks_classifiers_combined, "precision_macro", png_prefix)

# %%
boxplot_one_metric_all_ranks_and_classifiers(overall_agg_ranks_classifiers_combined, "recall_macro", png_prefix)

# %%
boxplot_one_metric_all_ranks_and_classifiers(overall_agg_ranks_classifiers_combined, "f1_macro", png_prefix)

# %%
boxplot_one_metric_all_ranks_and_classifiers(overall_agg_ranks_classifiers_combined, "accuracy", png_prefix)

# %%
boxplot_one_metric_all_ranks_and_classifiers(overall_agg_ranks_classifiers_combined, "balanced_accuracy", png_prefix)

# %% [markdown]
# ### Create boxplots per metric, per classifier: comparing all classes

# %%
# Calculate the median score for each class and sort
precision_sorted_species = list(per_class_agg_ranks_classifiers_combined[
    (per_class_agg_ranks_classifiers_combined["metric"] == "precision") &
    (per_class_agg_ranks_classifiers_combined["rank"] == "species")
    ].groupby('class')['score'].median().sort_values(ascending=False).index)

# %%
# Calculate the median score for each class and sort
precision_sorted_genus = list(per_class_agg_ranks_classifiers_combined[
    (per_class_agg_ranks_classifiers_combined["metric"] == "precision") &
    (per_class_agg_ranks_classifiers_combined["rank"] == "genus")
    ].groupby('class')['score'].median().sort_values(ascending=False).index)

# %%
# Calculate the median score for each class and sort
precision_sorted_family = list(per_class_agg_ranks_classifiers_combined[
    (per_class_agg_ranks_classifiers_combined["metric"] == "precision") &
    (per_class_agg_ranks_classifiers_combined["rank"] == "family")
    ].groupby('class')['score'].median().sort_values(ascending=False).index)

# %%
def boxplot_one_metric_one_classifier_per_class(data, metric, classifier, rank, png_prefix, sorted_classes=None):
    
    png_name = f"{png_prefix}_boxplot_per_class_{metric}_{classifier}_{rank}.png"

    # Filter the data
    data = data[(data["metric"] == metric) &
                (data["classifier"] == classifier) &
                (data["rank"] == rank)]


    # Calculate the median score for each class and sort
    if not sorted_classes:
        sorted_classes = list(data.groupby('class')['score'].median().sort_values(ascending=False).index)

    # Create the plot
    fig_height = len(sorted_classes)/4
    plt.figure(figsize=(8, fig_height))
    sns.boxplot(data=data, x="score", y="class", order=sorted_classes, color=color_per_rank[rank])
    plt.ylabel(f"{rank.capitalize()} class")
    plt.xlabel(f"{metric.capitalize()} score")
    plt.xlim=(0, 1)

    plt.tight_layout()
    plt.savefig(png_name, bbox_inches='tight')
    plt.show()
    plt.close()

    return sorted_classes

# %%
boxplot_one_metric_one_classifier_per_class(per_class_agg_ranks_classifiers_combined, "precision", "random_forest", "species", png_prefix)

# %%
RF_sorted_genus = boxplot_one_metric_one_classifier_per_class(per_class_agg_ranks_classifiers_combined, "precision", "random_forest", "genus", png_prefix)

# %%
RF_sorted_family = boxplot_one_metric_one_classifier_per_class(per_class_agg_ranks_classifiers_combined, "precision", "random_forest", "family", png_prefix)

# %%
boxplot_one_metric_one_classifier_per_class(per_class_agg_ranks_classifiers_combined, "precision", "svc_linear", "species", png_prefix)

# %%
boxplot_one_metric_one_classifier_per_class(per_class_agg_ranks_classifiers_combined, "precision", "svc_linear", "genus", png_prefix, RF_sorted_genus)

# %%
boxplot_one_metric_one_classifier_per_class(per_class_agg_ranks_classifiers_combined, 
                                            "precision", "svc_linear", "family", png_prefix,
                                            RF_sorted_family)

# %%
boxplot_one_metric_one_classifier_per_class(per_class_agg_ranks_classifiers_combined, "precision", "naivebayes", "species", png_prefix)

# %%
boxplot_one_metric_one_classifier_per_class(per_class_agg_ranks_classifiers_combined, "precision", "naivebayes", "genus", png_prefix)

# %%
boxplot_one_metric_one_classifier_per_class(per_class_agg_ranks_classifiers_combined, "precision", "naivebayes", "family", png_prefix)

# %%
boxplot_one_metric_one_classifier_per_class(per_class_agg_ranks_classifiers_combined, "precision", "random_model", "species", png_prefix)

# %%
boxplot_one_metric_one_classifier_per_class(per_class_agg_ranks_classifiers_combined, "precision", "random_model", "genus", png_prefix)

# %%
boxplot_one_metric_one_classifier_per_class(per_class_agg_ranks_classifiers_combined, "precision", "random_model", "family", png_prefix)

