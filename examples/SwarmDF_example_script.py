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
from PIL import Image 

from swarmdf.config import SwarmDFConfig, SwarmDFPlotSettings
from swarmdf.pipeline import *
from swarmdf import *

matplotlib.rcParams['figure.dpi'] = 300

## Uncomment if weird kernel crash
# matplotlib.use("TkAgg")

######################
# Input settings
######################  

is_demo = False # set to True to use example configuration and sample datasets

config = SwarmDFConfig(sat_id='Swarm C',
                       start_time=datetime.datetime(2014, 12, 15, 1, 15),
                       end_time=datetime.datetime(2014, 12, 15, 1, 20),
                       timestep=30.0,
                       datasets2download=['swarm_mag', 'superdarn', 'supermag', 'iridium_ampere', 'dmsp_ssies17', 'dmsp_ssies18'],
                       conductance_method='Hardy model',
                       conductance_params={'kp': 4, 'f107': 100.0, 'background': 2.0},
                       grid_params={'L': 2000.0, 'W': 1500.0, 'Lres': 80.0, 'Wres': 80.0, 'wshift': 0.0},
                       run_lompe_flag=True,
                       regularization_l1=1.0,
                       regularization_l2=1.0,
                       run_validation_flag=False,
                       time_offset=0,
                       snapshot=0)

plot_settings = SwarmDFPlotSettings(figh=9.0,
                                    mag_coords_flag=True,
                                    show_all_data_flag=True,
                                    gif_speed=550,
                                    generate_input_plots=True, 
                                    generate_gifs=False)


######################
# Retrieve and load data
######################

datasets = get_data(config, is_demo)

######################
# Prepare input for Lompe  
######################

swarmdf_input = compute_swarmdf_input(datasets, config)

if plot_settings.generate_input_plots:
    input_figs = render_swarmdf_input(swarmdf_input, plot_settings)

    %matplotlib inline
    for input_fig in input_figs:
        plt.figure(figsize=(8, 6))
        plt.imshow(Image.open(input_fig))
        plt.axis("off")
        plt.show()

######################
# Run Lompe analysis (along satellite trajectory)
######################

if config.run_lompe_flag:

    swarmdf_output = compute_swarmdf_output(swarmdf_input, config)

    output_figs = render_swarmdf_output(swarmdf_output, plot_settings)   

    for output_fig in output_figs:
        plt.figure(figsize=(8, 6))
        plt.imshow(Image.open(output_fig))
        plt.axis("off")
        plt.show()

######################
# LompeOSSE analysis (validation)
######################

if config.run_validation_flag and config.run_lompe_flag is not None:

    swarmdf_validation = compute_swarmdf_validation(swarmdf_output, config)

    lompeosse_figs, gamera_figs = render_swarmdf_validation(swarmdf_validation, plot_settings)

    for lompeosse_fig, gamera_fig in zip(lompeosse_figs, gamera_figs):
        fig, ax = plt.subplots(1, 2, figsize=(10, 5))
        ax[0].imshow(Image.open(lompeosse_fig))
        ax[0].axis("off")
        ax[1].imshow(Image.open(gamera_fig))
        ax[1].axis("off")
        plt.tight_layout()
        plt.show()
    

# # Access individual Lompe model
# lompe_models = swarmdf_output.lompe_models
# models = [entry["model"] for entry in lompe_models]
# model0 = models[0] 
