# %%
#!/usr/bin/env python3

# %% [markdown]
# ### Optimize the settings for the chosen classifiers

# %% [markdown]
# ### Prepare the environment

# %%
# Load utilities
import sys
import os
import joblib
import optuna
import numpy as np
from optuna import Trial
from typing import Union
from time import time
import matplotlib.pyplot as plt
import seaborn as sns

# For cleaner output (optional)
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")
    os.environ["PYTHONWARNINGS"] = "ignore"

# To speed up sklearn actions
from sklearnex import patch_sklearn
patch_sklearn()

# %%
#pip install nbformat # > v5
#pip install -U kaleido

# %% [markdown]
# ### Define the input and output file names

# %%
# # Command line input to the script
Xy_prefix = sys.argv[1]                 # prefix to the X and y files
rank_level = sys.argv[2]                # "species" or "genus" or "family" 
classifier_to_evaluate = sys.argv[3]    # one classifier will be evaluated
output_folder = sys.argv[4]             # output folder for this classifier
optuna_trials = int(sys.argv[5])        # nr of different pipeline set-ups to try per classifier (per optimization study)
settings_nr = int(sys.argv[6])        # update with how many times the script has been run for this classifier

# %%
# Define input file names
X_data = f"{Xy_prefix}_Xtrain.npy"                  # normalized methylation profile per read
y_data = f"{Xy_prefix}_ytrain_{rank_level}.npy"     # taxonomic label per read

# %%
# Define output file names
study_backup_file = f"{output_folder}/{classifier_to_evaluate}_{rank_level}_{settings_nr}trials_study.pkl"
figure_prefix = f"{output_folder}/{classifier_to_evaluate}_{rank_level}_{settings_nr}trials"

# %%
# Make sure that output files do not overwrite each other (just in case)
# study pkl file
if os.path.exists(study_backup_file):
    print(f"The output file {study_backup_file} already exists.")
    study_backup_file = f"{os.path.splitext(study_backup_file)[0]}_{int(time())}.pkl"
    print(f"New output file: {study_backup_file}")
# figure prefix
if os.path.exists(figure_prefix):
    print(f"The output file {figure_prefix} already exists.")
    figure_prefix = f"{os.path.splitext(figure_prefix)[0]}_{int(time())}.pkl"
    print(f"New output file: {figure_prefix}")

# %%
# Print the output files
print(f"Will save output to the files: {study_backup_file}, and figures with prefix {figure_prefix}.")

# %%
# Set seed for reproducability
seed = 54
# Every repetition must use a different (random) split of the data
split_seed = 54321

# %% [markdown]
# ### Load the X and y data

# %%
# %%
# Load the training data and labels
X = np.load(X_data)
y = np.load(y_data)

# %%
# Check the memory consuption of the methylation profile (X)
# This has already been reduced in the train/test split script
print(f"Memory consumption of the numpy methylation profile (X): {X.nbytes/1000000} mb")
print(f"Memory consumption of the taxonomic labels (y): {y.nbytes/1000000} mb")

# %%
# Show the data (X and y)
print(f"Numpy representation of the taxonomic labels (y): {y}")
print(f"Numpy representation of the methylation profile (X): {X}")

# %%
# Show the nr of reads and taxonomies in the training data
print(f"Nr of reads in training data = {len(y)}")
print(f"Nr of taxonomies in training data = {len(np.unique(y))}")

# %% [markdown]
# ### Encode the labels

# %%
from sklearn.preprocessing import LabelEncoder

label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y)
y_original = label_encoder.inverse_transform(y)

# %%
# Show the encoded labels
print(f"Numpy representation of the encoded labels (y): {y}")

# %% [markdown]
# ### Define scalers to be tested: no scaling, MinMaxScaler, RobustScaler

# %%
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import RobustScaler

Scaler = Union[str, MinMaxScaler, RobustScaler]

def instantiate_scaler(trial : Trial) -> Scaler:
  method = trial.suggest_categorical(
    'scaling_method', ['passthrough', 'minmax', 'robust'])
  
  if method=='passthrough':
    return 'passthrough'
  elif method=='minmax':
    return MinMaxScaler()
  elif method=='robust':
    return RobustScaler(with_centering=False, with_scaling=True)

# %% [markdown]
# ### Define feature selectors to be tested: no selection, variance-based selection, ANOVA-based selection

# %%
# %%
from sklearn.feature_selection import VarianceThreshold

def instantiate_variance_selector(trial: Trial) -> VarianceThreshold:
    params = {
        'threshold': trial.suggest_float('threshold', 1e-5, 1e-2/2)
    }
    return VarianceThreshold(**params)

# %%
from sklearn.feature_selection import SelectKBest, f_classif

def instantiate_anova_selector(trial: Trial) -> SelectKBest:
    params = {
        'k': trial.suggest_int('k', 100, 1000)
    }
    return SelectKBest(f_classif, **params)

# %%
Selector = Union[str, VarianceThreshold, SelectKBest]

def instantiate_selector(trial : Trial) -> Selector:
  method = trial.suggest_categorical(
    'selector_method', ['passthrough', 'variance', 'anova'])
  
  if method=='passthrough':
    return 'passthrough'
  elif method=='variance':
    return instantiate_variance_selector(trial)
  elif method=='anova':
    return instantiate_anova_selector(trial)

# %% [markdown]
# ### Define classification models to be tested: random model, elastic net, random forest, MLP, linear SVC, non-linear SVC, KNN, Naive Bayes
# 

# %%
# Random forest
from sklearn.ensemble import RandomForestClassifier

def instantiate_randomforest_classifier(trial: Trial) -> RandomForestClassifier:
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 20, 200),
        'max_depth': trial.suggest_int('max_depth', 10, 30),
        'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
        'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 4),
        'random_state': seed
    }
    return RandomForestClassifier(**params)

# %%
# Linear SVC
from sklearn.linear_model import SGDClassifier

def instantiate_sgd_classifier(trial: Trial) -> SGDClassifier:
    params = {
        'alpha': trial.suggest_float('alpha', 1e-4, 1e+1, log=True),
        'loss': 'hinge',
        'random_state': seed
    }
    return SGDClassifier(**params)

# %%
# Define the type hint for the classifiers
Model = Union[RandomForestClassifier, SGDClassifier]

# Function to instantiate a model based on the suggested method
# Only ONE model will be tested in the study, as defined by the input into the file
def instantiate_classifier(trial: Trial) -> Model:
    method = trial.suggest_categorical(
        'model_method', [classifier_to_evaluate]
    )
    
    if method == 'random_forest':
        classifier = instantiate_randomforest_classifier(trial)
    elif method == 'svc_linear':
        classifier = instantiate_sgd_classifier(trial)
    
    return classifier

# %% [markdown]
# ### Build Optuna evaluation and optimization pipeline

# %%
# Pipeline combining a scaler-selector-classifier, including set hyperparameters
from sklearn.pipeline import Pipeline

def instantiate_pipeline(trial: Trial) -> Pipeline:
    """This function creates a pipeline with a scaler, a selector, a classifier, and their hyperparameter settings.
    The classifier is predifined as input into this script, but it's hyperparameters and scaler/selector can be tuned.
    Essentially, each time this function is called, the classifier is combined with different hyperparemeters, a scaler and a selector."""

    scaler = instantiate_scaler(trial)
    selector = instantiate_selector(trial)
    classifier = instantiate_classifier(trial)  # Only one per script

    pipeline = Pipeline([
        ('scaler', scaler),
        ('selector', selector),
        ('classifier', classifier)
    ])

    return pipeline

# %%
# Define the optimization objective
# The performance of each scaler-selector-classifier combination will be evaluated on this objective
# Optuna will use that performance to tune the scaler, selector, and hyperparameters combined with the classifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import make_scorer, precision_score

def optimization_objective(trial : Trial, X_optimize : np.ndarray, y_optimize : np.ndarray) -> float:
  """This function performs one instance of hyperparameter optimization for one (or more) classifiers.
  It runs ONE combination of scaler-selecor-classifier WITH set parameters.
  The pipeline is evaluated by a cross validation on n_splits folds.
  This means that the training occurs on a part of the data each time, and the evaluation on the other part.
  The multiple scores are combined into a final (mean/median) score for this pipeline and settings.
  This function will be repeated many times (by optuna) to find the best performing model and settings."""
  
  # Combine the suggested models and parameters into a pipeline
  pipeline = instantiate_pipeline(trial)
  print(pipeline)

  # Run the pipeline through multiple evaluation rounds
  # Optimization will use macro precision as a metric
  # The goal is to limit false positives (using precision)
  # and to account for imbalance (using macro averaging)
  cv_folds = StratifiedKFold(n_splits=3, shuffle=True, random_state=split_seed)
  precision_scorer = make_scorer(precision_score, average='macro', zero_division=0)
  scores = cross_val_score(pipeline, X_optimize, y_optimize, scoring=precision_scorer, cv=cv_folds)
  
  # A single score needs to be returned on which the model can be optimized
  # We take the minimum value of the mean and median, which is more robust to outliers
  return np.min([np.mean(scores), np.median([scores])])

# %% [markdown]
# ### Define the outer part of the optimization

# %%
from sklearn.model_selection import train_test_split
from optuna import create_study
import logging

def run_hyperparameter_optimization(X : np.ndarray, y : np.ndarray, optuna_trials : int=100):
    """Function to run one Optuna optimization study. In one study, a number of trials with different
    scaler/selector/hyperparameter settings will be compared. The optimal settings will be searched for
    using a Bayesian algorithm. The best performing set-up will be evaluated on the validation data.
    A random subset of the data will be used (50%) to reduce computational intensity/overload."""

    # Start the timer
    start_time = time()

    # The complete dataset is too big to use (computationally slow and expensive)
    # Create a stratified include/exclude split (20%:80%)
    print(f"Starting data preparation for one optimization study.")
    X_train, X_exclude, y_train, y_exclude = train_test_split(X, y, test_size=0.80, stratify=y, random_state=split_seed)
    del X_exclude, y_exclude

    # Define the study set-up
    # The study will use sampling and pruning to find the best classifier pipeline
    # I.e. the best hyperparameters, scaler, and selector for the classifier under analysis
    # Optuna recommends the TPESampler - HyperBandPruner combination
    sampler = optuna.samplers.TPESampler()
    #pruner = optuna.pruners.HyperbandPruner()
    optimization_study = create_study(direction='maximize', sampler=sampler) #, pruner=pruner)

    # A training set will be used to run the hyperparameter optimization
    # A nr (=optuna_trials) of different scaler/selector/parameter combinations will be tested
    # One study can run for a maximum of 5 days (400.000 seconds, plus extra time for the train-test splits etc)
    optuna.logging.get_logger("optuna").addHandler(logging.StreamHandler(sys.stdout))
    optimization_study.optimize(lambda trial: optimization_objective(trial, X_train, y_train),
                                n_trials=optuna_trials, n_jobs=4, gc_after_trial=True, timeout=260000)
    study_time = time() - start_time

    # Save the study for later (additional/back-up) analysis
    print(f"Saving the study to {study_backup_file}")
    joblib.dump(optimization_study, study_backup_file)

    # Print the performance and settings of the best pipeline
    print(f"Best parameters: {optimization_study.best_params}")
    print(f"Best score: {optimization_study.best_value}")

    return optimization_study, study_time

# %%
# Run an optuna optimization study on the training data (with number of trials = optuna_trials) 
# The function includes evaluation of the best model on the test data 
print(f"Starting the Optuna study with {optuna_trials} trials.")
optimization_study, study_time = run_hyperparameter_optimization(X, y, optuna_trials=optuna_trials)
print(f"Finished optimization. Study took {study_time} seconds.")
