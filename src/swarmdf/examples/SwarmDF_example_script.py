"""
This example reproduces a typical SwarmDF workflow. 
The `config` object is normally populated directly from 
the user input in the GUI, but its parameters can also 
be edited manually in this script.

Turn demo on to skip data download
and use the example event instead.
"""

import datetime
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from swarmdf.config import SwarmDFConfig
from swarmdf import *

matplotlib.rcParams['figure.dpi'] = 300

## Uncomment if weird kernel crash
# matplotlib.use("TkAgg")

######################
# Input settings
######################  

demo = True # set to True to turn demo on

config = SwarmDFConfig(sat_id='Swarm A',
                       start_time=datetime.datetime(2014, 12, 15, 1, 19),
                       end_time=datetime.datetime(2014, 12, 15, 1, 20),
                       timestep=30.0,
                       datasets2download=['swarm_mag', 'superdarn', 'supermag', 'iridium_ampere', 'dmsp_ssies17', 'dmsp_ssies18'],
                       conductance_method='Zhang & Paxton model',
                       conductance_params={'kp': 4.0, 'f107': 100.0, 'background': 2.0},
                       grid_params={'L': 2000.0, 'W': 1500.0, 'Lres': 200.0, 'Wres': 200.0, 'wshift': 0.0},
                       run_lompe_flag=True,
                       regularization_l1=1.0,
                       regularization_l2=1.0,
                       gif_speed=550,
                       figw=12.2,
                       figh=9.0,
                       mag_coords_flag=False,
                       show_all_data_flag=True,
                       run_validation_flag=False,
                       time_offset=0,
                       snapshot=0,
                       demo_flag=demo)

######################
# Retrieve and load data
######################

datahandler = DataManager(config.start_time, config.end_time, config.datasets2download, config.demo_flag)
datasets = datahandler.datasets

######################
# Prepare input for Lompe  
######################

# Define individual analysis frames (grid)
lompe_input = LompeInput(config.sat_id, config.start_time, config.end_time, datasets, config.mag_coords_flag)
grids, analysis_times = lompe_input.build_grids_around_swarm(config.timestep, config.grid_params)

# Prepare data objects for each analysis frame
data_objects_per_grid = lompe_input.prepare_lompe_input(grids, analysis_times) 

# Plot input (analysis grids along satellite tracks and data distribution)
input_figs = lompe_input.plot_lompe_input(grids, analysis_times, data_objects_per_grid, config.figh, config.figw, config.gif_speed, show_global_data=config.show_all_data_flag)

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
    l1, l2 = config.regularization_l1, config.regularization_l2

    # Build Lompe model for each analysis frame
    lompe_models = run_lompe(analysis_times, grids, data_objects_per_grid, SHs, SPs, l1, l2)

    # Plot output (reconstructed electrodynamics)
    output_figs = plot_lompe_output(lompe_models, config.sat_id, config.figh, config.gif_speed)    

    for frame in output_figs:
        plt.figure(figsize=(8, 6))
        plt.imshow(np.array(frame))
        plt.axis("off")
        plt.show()

######################
# LompeOSSE analysis (validation)
######################

if config.run_validation_flag:
    lompeOSSE_models, gamera_quantities = run_lompeOSSE(lompe_models, config.time_offset, config.snapshot)
    lompeosse_figs, gamera_figs = plot_lompeOSSE_output(lompeOSSE_models, gamera_quantities, config.figh, config.gif_speed)

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

