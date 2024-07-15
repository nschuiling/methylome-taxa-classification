#!/usr/bin/env python3

# %% [markdown]
# # Repeated Optuna Optimization-Evaluation for classifier comparison

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
# Only one classifier will be evaluated per script/run. Choose from: 'random_model', 'elastic_net', 'random_forest', 'mlp','svc_linear','svc_nonlinear', 'knn', 'naivebayes'  -->  eventually elastic_net, mlp, and svc_nonlinear did not yield results in the set time (4 days)

# %%
# Command line input to the script
Xy_prefix = sys.argv[1]                 # prefix to the X and y files
rank_level = sys.argv[2]                # "species" or "genus" or "family" 
classifier_to_evaluate = sys.argv[3]    # one classifier will be evaluated
output_folder = sys.argv[4]             # output folder for this classifier
optuna_trials = int(sys.argv[5])        # nr of different pipeline set-ups to try per classifier (per optimization study)
repetition_nr = int(sys.argv[6])        # update with how many times the script has been run for this classifier

# %%
# Define input file names
X_data = f"{Xy_prefix}_Xtrain.npy"                  # normalized methylation profile per read
y_data = f"{Xy_prefix}_ytrain_{rank_level}.npy"     # taxonomic label per read

# %%
# Define output file names
json_evaluation_output = f"{output_folder}/{classifier_to_evaluate}_{rank_level}_rep{repetition_nr}_evaluation.json"
study_backup_file = f"{output_folder}/{classifier_to_evaluate}_{rank_level}_rep{repetition_nr}_study.pkl"
ypred_file = f"{output_folder}/{classifier_to_evaluate}_{rank_level}_rep{repetition_nr}_ypred.npy"

# Make sure that output files do not overwrite each other (just in case)
# json file
if os.path.exists(json_evaluation_output):
    print(f"The output file {json_evaluation_output} already exists.")
    json_evaluation_output = f"{os.path.splitext(json_evaluation_output)[0]}_{int(time())}.json"
    print(f"New output file: {json_evaluation_output}")
# study pkl file
if os.path.exists(study_backup_file):
    print(f"The output file {study_backup_file} already exists.")
    study_backup_file = f"{os.path.splitext(study_backup_file)[0]}_{int(time())}.pkl"
    print(f"New output file: {study_backup_file}")
# ypred numpy file (predictions using the optimized model)
if os.path.exists(ypred_file):
    print(f"The output file {ypred_file} already exists.")
    ypred_file = f"{os.path.splitext(ypred_file)[0]}_{int(time())}.pkl"
    print(f"New output file: {ypred_file}")

# Print the output files
print(f"Will save output to the files: {json_evaluation_output}, {study_backup_file}, and {ypred_file}.")

# %%
# Set seed for reproducability
seed = 54
# Every repetition must use a different (random) split of the data
split_seed = 54 * repetition_nr

# %% [markdown]
# ### Load the X and y data

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

# %%
# Random model
from sklearn.dummy import DummyClassifier

def instantiate_dummy_classifier(trial: Trial) -> DummyClassifier:
    return DummyClassifier(random_state=seed)

# %%
# Elastic net
from sklearn.linear_model import LogisticRegression

def instantiate_elasticnet_classifier(trial: Trial) -> LogisticRegression:
    params = {
        'penalty': 'elasticnet',
        'solver': 'saga',
        'l1_ratio': trial.suggest_float('l1_ratio', 0, 1),
        'random_state': seed
    }
    return LogisticRegression(**params)

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
# MLP (simple neural network)
from sklearn.neural_network import MLPClassifier

def instantiate_mlp_classifier(trial: Trial) -> MLPClassifier:
    params = {
        'hidden_layer_sizes': trial.suggest_categorical('hidden_layer_sizes', [(20,), (50,), (100,), (50, 50)]),
        'alpha': trial.suggest_float('alpha', 1e-4, 5e-2, log=True),
        'max_iter': trial.suggest_int('max_iter', 100, 1000),
        'activation': 'relu',
        'solver': 'adam',
        'random_state': seed
    }
    return MLPClassifier(**params)

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
# Non-linear SVC
from sklearn.svm import SVC

def instantiate_svc_classifier(trial: Trial) -> SVC:
    params = {
        'C': trial.suggest_float('C', 1e-4, 1e+1, log=True),
        'gamma': trial.suggest_float('gamma', 1e-4, 1e+1, log=True),
        'decision_function_shape': 'ovo',
        'kernel': 'rbf',
        'random_state': seed
    }
    return SVC(**params)

# %%
# KNN
from sklearn.neighbors import KNeighborsClassifier

def instantiate_knn_classifier(trial: Trial) -> KNeighborsClassifier:
    params = {
        'n_neighbors': trial.suggest_int('n_neighbors', 3, 20),
        'weights': trial.suggest_categorical('weights', ['uniform', 'distance'])
    }
    return KNeighborsClassifier(**params)

# %%
# Naive Bayes
from sklearn.naive_bayes import ComplementNB

def instantiate_naivebayes_classifier(trial: Trial) -> ComplementNB:
    params = {
        'alpha': trial.suggest_float('alpha', 1e-6, 1e+6, log=True)
    }
    return ComplementNB(**params)

# %%
# Define the type hint for the classifiers
Model = Union[DummyClassifier, LogisticRegression, RandomForestClassifier, MLPClassifier, SGDClassifier, SVC, KNeighborsClassifier, ComplementNB]

# Function to instantiate a model based on the suggested method
# Only ONE model will be tested in the study, as defined by the input into the file
def instantiate_classifier(trial: Trial) -> Model:
    method = trial.suggest_categorical(
        'model_method', [classifier_to_evaluate]
    )
    
    if method == 'random_model':
        classifier = instantiate_dummy_classifier(trial)
    elif method == 'elastic_net':
        classifier = instantiate_elasticnet_classifier(trial)
    elif method == 'random_forest':
        classifier = instantiate_randomforest_classifier(trial)
    elif method == 'mlp':
        classifier = instantiate_mlp_classifier(trial)
    elif method == 'svc_linear':
        classifier = instantiate_sgd_classifier(trial)
    elif method == 'svc_nonlinear':
        classifier = instantiate_svc_classifier(trial)
    elif method == 'knn':
        classifier = instantiate_knn_classifier(trial)
    elif method == 'naivebayes':
        classifier = instantiate_naivebayes_classifier(trial)
    
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

def optimization_objective(trial : Trial, X_optimize : np.ndarray, y_optimize : np.ndarray, n_splits : int=3, seed : int=seed) -> float:
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
  # Alternative scoring: balanced accuracy
  #scores = cross_val_score(pipeline, X_optimize, y_optimize, scoring='balanced_accuracy', cv=cv_folds)
  
  # A single score needs to be returned on which the model can be optimized
  # We take the minimum value of the mean and median, which is more robust to outliers
  return np.min([np.mean(scores), np.median([scores])])

# %% [markdown]
# ### Define the outer part of the optimization
# Use an Optuna study with n trials to optimize the classifier pipeline. Use a random subset of the data, perform a train/test split on it, use the training part for the optimization study and the testing part to evaluate the performance of the best classifier set-up. Save the study and scores to files. This part can be repeated by running the script multiple times."

# %%
from sklearn.metrics import accuracy_score, balanced_accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import classification_report

def score_and_save(best_parameters, y_test, y_pred, start_time, json_evaluation_output):
    """Function to calculate the scores for the model that perfromed best in the Optuna optimization study.
     The best model will be used to make predictions on the test set (in the function run_one_study).
     The predictions (y_pred) will be scored using the true labels (y_test), overall and per class.
     The scores will be saved to the file: json_evaluation_output."""

    # Convert the labels to their original values (for later interpretation)
    y_test = label_encoder.inverse_transform(y_test)
    y_pred = label_encoder.inverse_transform(y_pred)
    np.save(ypred_file, y_pred)

    # Per class performance
    per_class_scores = classification_report(y_test, y_pred, output_dict=True)
    print(f"Per class scores: \n {per_class_scores}")

    # Overall performance
    overall_scores = {
        'accuracy': accuracy_score(y_test, y_pred),
        'balanced_accuracy': balanced_accuracy_score(y_test, y_pred),
        'precision_micro': precision_score(y_test, y_pred, zero_division=0, average='micro'),
        'recall_micro': recall_score(y_test, y_pred, average='micro'),
        'f1_micro': f1_score(y_test, y_pred, average='micro'),
        'precision_macro': precision_score(y_test, y_pred, zero_division=0, average='macro'),
        'recall_macro': recall_score(y_test, y_pred, average='macro'),
        'f1_macro': f1_score(y_test, y_pred, average='macro'),
        'precision_weighted': precision_score(y_test, y_pred, zero_division=0, average='weighted'),
        'recall_weighted': recall_score(y_test, y_pred, average='weighted'),
        'f1_weighted': f1_score(y_test, y_pred, average='weighted')
    }
    print(f"Overall scores: \n {overall_scores}")
    runtime = time() - start_time

    # Structure the data to save
    result = {
        'best_parameters': best_parameters,
        'overall_scores': overall_scores,
        'per_class_scores': per_class_scores,
        'study_run_time': runtime
    }
    print(f"Result: \n {result}")

    # Load existing results if the file exists
    if os.path.exists(json_evaluation_output):
        with open(json_evaluation_output, 'r') as f:
            results = json.load(f)
    else:
        results = []
    
    # Append the new result
    results.append(result)
    
    # Save the results back to the JSON file
    with open(json_evaluation_output, 'w') as f:
        json.dump(results, f, indent=4)
    
    print(f"Results saved to {json_evaluation_output}")

# %%
from optuna import create_study
import logging

def run_one_study(X_train : np.ndarray, y_train : np.ndarray, X_test : np.ndarray, y_test : np.ndarray,
                  json_evaluation_output, optuna_trials : int=30):
    """Function to run one Optuna optimization study. In one study, a number of trials with different
    scaler/selector/hyperparameter settings will be compared. The optimal settings will be searched for
    using a Bayesian algorithm. The best performing set-up will be evaluated on the validation data."""

    # Start the timer
    start_time = time()

    # Define the study set-up
    # The study will use sampling and pruning to find the best classifier pipeline
    # I.e. the best hyperparameters, scaler, and selector for the classifier under analysis
    # Optuna recommends the TPESampler - HyperBandPruner combination
    sampler = optuna.samplers.TPESampler()
    pruner = optuna.pruners.HyperbandPruner()
    study = create_study(direction='maximize', sampler=sampler, pruner=pruner)

    # A training set will be used to run the hyperparameter optimization
    # A nr (=optuna_trials) of different scaler/selector/parameter combinations will be tested
    # One study can run for a maximum of 5 days (400.000 seconds, plus extra time for the train-test splits etc)
    optuna.logging.get_logger("optuna").addHandler(logging.StreamHandler(sys.stdout))
    study.optimize(lambda trial: optimization_objective(trial, X_train, y_train),
                   n_trials=optuna_trials, n_jobs=4, gc_after_trial=True, timeout=260000)
    # Save the study for later (additional/back-up) analysis
    print(f"Saving the study to {study_backup_file}")
    joblib.dump(study, study_backup_file)

    # Print the performance and settings of the best pipeline
    print(f"Best parameters: {study.best_params}")
    print(f"Best score: {study.best_value}")

    # Train the best pipeline (scaler-selector-classifier) on the full training data
    print("Retraining the best model for evaluation.")
    best_trial = study.best_trial
    best_model = instantiate_classifier(best_trial)
    best_model.fit(X_train, y_train)

    # Make predictions on the test data
    print("Making predictions with the retrained model.")
    y_pred = best_model.predict(X_test)

    # Evaluate the model performance
    print("Evaluating the retrained model.")
    score_and_save(study.best_params, y_test, y_pred, start_time, json_evaluation_output)
    

# %%
from sklearn.model_selection import train_test_split

def run_one_optimization_repetition(X : np.ndarray, y : np.ndarray, json_evaluation_output : str, optuna_trials : int):
    """Function to prepare the data for one optimization study.
    A random subset of the data will be used (80%) to reduce computational intensity/overload.
    A train/validation split will be performed on this data to use for independent optimization and evaluation.
    This function could be repeated to obatain performances based on different data subsets. 
    Preferably, repetitions are run by calling the script multiple times (enabling parallelism)."""
    
    print(f"Starting data preparation for one optimization study.")

    # The complete dataset is too big to use (computationally slow and expensive)
    # Create a stratified include/exclude split (20%:80%)
    X_include, X_exclude, y_include, y_exclude = train_test_split(X, y, test_size=0.80, stratify=y, random_state=split_seed)
    del X_exclude, y_exclude

    # Run a train-validation split (90%:10%) on the included data
    # Use 90% of the data for scaler/selector/hyperparameter optimization
    # Use 10% of the data for evaluation of the best performing pipeline
    X_train, X_test, y_train, y_test = train_test_split(X_include, y_include, test_size=0.10, stratify=y_include, random_state=split_seed)
    del X_include, y_include

    # Run an optuna optimization study on the training data (with number of trials = optuna_trials) 
    # The function includes evaluation of the best model on the test data 
    print(f"Starting the Optuna study with {optuna_trials} trials.")
    run_one_study(X_train, y_train, X_test, y_test, json_evaluation_output, optuna_trials=optuna_trials)
        
    # Finished this round
    del X_train, y_train
    print(f"Finished optimization.")


# %%
# Create a list of all taxonomic labels to ensure the same order of per-class scores
run_one_optimization_repetition(X, y, json_evaluation_output, optuna_trials=optuna_trials)
