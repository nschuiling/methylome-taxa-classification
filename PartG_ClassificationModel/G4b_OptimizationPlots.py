# %%
#!/usr/bin/env python3

# %% [markdown]
# # Print the outcomes of the final optimization study

# %% [markdown]
# ### Prepare the environment

# %%
# Load utilities
import sys
import os
import joblib
import optuna
import numpy as np
from time import time
import matplotlib.pyplot as plt
import seaborn as sns

# %% [markdown]
# ### Define input and output

# %%
study_path = sys.argv[1]
figure_prefix = sys.argv[2]


# %% [markdown]
# ### Load Optuna study and show best scores and parameters

# %%
optimization_study = joblib.load(study_path)

# %%
print("Best score:")
print(optimization_study.best_value)

# %%
print("Best parameters:")
print(optimization_study.best_params)

# %% [markdown]
# ### Visualize optimization results

# %%
parameters = list(optimization_study.best_params.keys())
parameters.remove("model_method")
parameters

# %%
fig = optuna.visualization.plot_optimization_history(optimization_study)
fig.update_layout(
    width=1800,
    height=500,
    font_size=14
)
fig.write_image(f"{figure_prefix}_history.png")

# %%
fig = optuna.visualization.plot_slice(optimization_study, params=parameters)
fig.update_layout(
    width=2000,
    height=500,
    font_size=14
)
fig.write_image(f"{figure_prefix}_sliceplot.png")

# %%
fig = optuna.visualization.plot_rank(optimization_study, params=parameters)

fig.update_layout(
    width=1800,
    height=1600,
    font_size=14
)

fig.write_image(f"{figure_prefix}_rankplot.png")

# %%
fig = optuna.visualization.plot_parallel_coordinate(optimization_study, params=parameters)
fig.update_layout(
    width=1800,
    height=500,
    font_size=14
)
fig.write_image(f"{figure_prefix}_parallelcoordinate.png")

# %%
fig = optuna.visualization.plot_contour(optimization_study, params=parameters)
fig.update_layout(
    width=1800,
    height=1800,
    font_size=14
)
fig.write_image(f"{figure_prefix}_contourplot.png")

# %%
fig = optuna.visualization.plot_edf(optimization_study)
fig.update_layout(
    width=1800,
    height=500,
    font_size=14
)
fig.write_image(f"{figure_prefix}_edf.png")

# %%
fig = optuna.visualization.plot_timeline(optimization_study)
fig.update_layout(
    width=1800,
    height=500,
    font_size=14
)
fig.write_image(f"{figure_prefix}_timeline.png")

# %%
fig = optuna.visualization.plot_param_importances(optimization_study, params=parameters)
fig.update_layout(
    width=900,
    height=500,
    font_size=14
)
fig.write_image(f"{figure_prefix}_paramimportances.png")

# %%
fig = optuna.visualization.plot_param_importances(optimization_study, target=lambda t: t.duration.total_seconds(), target_name="duration")
fig.update_layout(
    width=1800,
    height=500,
    font_size=14
)
fig.write_image(f"{figure_prefix}_paramimportances_duration.png")
