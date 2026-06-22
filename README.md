# Swarm Data Fusion (SwarmDF)

SwarmDF is a Python tool designed to automate the full workflow for analysing high-latitude ionospheric electrodynamics using multi-instrument observations.

## Overview

SwarmDF uses the [Lompe technique](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2022JA030356) to combine measurements from Swarm satellites with complementary datasets (SuperMAG, SuperDARN, Iridium/AMPERE, DMSP/SSIES) and reconstruct two-dimensional maps of ionospheric electrodynamics along and around a user-defined Swarm trajectory.

### Key features:
- End-to-end automated workflow
- Multi-instrument data fusion  
- Electrodynamics reconstruction using [Lompe](https://github.com/klaundal/lompe)  
- Built-in validation tool (LompeOSSE, under development)
- User-friendly graphical interface

## Package installation

```bash
git clone https://github.com/Margot-D/SwarmDF.git
cd SwarmDF
pip install .
```

### Dependencies 

SwarmDF requires several external Python packages.
If Lompe is already installed, the following dependencies may still be needed:
`pip install customtkinter tkcalendar imageio pillow`

<!-- SwarmDF also integrates LompeOSSE (under development) as a built-in validation tool:<br>
```bash
git clone https://github.com/Margot-D/lompe_osse.git (not functional yet)
cd lompe_osse
pip install .
``` -->

<!-- ### Environment setup (recommended)

An environment file (swarmdf_environment.yml) is provided to install all dependencies automatically, including Lompe and LompeOSSE:
`conda env create -f swarmdf_environment.yml` -->

## Getting started 

Once installed, the commands `swarmdf-gui` and `swarmdf` are available from any terminal within the active Python environment.

### Graphical user interface (recommended)
```bash
swarmdf-gui
```

The GUI can also generate a standalone Python script reproducing the configured SwarmDF workflow. This allows users to inspect, modify, and rerun the analysis outside the GUI.

### Command-line interface
For a quick start, run the built-in demo using sample datasets:
```bash
swarmdf --demo
```

Run a full SwarmDF analysis using a configuration file:<br>
```bash
swarmdf --config path/to/config.yaml
```
An example configuration files is provided in the examples/ directory.

Optional advanced plotting settings can be provided through a separate configuration file. If omitted, default plotting settings are used.

```bash
swarmdf --config path/to/config.yaml --plot-config path/to/plot_settings.yaml
```

## Python interface

SwarmDF can also be used directly from Python, which allows full control over the workflow and direct access to results and plots.

### Run a demo analysis:

```python
from swarmdf.config import SwarmDFConfig, SwarmDFPlotSettings
from swarmdf.pipeline import *

config = SwarmDFConfig.default()  
plot_settings = SwarmDFPlotSettings.default() 

results = run_swarmdf_pipeline(config=config, plot_settings=plot_settings, use_sample_data=True)
```

To run a custom analysis, set `use_sample_data=False` and configure the desired analysis and plotting parameters through `SwarmDFConfig` and `SwarmDFPlotSettings`.

### Plot results:

```python
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from PIL import Image

# %matplotlib inline
for input_fig in results.plots.input_frames:
    plt.figure(figsize=(8, 6))
    plt.imshow(Image.open(input_fig))
    plt.axis("off")
    plt.show()

if config.run_lompe_flag:
    # %matplotlib inline
    for output_fig in results.plots.output_frames:
        plt.figure(figsize=(8, 6))
        plt.imshow(Image.open(output_fig))
        plt.axis("off")
        plt.show()
```

<!-- #TODO add lompeosse when ready
# if config.run_validation_flag: # use result.plots.validation_frames
#     # %matplotlib inline
#     for framea, frameb in zip(results.validation.lompeOSSE_PILframes, results.validation.gamera_PILframes):
#         fig, ax = plt.subplots(1, 2, figsize=(10, 5))
#         ax[0].imshow(np.array(framea))
#         ax[0].axis("off")
#         ax[1].imshow(np.array(frameb))
#         ax[1].axis("off")
#         plt.tight_layout()
#         plt.show() -->

### Access results:

The pipeline returns a `results` object containing analysis outputs and generated figures.

For example, the Lompe model corresponding to the first analysis frame can be accessed as follows:

```python
lompe_model = results.output.lompe_models[0]["model"]

# Example: compute the ground magnetic perturbations
Bground = lompe_model.B_ground()
```

 <!-- # TODO fix that... maybe save lompe differently in lompe_analyss.py
#using 
#  @dataclass
# class LompeFrame:
#     model: lompe.Emodel
#     t0: pd.Timestamp
#     ct: pd.Timestamp
#     t1: pd.Timestamp
#     l1: float
#     l2: float
#     apex: apexpy.Apex

#then do 
# models.append(
#     LompeResult(
#         model=copy.deepcopy(model),
#         t0=t0,
#         ct=ct,
#         t1=t1,
#         l1=l1,
#         l2=l2,
#         apex=apx,
#     )
# )
# so the user can do results.lompe_results[0].model
# does not change anything really... -->

<!-- ### Configuration

SwarmDF runs are controlled via a YAML configuration file.
The config file can be located anywhere, you only need to provide its path:
`swarmdf --config path/to/config.yaml` -->

## Examples

The repository also includes examples to help users get started:
- Jupyter demo notebook: `SwarmDF_demo.ipynb`<br>
- Python script: `SwarmDF_example_script.py`.

Both examples provide a step-by-step walkthrough of the complete SwarmDF workflow, from data retrieval and preprocessing to electrodynamic reconstruction and validation.

## Current status

⚠️ This project is under active development.

### Working features
Data retrieval and preprocessing \
Multi-instrument data integration \
Electrodynamics reconstruction (Lompe) \
Demo script and notebook (/example folder) \
Graphical user interface (/gui folder)

### In progress
Validation tool (LompeOSSE) \
Extended documentation \
Data product descriptions

