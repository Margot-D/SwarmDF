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
If you already have Lompe installed, you may still need the following dependencies:
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

For a quick start, run the built-in demo using sample datasets:
```bash
swarmdf --demo
```

### Graphical user interface (recommended)
```bash
swarmdf-gui
```

### Command-line interface
Run a full SwarmDF analysis using a configuration file:<br>
```bash
swarmdf --config path/to/config.yaml
```

## Python interface

SwarmDF can also be used directly from Python, which allows full control over the workflow and direct access to results and plots.

### Run a demo analysis
```python
from swarmdf.config import SwarmDFConfig, SwarmDFPlotSettings
from swarmdf.pipeline import *

config = SwarmDFConfig.default()
plot_settings = SwarmDFPlotSettings()

results = run_swarmdf_pipeline(config=config, plot_settings=plot_settings, use_sample_data=True)
```
### Access results and plots:

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

<!-- ### Configuration

SwarmDF runs are controlled via a YAML configuration file.
The config file can be located anywhere, you only need to provide its path:
`swarmdf --config path/to/config.yaml` -->

## Examples

The repository also includes examples to help users get started:
- Jupyter demo notebook: `SwarmDF_demo.ipynb`<br>
- Python script: `SwarmDF_example_script.py`

These provide a walkthrough of the full SwarmDF workflow. 


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

