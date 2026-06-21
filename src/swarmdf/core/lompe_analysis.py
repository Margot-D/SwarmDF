"""
SwarmDF — Lompe analysis module
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
import apexpy
import copy
from pathlib import Path
import imageio.v2 as imageio

import lompe
from lompe.utils.time import yearfrac_to_datetime 
from .lompe_input import QUIVERSCALES

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Path for saving output files
package_root = Path(__file__).resolve().parents[3]
output_dir = package_root / "outputs"
tmpdir = output_dir / "tmp" #TODO switch to real temporary folder?

def run_lompe(grids, time_bounds, data_objects_per_grid, SHs, SPs, l1=1, l2=1): #TODO remove default values?
    """
    Run a sequence of Lompe inversions over multiple analysis grids and time intervals.

    Returns
    -------
    dict
        Dictionary containing Lompe models (TODO ok?) and associated metadata for subsequent analysis and visualization
    """

    epoch = time_bounds['ct'][0].year
    time = yearfrac_to_datetime([epoch])
    apx = apexpy.Apex(time[0].year)

    models = []

    print(f"Running Lompe analysis (l1={l1:.2f}, l2={l2:.2f})...") #TODO remove regul parameters from print?

    total_frames = len(grids)
    i = 1
    for grid, SH, SP, ct, t0, t1, data_objects in zip(grids, SHs, SPs, time_bounds['ct'], time_bounds['t0'], time_bounds['t1'], data_objects_per_grid):

        print(f'Frame {i}/{total_frames}')

        # Build model
        model = lompe.Emodel(grid, Hall_Pedersen_conductance = (SH, SP))

        # Add data
        for data_obj in data_objects.values():
            model.add_data(data_obj)

        # Run inversion
        model.run_inversion(l1=l1, l2=l2)
        
        models.append({"model": copy.deepcopy(model),
                        "t0": t0,
                        "ct": ct,
                        "l1": l1, # useful for LompeOSSE run 
                        "l2": l2, # useful for LompeOSSE run 
                        "t1": t1,
                        "apex": apx})
        
        model.clear_model()
        i += 1
    
    print('Done. Returning Lompe inversion results.')

    return models

def plot_lompe_output(models, sat_id, plot_settings):
    """
    Plot Lompe results for each analysis interval, and optionally, generate GIF animation.

    Returns
    -------
    list[str]
        Paths to the generated PNG images.
    """

    print('Plotting Lompe output...')
    
    png_frames = []

    for entry in models:
        user_model = entry["model"]
        t0 = entry["t0"]
        t1 = entry["t1"]
        ct = entry["ct"]
        apx = entry["apex"]

        # Save to PNG
        fn = f'lompe_sw{sat_id[-1]}'
        fn_ct = tmpdir / f"{fn}_{ct:%Y%m%d_%H%M%S}.png"
        png_frames.append(fn_ct)
        savekw = {"fname": fn_ct, "dpi": 400}

        # Lompe plot
        suptitle = f"{t0.strftime('%Y-%m-%d %H:%M:%S')} - {t1.strftime('%Y-%m-%d %H:%M:%S')}"
        fig = lompe.lompeplot(user_model, 
                              include_data=True, time=ct, apex=apx,
                              colorscales={"fac": np.linspace(-2, 2, 40) * 1e-6 * 2,
                                          "ground_mag": np.linspace(-500, 500, 50) * 1e-9 / 3,
                                          "hall":       np.linspace(0, 20, 32),
                                          "pedersen":   np.linspace(0, 20, 32)},
                                quiverscales = QUIVERSCALES,
                                suptitle = suptitle,
                                figheight = plot_settings.figh,
                                savekw=savekw)

        plt.close(fig)

    print(f"Lompe output figures for each time step saved in temporary folder: {tmpdir}")

    # Generate GIF
    if plot_settings.generate_gifs:

        t00 = models[0]["t0"]
        t11 = models[-1]["t1"]
        fn_time = output_dir / f"{fn}_{t00:%Y%m%d_%H%M%S}-{t11:%Y%m%d_%H%M%S}.gif"
        output = fn_time

        with imageio.get_writer(output, mode="I", duration=plot_settings.gif_speed, loop=0) as writer:
            for frame in png_frames:
                writer.append_data(imageio.imread(frame))

        print(f"GIF saved in outputs directory: {output}")

    return png_frames


