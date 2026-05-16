"""
This example reproduces a typical SwarmDF workflow. 
The `config` object is normally populated directly from 
the user input in the GUI, but its parameters can also 
be edited manually in this script.
"""

import datetime
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from swarmdf.gui.config import SwarmDFConfig

# Uncomment if weird kernel crash
# import matplotlib
# matplotlib.use("TkAgg")

from swarmdf import *

######################
# Input settings
######################  


config = SwarmDFConfig(sat_id='Swarm A',
                       start_time=datetime.datetime(2014, 12, 15, 1, 19),
                       end_time=datetime.datetime(2014, 12, 15, 1, 20),
                       timestep=30.0,
                       datasets2download=['swarm_mag', 'superdarn', 'supermag', 'iridium_ampere', 'dmsp_ssies17', 'dmsp_ssies18'],
                       conductance_method='Zhang & Paxton model',
                       conductance_params={'kp': 4.0, 'f107': 100.0, 'background': 2.0},
                       grid_params={'L': 2000.0, 'W': 1500.0, 'Lres': 200.0, 'Wres': 200.0, 'wshift': 0.0},
                       run_lompe_flag=True,
                       l1=1.0,
                       l2=1.0,
                       speed=550,
                       figw=12.2,
                       figh=9.0,
                       mag=False,
                       show_data=True,
                       run_validation_flag=False,
                       timeoff=0,
                       snapshot=0,
                       generate_script_flag=True)


######################
# Retrieve and load data
######################

datahandler = DataManager(config.start_time, config.end_time, config.datasets2download)
datasets = datahandler.datasets

######################
# Prepare input for Lompe  
######################

# Define individual analysis frames (grid)
lompe_input = LompeInput(config.sat_id, config.start_time, config.end_time, datasets, config.mag)
grids, analysis_times = lompe_input.build_grids_around_swarm(config.timestep, config.grid_params)

# Prepare data objects for each analysis frame
data_objects_per_grid = lompe_input.prepare_lompe_input(grids, analysis_times) 

# Plot input (analysis grids along satellite tracks and data distribution)
input_figs = lompe_input.plot_lompe_input(grids, analysis_times, data_objects_per_grid, figheight=config.figh, figwidth=config.figw, gif_speed=config.speed, show_global_data=config.show_data)

%matplotlib inline
for frame in input_figs:
    plt.figure(figsize=(8, 6))
    plt.imshow(np.array(frame))
    plt.axis("off")
    plt.show()

######################
# Run Lompe analysis (along satellite trajectory)
######################

if config.run_lompe_flag:

    # Conductances
    SHs, SPs = compute_conductances(config.conductance_method, config.conductance_params, analysis_times, grids)

    # Regularization parameters
    l1, l2 = config.l1, config.l2

    # Build Lompe model for each analysis frame
    lompe_models = run_lompe(analysis_times, grids, data_objects_per_grid, SHs, SPs, l1, l2)

    # Plot output (reconstructed electrodynamics)
    output_figs = plot_lompe_output(lompe_models, config.sat_id, figheight=9, gif_speed=config.speed)    

    for frame in output_figs:
        plt.figure(figsize=(8, 6))
        plt.imshow(np.array(frame))
        plt.axis("off")
        plt.show()

######################
# LompeOSSE analysis (validation)
######################

if config.run_validation_flag:
    lompeOSSE_models, gamera_quantities = run_lompeOSSE(lompe_models, config.timeoff, config.snapshot)
    lompeosse_figs, gamera_figs = plot_lompeOSSE_output(lompeOSSE_models, gamera_quantities, figheight=config.figh, gif_speed=config.speed)

    for osse_frame, gamera_frame in zip(lompeosse_figs, gamera_figs):
        fig, ax = plt.subplots(1, 2, figsize=(10, 5))
        ax[0].imshow(np.array(osse_frame))
        ax[0].axis("off")
        ax[1].imshow(np.array(gamera_frame))
        ax[1].axis("off")
        plt.tight_layout()
        plt.show()
    

# # Access individual Lompe model
# models = [entry["model"] for entry in lompe_models]
# model0 = models[0] 

