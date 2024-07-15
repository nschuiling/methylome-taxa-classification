#!/usr/bin/env python3

# %% [markdown]
# # Train the final model

# %% [markdown]
# ### Prepare the environment

# %%
# Load utilities
import sys
import os
import numpy as np
from time import time
import joblib

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
# Command line input to the script
Xy_prefix = sys.argv[1]         # prefix to the X and y files
rank_level = sys.argv[2]        # "species" or "genus" or "family"
model_folder = sys.argv[3]      # output folder to save the classifier to
selected_classifier = sys.argv[4]   # "random_forest" or "svc_linear"

# %% [markdown]
# ### Define the input and output file names

# %%
# Define input file names
X_train_file = f"{Xy_prefix}_Xtrain.npy"
y_train_file = f"{Xy_prefix}_ytrain_{rank_level}.npy"

# %%
# Define output file names
final_model_file = f"{model_folder}/{selected_classifier}_{rank_level}.pkl"

# %%
# Make sure that output files do not overwrite each other (just in case)
# model pkl file
if os.path.exists(final_model_file):
    print(f"The output file {final_model_file} already exists.")
    final_model_file = f"{os.path.splitext(final_model_file)[0]}_{int(time())}.pkl"
    print(f"New output file: {final_model_file}")

# %%
# Print the output file name
print(f"Will save output to the file: {final_model_file}.")

# %%
# Set seed for reproducability
seed = 54

# %% [markdown]
# ### Load the X and y training data

# %%
# Load the training data and labels
X_train = np.load(X_train_file)
y_train = np.load(y_train_file)

# %% [markdown]
# ### Build final classification pipeline

# Robust scaler
from sklearn.preprocessing import RobustScaler
# Variance based feature selection
from sklearn.feature_selection import VarianceThreshold
# Random forest
from sklearn.ensemble import RandomForestClassifier
# Linear SVM
from sklearn.linear_model import SGDClassifier


## Set optimized parameters (from hyperparameter optimization)
rf_params_species = {
    'n_estimators': 187,
    'max_depth': 25,
    'min_samples_split': 7,
    'min_samples_leaf': 2,
    'random_state': seed
}

rf_params_genus = {
    'n_estimators': 130,
    'max_depth': 18,
    'min_samples_split': 2,
    'min_samples_leaf': 1,
    'random_state': seed
}

svc_params_species = {
    'alpha':0.00010159485975474086,
    'loss': 'hinge',
    'random_state': seed
}

svc_params_genus = {
    'alpha':0.00014535295123432434,
    'loss': 'hinge',
    'random_state': seed
}


## Define model pipelines

# For training the random forest
if selected_classifier == "random_forest":
    if rank_level == "species":
        classifier = RandomForestClassifier(**rf_params_species)
    elif rank_level == "genus":
        classifier = RandomForestClassifier(**rf_params_genus)
        
    # Both species and genus RF were optimal with robust scaling and without feature selection
    scaler = RobustScaler(with_centering=False, with_scaling=True)
    selector = "passthrough"
    
    
# For training the linear SVM
elif selected_classifier == "svc_linear":
    # Set the linear SVM parameters based on the rank
    if rank_level == "species":
        classifier = SGDClassifier(**svc_params_species)
        # Species level SVM was best without scaling or feature selection
        scaler = "passthrough"
        selector = "passthrough"
    elif rank_level == "genus":
        classifier = SGDClassifier(**svc_params_genus)
        # Genus level SVM was best without scaling but with selection
        scaler = "passthrough"
        selector = VarianceThreshold(threshold=0.0002040697764339664)


# Define the full pipeline
from sklearn.pipeline import Pipeline
pipeline = Pipeline([
        ('scaler', scaler),
        ('selector', selector),
        ('classifier', classifier)
    ])

# %% [markdown]
# ### Train final model on full training data

# %%
# Fit the classifier to the training data
pipeline.fit(X_train, y_train)

# %% [markdown]
# ### Save the final trained model

# %%
# Save the model for later validation and application
joblib.dump(pipeline, final_model_file)
