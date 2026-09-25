import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import copy
import datetime as dt

import matplotlib.gridspec as gridspec
import secsy as cs

from pathlib import Path
import os

import imageio.v2 as imageio
from PIL import Image, ImageOps

import lompe
from lompe.model.visualization import *
from lompeosse import LompeOSSE, GameraData, plot_gamera_lompe_style, validate


# TODO documentation

# Path for saving output files
output_dir = Path.home() / "SwarmDF" / "outputs" # TODO add option for user to choose where?
tmpdir = output_dir / "tmp" #TODO fix to real temporary folder?
# tmpdir.mkdir(parents=True, exist_ok=True)

class LompeOSSECancelled(Exception):
    """Raised when the user cancels the LompeOSSE analysis"""
    pass

def run_lompeOSSE(models, time_offset=0, snapshot=0, cancel_event=None):
    """
    """

    print("Running LompeOSSE validation...")

    osse_models = []
    gamera_outputs = []

    total_frames = len(models)
    i = 1
    for entry in models:

        # cancellation check  
        if cancel_event is not None and cancel_event.is_set():
            raise LompeOSSECancelled

        print(f'Frame {i}/{total_frames} \n')

        model = entry["model"]
        ct = entry["ct"]
        l1 = entry["l1"]
        l2 = entry["l2"]

        hemi = 'NORTH' if model.grid_E.lat.all() > 0 else 'SOUTH'

        # Extract Gamera data
        gamera_output = GameraData(ct, timestep = snapshot, hemisphere = hemi)
        gamera_outputs.append({"gamera_output": copy.deepcopy(gamera_output)})

        # cancellation check  
        if cancel_event is not None and cancel_event.is_set():
            raise LompeOSSECancelled
        
        # Derive synthetic (OSSE) model
        osse_object = LompeOSSE(model, gamera_output)
        osse_model = osse_object.make_OSSE_model(time_offset = time_offset) 

        # cancellation check  
        if cancel_event is not None and cancel_event.is_set():
            raise LompeOSSECancelled
        
        # Run inversion
        osse_model.run_inversion(l1 = l1, l2 = l2)

        # Save osse model for use in plotting function
        osse_models.append({"osse_model": copy.deepcopy(osse_model),
                            "t0": entry["t0"],
                            "t1": entry["t1"],
                            "ct": ct,
                            "apex": entry["apex"],
                            "time_offset": osse_object.time_offset})

        osse_model.clear_model()
        i += 1

    print('Done. Returning LompeOSSE inversion results and Gamera outputs.')

    return osse_models, gamera_outputs


def plot_lompeOSSE_output(osse_models, gamera_outputs, plot_settings):
    """ 
    input: osse models
    output: lompe plot
    explain that the plot of the origianl gamera electrodynamics is considered as ground truth. The lompeOSSE plot can be compared to that ground truth
    """

    lompeosse_png_frames = []
    gamera_png_frames = []
    validation_png_frames = []

    for entry, entry2  in zip(osse_models, gamera_outputs):

        #################
        # LompeOSSE plot
        #################

        osse_model = entry["osse_model"]
        t0 = entry["t0"]
        t1 = entry["t1"]
        ct = entry["ct"]
        apx = entry["apex"]
        toff = entry['time_offset']

        ntime = ct + dt.timedelta(hours=toff)
        
        print("\n Generating LompeOSSE output...")
        print("##", ntime, "##")

        # Save to PNG
        lompeosse_fn = f'lompeosse'
        fn = tmpdir / f"{lompeosse_fn}_{ct:%Y%m%d_%H%M%S}.png" # TODO ct or ntime?
        lompeosse_png_frames.append(fn)

        savekw = {"fname": fn, "dpi": 400}
        suptitle = f"LompeOSSE-reconstructed electrodynamics \n {t0.strftime('%Y-%m-%d %H:%M:%S')}  -  {t1.strftime('%Y-%m-%d %H:%M:%S')}"

        #TODO make that also a routine in lompeosse? maybe not necessary
        fig_lompeosse = lompe.lompeplot(osse_model,include_data=True,
                                        time=ntime, apex=apx,
                                        colorscales={"fac": np.linspace(-2, 2, 40) * 1e-6 * 2,
                                                    "ground_mag": np.linspace(-500, 500, 50) * 1e-9 / 3,
                                                    "hall":       np.linspace(0, 20, 32),
                                                    "pedersen":   np.linspace(0, 20, 32)},
                                        suptitle=suptitle, 
                                        figheight=plot_settings.figh, 
                                        savekw=savekw)

        plt.close(fig_lompeosse)

        #################
        # GAMERA plot 
        #################

        gamera_output = entry2['gamera_output']

        # Save to PNG 
        gamera_fn = f'Gamera'
        fn = tmpdir / f"{gamera_fn}_{ct:%Y%m%d_%H%M%S}.png" 
        gamera_png_frames.append(fn)

        savekw = {"fname": fn, "dpi": 400} #, "bbox_inches":"tight", "pad_inches":0.2
        suptitle = f'Gamera ("truth") electrodynamics \n {t0.strftime("%Y-%m-%d %H:%M:%S")}  -  {t1.strftime("%Y-%m-%d %H:%M:%S")}'
        fig_gamera = plot_gamera_lompe_style(osse_model, gamera_output, ntime, suptitle=suptitle, figheight=plot_settings.figh, savekw=savekw)

        plt.close(fig_gamera)

        #################
        # Validation metrics
        #################

        print("Calculating validation metrics...")

        # Save to PNG 
        validation_fn = f'validation_metrics'
        fn = tmpdir / f"{validation_fn}_{ct:%Y%m%d_%H%M%S}.png"        
        validation_png_frames.append(fn)

        savekw = {"fname": fn, "dpi": 400, "bbox_inches": "tight", "pad_inches": 0.2}
        suptitle = f'Validation of lompe reconstruction'
        fig_validation, _ = validate(osse_model, gamera_output, ct, primary='potential', overlay='fac', suptitle=suptitle, savekw=savekw)

        plt.close(fig_validation)

    print(f"LompeOSSE output and validation figures for each time step saved to the temporary folder: {tmpdir}")

    # Generate GIFs
    if plot_settings.generate_gifs:

        t00 = osse_models[0]["t0"]
        t11 = osse_models[-1]["t1"]
        output_gam = output_dir / f"{gamera_fn}_{t00:%Y%m%d_%H%M%S}-{t11:%Y%m%d_%H%M%S}.gif"
        output_lomp = output_dir / f"{lompeosse_fn}_{t00:%Y%m%d_%H%M%S}-{t11:%Y%m%d_%H%M%S}.gif"
        validation_metrics = output_dir / f"{validation_fn}_{t00:%Y%m%d_%H%M%S}-{t11:%Y%m%d_%H%M%S}.gif"

        with imageio.get_writer(output_lomp, mode="I", duration=plot_settings.gif_speed, loop=0) as writer:
            for frame in lompeosse_png_frames:
                writer.append_data(imageio.imread(frame))

        with imageio.get_writer(output_gam, mode="I", duration=plot_settings.gif_speed, loop=0) as writer:
            for frame in gamera_png_frames:
                writer.append_data(imageio.imread(frame))

        with imageio.get_writer(validation_metrics, mode="I", duration=plot_settings.gif_speed, loop=0) as writer:
            for frame in validation_png_frames:
                writer.append_data(imageio.imread(frame))

        print(f"GIFs saved:\n"
              f"  LompeOSSE: {output_lomp}\n"
              f"  Gamera: {output_gam}\n"
              f"  Validation metrics: {validation_metrics}")

    return lompeosse_png_frames, gamera_png_frames, validation_png_frames