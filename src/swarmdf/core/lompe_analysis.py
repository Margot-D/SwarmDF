"""
SwarmDF — Lompe analysis module

Runs a Lompe analysis using the inputs from lompe_input.py

"""

import numpy as np
import matplotlib.pyplot as plt
import apexpy
import copy
import tempfile
import os 
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import lompe
from lompe.utils.time import yearfrac_to_datetime 
from .lompe_input import QUIVERSCALES

import imageio.v2 as imageio
from PIL import Image, ImageOps

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Path for saving output files
package_root = Path(__file__).resolve().parents[3]
output_dir = package_root / "outputs"
tmpdir = output_dir / "tmp" #TODO fix to real temporary folder?

# TODO fix the lon_label thing again 

def run_lompe(time_bounds, grids, data_objects_per_grid, SHs, SPs, l1=1, l2=1):
    """
    Run Lompe analysis for all grids and return Tkinter PhotoImage frames for GIF animation.

    start_time and end_time define the total interval. we define sub-intervals of length DT

    Returns:
        Dictionnary of Lompe models with time and apex parameters, as well as regularization parameters
    """

    epoch = time_bounds['ct'][0].year
    time = yearfrac_to_datetime([epoch])
    apx = apexpy.Apex(time[0].year)

    models = []

    print(f"Running Lompe analysis (l1={l1:.2f}, l2={l2:.2f})...") 

    for grid, SH, SP, ct, t0, t1, data_objects in zip(grids, SHs, SPs, time_bounds['ct'], time_bounds['t0'], time_bounds['t1'], data_objects_per_grid):

        # Build model
        user_model = lompe.Emodel(grid, Hall_Pedersen_conductance = (SH, SP))

        # Add data
        for data_obj in data_objects.values():
            user_model.add_data(data_obj)

        # Run inversion
        user_model.run_inversion(l1=l1, l2=l2)
        
        models.append({"model": copy.deepcopy(user_model),
                        "t0": t0,
                        "ct": ct,
                        "t1": t1,
                        "apex": apx,
                        "l1":l1,
                        "l2":l2})
        
        user_model.clear_model()

    return models

def plot_lompe_output(models, sat_id, figheight=9, gif_speed=550):
    """
    Gives Lompe plot for each grid frame along Swarm trajectory

    Returns: 
        (PNG image for each time step)
        (GIF animation saved on disk)
        list of PIL images for animation in GUI    
    """

    frames_pil = []

    for entry in models:
        user_model = entry["model"]
        t0 = entry["t0"]
        t1 = entry["t1"]
        ct = entry["ct"]
        apx = entry["apex"]
        l1 = entry["l1"]
        l2 = entry["l2"]

        # Save to PNG
        fn = f'lompe_sw{sat_id[-1]}'
        fn_ct = tmpdir / f"{fn}_{ct:%Y%m%d_%H%M%S}.png"
        savekw = {"fname": fn_ct, "dpi": 400}

        # Lompe plot
        fig = lompe.lompeplot(user_model, 
                              include_data=True, time=ct, apex=apx,
                              colorscales={"fac": np.linspace(-2, 2, 40) * 1e-6 * 2,
                                          "ground_mag": np.linspace(-500, 500, 50) * 1e-9 / 3,
                                          "hall":       np.linspace(0, 20, 32),
                                          "pedersen":   np.linspace(0, 20, 32)},
                            #   quiverscales={"ground_mag":      600e-9,
                            #                "space_mag_fac":    600e-9,
                            #                "space_mag_full":   600e-9,
                            #                "electric_current": 1}
                                quiverscales = QUIVERSCALES,
                                figheight = figheight,
                                savekw=savekw)

        fig.suptitle(f"{t0.strftime('%Y-%m-%d %H:%M:%S')} - {t1.strftime('%Y-%m-%d %H:%M:%S')}",
                fontsize=22, color="black", y=0.98)
        
        fig.subplots_adjust(left=0.08, right=0.95, hspace=.8, wspace=0.2)

        # Save PNG (with title)
        fig.savefig(fn_ct, dpi=400)

        # Convert figure to PIL (used for the UI GIF)
        fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
        pil_img = Image.fromarray(buf)
        pil_img = ImageOps.expand(pil_img, border=15, fill="white")
        frames_pil.append(pil_img.copy())

        plt.close(fig)

    print(f"Lompe output figures for each time step saved in temporary folder: {tmpdir}")

    # Path to save the GIF
    t00 = models[0]["t0"]
    t11 = models[-1]["t1"]
    fn_time = output_dir / f"{fn}_{t00:%Y%m%d_%H%M%S}-{t11:%Y%m%d_%H%M%S}.gif"
    output = fn_time

    # output = output_dir / f"{lompe_fn}.gif"

    with imageio.get_writer(output, mode="I", duration=gif_speed, loop=0) as writer:
        for frame in frames_pil:
            writer.append_data(np.array(frame))  # convert PIL → numpy

    print(f"GIF saved in outputs directory: {output}")

    return frames_pil


