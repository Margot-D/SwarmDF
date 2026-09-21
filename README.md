# Swarm Data Fusion (SwarmDF)

SwarmDF is a Python tool designed to automate the full workflow for analysing high-latitude ionospheric electrodynamics using multi-instrument observations.

## Overview

SwarmDF uses the [Lompe technique](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2022JA030356) to combine measurements from Swarm satellites with complementary datasets (SuperMAG, SuperDARN, Iridium/AMPERE, DMSP/SSIES) and reconstruct two-dimensional maps of ionospheric electrodynamics along a user-defined Swarm trajectory. SwarmDF incorporates the [LompeOSSE](https://github.com/Margot-D/lompeOSSE) tool to enable validation of the Lompe reconstruction against synthetic data.

For supported datasets, SwarmDF **automatically** downloads the required data for the selected time interval and then runs the complete analysis pipeline, from data processing through to the Lompe reconstruction and optional validation.

### Key features:
- End-to-end automated workflow
- Multi-instrument data fusion
- Electrodynamics reconstruction using [Lompe](https://github.com/klaundal/lompe) 
- Built-in validation using [LompeOSSE](https://github.com/Margot-D/lompeOSSE) 
- User-friendly graphical interface and Python API

## Installation

### System prerequisites

SwarmDF requires Python 3.11 or newer. 

SwarmDF also depends on ApexPy (a Python wrapper for Apex coordinates), which uses Fortran code. Depending on your system, installing ApexPy may require a Fortran compiler and runtime.

For the most reliable installation, we recommend installing the required compilers before installing SwarmDF.

On macOS and Windows, if you are using Conda, you can install the compilers with: 
<!-- check if it works on windows! -->

```bash
conda install conda-forge::compilers
```

On Ubuntu/Debian-based Linux systems:

```bash
sudo apt install gcc gfortran python3.11-dev
```

Replace `3.11` with your Python version (e.g. `python3.12-dev` for Python 3.12).

### Install SwarmDF

#### On macOS and Windows

We recommend installing SwarmDF in a dedicated Conda environment:

```bash
git clone https://github.com/Margot-D/SwarmDF.git
cd <path/to/SwarmDF>

conda create -n swarmdf python=3.11
conda activate swarmdf

pip install .
```

#### On Linux 

There is evidence of rendering issues with CustomTkinter (used for the SwarmDF graphical user interface) on some Linux systems when using Conda environments. For the best GUI compatibility, we recommend using a standard Python venv environment instead of a Conda environment on Linux.

On Ubuntu/Debian-based systems:

```bash
git clone https://github.com/Margot-D/SwarmDF.git
cd <path/to/SwarmDF>  

python3 -m venv swarmdf
source swarmdf/bin/activate

pip install .
```

The `pip install .` command installs SwarmDF and all of its required Python dependencies automatically.

SwarmDF can be installed in any compatible Python environment. However, using a dedicated environment is recommended to avoid dependency conflicts with other packages.


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
swarmdf --config <path/to/config.yaml>
```
An example configuration files is provided in the examples directory.

Optional advanced plotting settings can be provided through a separate configuration file. If omitted, default plotting settings are used.

```bash
swarmdf --config <path/to/config.yaml> --plot-config <path/to/plot_settings.yaml>
```

## Python interface

SwarmDF can also be used directly from Python, which allows full control over the workflow and direct access to results and plots.

### Run a demo analysis:

The following example runs SwarmDF using the default configuration and sample data:

```python
from swarmdf.config import SwarmDFConfig, SwarmDFPlotSettings
from swarmdf.pipeline import *

config = SwarmDFConfig.default()  
plot_settings = SwarmDFPlotSettings.default() 

results = run_swarmdf_pipeline(config=config, plot_settings=plot_settings, use_sample_data=True)
```

The default configuration provides the parameters required for a complete SwarmDF analysis, but does not include LompeOSSE validation of the Lompe reconstruction.
To enable validation in demo mode, replace the `config` line in the previous script with:

```python
from dataclasses import replace
config = replace(SwarmDFConfig.default(), run_validation_flag=True)
```

To run a custom analysis, set `use_sample_data=False` and configure the desired analysis and plotting parameters using `SwarmDFConfig` and `SwarmDFPlotSettings` (see, for example, `SwarmDF_example_script.py` in the example directory).


### Access results

The pipeline returns a `SwarmDFResults` object containing the analysis results and paths to the generated plot frames. 
Individual plot frames are saved to ~/SwarmDF/outputs/tmp. If GIF generation is enabled, the resulting GIFs are saved to ~/SwarmDF/outputs.

The main components are:

* `results.input` — input data and information used to construct the Lompe analysis, including the Swarm passes, analysis grids, analysis times, and processed data objects.
* `results.output` — Lompe reconstruction results, including the reconstructed Lompe models.
* `results.validation` — LompeOSSE validation results, including the LompeOSSE models and corresponding Gamera output. This is `None` if validation is disabled.
* `results.plots` — paths to the generated input, output, and validation plot frames.

For example:

```python
results.input.grids
results.output.lompe_models
results.validation.lompeosse_models
results.plots.output_frames
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
Validation tool (LompeOSSE) \
Demo script and notebook (/example folder) \
Graphical user interface (app.py in /gui folder)

### In progress
Extended documentation \
Data product descriptions

