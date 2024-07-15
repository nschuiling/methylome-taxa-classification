# %%
#!/usr/bin/env python3

# %% [markdown]
# # Evaluate feature importances in final models

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
import joblib
from time import time
import sys

# %% [markdown]
# ### Load the final model

# %%
rank_level = sys.argv[1]
classifier_type = sys.argv[2]
feature_selection = sys.argv[3]
trained_pipeline_path = sys.argv[4]
motifs_list_file = sys.argv[5]
output_prefix = sys.argv[6]

importances_csv_name = f"{output_prefix}_feature_importances.csv"

# %%
# Define output file names
trained_pipeline = joblib.load(trained_pipeline_path)
if feature_selection == "True":
    feature_selector = trained_pipeline.named_steps['selector']
trained_classifier = trained_pipeline.named_steps['classifier']


# %%
# Use Pickle to load the list of motifs
with open(motifs_list_file, 'rb') as f:
    motif_list = pickle.load(f)

# %% [markdown]
# ### Evaluate random forest feature importances: impurity

# %% [markdown]
# https://scikit-learn.org/stable/auto_examples/ensemble/plot_forest_importances.html

# %%
def get_RF_feature_importances(trained_RF, motif_list, importances_csv_name):
    
    # Track the time
    start_time = time()
    importances = trained_RF.feature_importances_
    std = np.std([tree.feature_importances_ for tree in trained_RF.estimators_], axis=0)
    elapsed_time = time() - start_time
    # How long did it take?
    print(f"Elapsed time to compute the importances: {elapsed_time:.3f} seconds")

    # Return the importances and standard deviation in a dataframe
    forest_importances = pd.DataFrame(zip(motif_list, importances, std), columns=["motif", "importance", "std"]).sort_values(by="importance", ascending=False)
    forest_importances.to_csv(importances_csv_name, index=False)
    return forest_importances

# %%
def plot_top50_features(forest_importances, png_name):

    # PLot only the top 50
    plot_features = forest_importances.iloc[0:50]

    # Plot the top 100 features
    fig, ax = plt.subplots(figsize=(16, 10))
    plot_features.plot.bar(x="motif", y="importance", yerr="std", ax=ax)
    ax.set_title("Top 50 impurity-based motif importances")
    ax.set_ylabel("Mean decrease in impurity")
    ax.set_xlabel("Motif")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, fontsize=12)

    # Save the figure
    plt.savefig(png_name, bbox_inches='tight')

# %%
if classifier_type == "random_forest":
    forest_importances = get_RF_feature_importances(trained_classifier, motif_list, importances_csv_name)
    top_200_features = forest_importances.iloc[0:200]["motif"]
    png_name = f"{output_prefix}_feature_importances.png"
    plot_top50_features(forest_importances, png_name)

    # SAVE THIS DF

# %% [markdown]
# ### Evaluate linear SVM feature importances

# %%
def get_selected_features(feature_selector):
    selected_features_indices = feature_selector.get_support()
    return selected_features_indices

# %%
def get_linSVM_feature_importances(trained_SVM, motif_list, importances_csv_name):
    coefficients = trained_SVM.coef_
    classes = trained_SVM.classes_

    df_coefficients = pd.DataFrame(coefficients, index=classes, columns=motif_list)
    df_coefficients.loc["total"] = df_coefficients.abs().sum()
    sorted_coefficients = df_coefficients.sort_values(by="total", ascending=False, axis=1)

    sorted_coefficients.to_csv(importances_csv_name, index=True)
    return sorted_coefficients
    

# %%
def plot_SVM_feature_importances(top_N_motifs, taxa_to_show, png_name):

    top_N_motifs_melted = top_N_motifs.loc[taxa_to_show,:].melt(var_name='Motif', value_name='Importance', ignore_index=False).reset_index(drop=False, names="Class")

    sns.set_theme(style="whitegrid") #, font_scale = 1.4)
    f, ax = plt.subplots(figsize=(22, 6))
    sns.barplot(top_N_motifs_melted, x="Motif", y="Importance", hue="Class", palette=["#a6cee3", "#1f78b4", "#33a02c", "#b2df8a"])
    ax.set(xlabel="Motif", ylabel="Classifier coefficient")
    plt.xticks(rotation=90)
    plt.savefig(png_name, bbox_inches = "tight")

# %%
from itertools import compress

if classifier_type == "svc_linear":
    if feature_selection == "True":
        selected_features_indices = get_selected_features(feature_selector)
        selected_motifs = list(compress(motif_list, selected_features_indices))
    else:
        selected_motifs = motif_list
    
    # Calculate the coefficients for the motif-class combinations
    coefficients = get_linSVM_feature_importances(trained_classifier, selected_motifs, importances_csv_name)
    top_N = 40
    top_N_motifs = coefficients.iloc[:,0:top_N].drop(index="total")
    
    if rank_level == "genus":
        taxa_to_show = [286, 239934, 1301, 2569097]
    elif rank_level == "species":
        taxa_to_show = [256701, 165179, 273384, 216816]
    png_name = f"{output_prefix}_feature_importances_some_species.png"
    plot_SVM_feature_importances(top_N_motifs, taxa_to_show, png_name)

    # %%
    top_N_motifs
