#!/usr/bin/env python3

# %% [markdown]
# # Evaluate the final model

# %% [markdown]
# ### Prepare the environment

# %%
# Load utilities
import sys
import os
import numpy as np
import pandas as pd
import joblib
import json

# For cleaner output (optional)
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")
    os.environ["PYTHONWARNINGS"] = "ignore"

# To speed up sklearn actions
from sklearnex import patch_sklearn
patch_sklearn()

# %% [markdown]
# ### Define the input and output file names

# %%
Xy_holdout_prefix = sys.argv[1]
Xy_independent_prefix = sys.argv[2]
rank_level = sys.argv[3]
trained_classifier_path = sys.argv[4]
evaluation_output_prefix = sys.argv[5]

# Output file names, for evaluation in a seperate script
ypred_holdout_file = f"{evaluation_output_prefix}_ypred_holdout.npy"
ypred_independent_file = f"{evaluation_output_prefix}_ypred_independent.npy"
json_evaluation_output_holdout = f"{evaluation_output_prefix}_evaluation_holdout.json"
json_evaluation_output_independent = f"{evaluation_output_prefix}_evaluation_independent.json"

# %%
# Set seed for reproducability
seed = 54

# %% [markdown]
# ### Load the test data and model

# %%
# Holdout test files
X_test_holdout_file = f"{Xy_holdout_prefix}_Xtest.npy"
y_test_holdout_file = f"{Xy_holdout_prefix}_ytest_{rank_level}.npy"

# Load the holdout test data and labels
X_test_holdout = np.load(X_test_holdout_file)
y_test_holdout = np.load(y_test_holdout_file)

# Show the nr of reads and taxonomies in the holdout test data
print(f"Nr of reads in holdout test data = {len(y_test_holdout)}")
print(f"Nr of taxonomies in holdout test data = {len(np.unique(y_test_holdout))}")

# %%
# Independent test files
X_test_independent_file = f"{Xy_independent_prefix}_X.npy"
y_test_independent_file = f"{Xy_independent_prefix}_y_{rank_level}.npy"

# Load the independent test data and labels
X_test_independent = np.load(X_test_independent_file)
y_test_independent = np.load(y_test_independent_file)

# Show the nr of reads and taxonomies in the independent test data
print(f"Nr of reads in independent test data = {len(y_test_independent)}")
print(f"Nr of taxonomies in independent test data = {len(np.unique(y_test_independent))}")

# %%
# Define output file names
trained_classifier = joblib.load(trained_classifier_path)

# %% [markdown]
# ### Use the model to make predictions

# %%
y_pred_holdout = trained_classifier.predict(X_test_holdout)
np.save(ypred_holdout_file, y_pred_holdout)
print("Saved the holdout test set predictions.")

# %%
y_pred_independent = trained_classifier.predict(X_test_independent)
np.save(ypred_independent_file, y_pred_independent)
print("Saved the independent test set predictions.")

# %% [markdown]
# ### Evaluate the predictions

# %%
from sklearn.metrics import accuracy_score, balanced_accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import classification_report

def evaluate_predictions(y_test, y_pred, json_evaluation_output):
    """Function to evaluate a classification pipelinne..
     The model will be used to make predictions on the test set.
     The predictions (y_pred) will be scored using the true labels (y_test), overall and per class.
     The scores will be saved to the file: json_evaluation_output."""

    # Per class performance
    per_class_scores = classification_report(y_test, y_pred, output_dict=True, zero_division=np.nan)
    print(f"Per class scores: \n {per_class_scores}")

    # Overall performance
    overall_scores = {
        'accuracy': accuracy_score(y_test, y_pred),
        'balanced_accuracy': balanced_accuracy_score(y_test, y_pred),
        'precision_micro': precision_score(y_test, y_pred, zero_division=np.nan, average='micro'),
        'recall_micro': recall_score(y_test, y_pred, zero_division=np.nan, average='micro'),
        'f1_micro': f1_score(y_test, y_pred, zero_division=np.nan, average='micro'),
        'precision_macro': precision_score(y_test, y_pred, zero_division=np.nan, average='macro'),
        'recall_macro': recall_score(y_test, y_pred, zero_division=np.nan, average='macro'),
        'f1_macro': f1_score(y_test, y_pred, zero_division=np.nan, average='macro'),
        'precision_weighted': precision_score(y_test, y_pred, zero_division=np.nan, average='weighted'),
        'recall_weighted': recall_score(y_test, y_pred, zero_division=np.nan, average='weighted'),
        'f1_weighted': f1_score(y_test, y_pred, zero_division=np.nan, average='weighted')
    }
    print(f"Overall scores: \n {overall_scores}")

    # Structure the data to save it to a json file
    result = {'overall_scores': overall_scores, 'per_class_scores': per_class_scores}
    # Save the results to a JSON file
    with open(json_evaluation_output, 'w') as f:
        json.dump(result, f, indent=4)

    return overall_scores, per_class_scores

# %%
overall_scores_holdout, per_class_scores_holdout = evaluate_predictions(y_test_holdout, y_pred_holdout,
                                                                        json_evaluation_output_holdout)
print("Saved the holdout test set evaluations.")

# %%
overall_scores_independent, per_class_scores_independent = evaluate_predictions(y_test_independent, y_pred_independent,
                                                                                json_evaluation_output_independent)
print("Saved the independent test set evaluations.")

