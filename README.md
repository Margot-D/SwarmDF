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

### Getting started 
We recommend running `SwarmDF_GUI.py`, which provides a graphical user interface and does not require prior knowledge of the code structure. 

Alternatively, you can run:
- the demo notebook (`SwarmDF_demo.ipynb`), or 
- the example Python script (`SwarmDF_example_script.py`).

These provide a walkthrough of the full workflow. 

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


## Installation

SwarmDF can be installed by cloning the repository: `git clone https://github.com/Margot-D/SwarmDF.git`

### Dependencies 

SwarmDF requires several external Python packages.
If you already have Lompe installed, you may still need the following dependencies:
`pip install customtkinter tkcalendar imageio pillow`

SwarmDF also integrates LompeOSSE (under development) as a built-in validation tool:
`git clone https://github.com/Margot-D/lompe_osse.git` (not functional yet)

### Environment setup (recommended)

An environment file (swarmdf_environment.yml) is provided to install all dependencies automatically, including Lompe and LompeOSSE:
`conda env create -f environment.yml`


