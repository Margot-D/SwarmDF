
"""
TODO This file reproduces the SwarmDF run that was created for the paper...
"""

import datetime
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

from swarmdf import *

config = {'satellite ID': 'Swarm A', 'start time': datetime.datetime(2014, 12, 16, 1, 15), 'end time': datetime.datetime(2014, 12, 16, 3, 16), 'DT': 240.0, 'datasets2download': ['swarm_mag', 'superdarn', 'supermag', 'iridium_ampere', 'dmsp_ssies17', 'dmsp_ssies18'], 'conductance method': 'Zang & Paxton model', 'conductance parameters': {'kp': 4.0, 'f107': 100.0, 'background': 2.0}, 'grid parameters': {'L': 1500.0, 'W': 2000.0, 'Lres': 200.0, 'Wres': 200.0, 'wshift': 0.0}, 'regularization parameters': {'l1': 1.0, 'l2': 1.0}, 'gif speed': 550, 'lompeOSSE analysis': 0, 'time offset': 0, 'Gamera snapshot': 0}
# config = {'satellite ID': 'Swarm A', 'start time': datetime.datetime(2014, 12, 15, 1, 15), 'end time': datetime.datetime(2014, 12, 15, 1, 17), 'DT': 30.0, 'datasets2download': ['swarm_mag', 'superdarn', 'supermag', 'iridium_ampere', 'dmsp_ssies17', 'dmsp_ssies18'], 'conductance method': 'Zang & Paxton model', 'conductance parameters': {'kp': 4.0, 'f107': 100.0, 'background': 2.0}, 'grid parameters': {'L': 1500.0, 'W': 2000.0, 'Lres': 200.0, 'Wres': 200.0, 'wshift': 0.0}, 'regularization parameters': {'l1': 1.0, 'l2': 1.0}, 'gif speed': 550, 'lompeOSSE analysis': 0, 'time offset': 0, 'Gamera snapshot': 0}

# Duration of satellite orbit covered by each (animation) frame
timestep = config["DT"] # [s]
start_time = config["start time"]
end_time = config["end time"]

grid_params = config["grid parameters"]

gif_speed = config["gif speed"]

######################
# Collect data
######################

# Path to sample datasets
package_root = Path(__file__).resolve().parents[0]
data_path = str(package_root / "data" / "sample_datasets") + "/" 

# Fetch and load data
datahandler = DataManager(start_time, end_time, config["datasets2download"])
datasets = datahandler.datasets

######################
# Data distrubution and orbit trajectory
######################

lompe_input = LompeInput(config["satellite ID"], start_time, end_time, datasets)
grids, analysis_times = lompe_input.build_grids_around_swarm(timestep, grid_params)
data_objects_per_grid = lompe_input.prepare_lompe_input(grids, analysis_times) 
lompe_input.plot_lompe_input(grids, analysis_times, data_objects_per_grid, gif_speed, show_global_data=True)

######################
# Lompe analysis
######################

SHs, SPs = compute_conductances(config["conductance method"], analysis_times, grids, config["conductance parameters"])

# Build model
l1, l2 = config["regularization parameters"]['l1'], config["regularization parameters"]['l2']
lompe_models = run_lompe(analysis_times, grids, data_objects_per_grid, SHs, SPs, l1, l2)
plot_lompe_output(lompe_models, config["satellite ID"], gif_speed)    


# Example usage:

# models = [entry["model"] for entry in lompe_models]
# model0 = models[0]
# grid = model0.grid_E
# facs = model0.FAC(grid.lon, grid.lat).reshape(grid.lon.shape)

# fac_levels = np.linspace(-1.95, 1.95, 40) * 1e-6 * 2

# fig, ax = plt.subplots(figsize=(8, 8))
# csax1 = cs.CSplot(ax, grid, gridtype='cs')
# csax1.contour(grid.lon, grid.lat, facs, colors='k')
# ax.set_title("")

# Convection velocity from Lompe reconstruction 
Ves, Vns = [], []
models = [entry["model"] for entry in lompe_models]
for model in models:
    Ve = model.Ve
    Vn = model.Vn
    Ves.append(Ve)
    Vns.append(Vn)

# TODO compare with Swarm convection measurements (accessed by doing: datasets['Swarm_conv'] for example)
# Answer the question: is the reconstruction good? (plot correlation or somthg)

# Then re-run SwarmDF for the same time range, but without including Swarm convection measurements; and compare again.
# Answer the question: is the reconstruction still good? 

# If the reconstruction is good either way, then we can assume the lompe reconstruction can be trusted, and we can make maps of average convection using the reconstructed convection

######################
# Validation / LompeOSSE analysis
######################

dolompeosse = config["lompeOSSE analysis"]
if dolompeosse:
    lompeOSSE_models, gamera_models = run_lompeOSSE(lompe_models, config["time offset"], config["Gamera snapshot"])
    plot_lompeOSSE_output(lompeOSSE_models, gamera_models, gif_speed)


