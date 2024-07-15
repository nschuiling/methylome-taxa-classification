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
X_data = sys.argv[1]
rank_level = sys.argv[2]
trained_classifier_path = sys.argv[3]
predictions_output_prefix = sys.argv[4]

# Output file names, for evaluation in a seperate script
ypred_file = f"{predictions_output_prefix}_ypred.npy"

# %%
# Set seed for reproducability
seed = 54

# %% [markdown]
# ### Load the test data and model

# Load the holdout test data and labels
X_application = np.load(X_data)

# Show the nr of reads and taxonomies in the holdout test data
print(f"Nr of reads in application data = {len(X_application)}")

# %%
# Define output file names
trained_classifier = joblib.load(trained_classifier_path)

# %% [markdown]
# ### Use the model to make predictions

# %%
y_pred = trained_classifier.predict(X_application)
np.save(ypred_file, y_pred)
print("Saved the application dataset predictions.")
