import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import apexpy
import copy
import datetime as dt

from pathlib import Path

import imageio.v2 as imageio

import lompe
from lompe.model.visualization import *
from lompeosse import LompeOSSE, plot_gamera_lompe_style, validate

# Directory for output files 
output_dir = Path.home() / "SwarmDF" / "outputs" # TODO add option for user to choose where?
tmpdir = output_dir / "tmp" #TODO fix to real temporary folder?
# tmpdir.mkdir(parents=True, exist_ok=True)

class LompeOSSECancelled(Exception):
    """Raised the LompeOSSE analysis is cancelled by the user"""
    pass

def run_lompeOSSE(models, time_offset=0, snapshot=0, cancel_event=None):
    """
    Run a sequence of LompeOSSE inversions over multiple analysis grids along a Swarm trajectory. 

    Parameters
    ----------
    models : list of dict
        Lompe models and associated parameters for each time frame.
    time_offset : int
        Time offset in hours relative to the reference time to obtain the LompeOSSE analysis time. Changes the orientation of the Gamera
        pattern relative to the Lompe analysis region.
    snapshot : int
        Gamera simulation snapshot to use.
    cancel_event : threading.Event, optional
        Event used to signal cancellation of the analysis.

    Returns
    -------
    osse_models : list of dict
        LompeOSSE inversion results, the central LompeOSSE analysis time and the start (t0) and end (t1) times of each analysis frame.
    gamera_outputs : list of dict
        Gamera objects corresponding to each analysis frame.

    Notes
    -----
    See https://github.com/Margot-D/lompeOSSE for more extended documentation on LompeOSSE.
    """

    print("Running LompeOSSE analysis...")

    osse_models = []
    gamera_outputs = []

    total_frames = len(models)
    i = 1
    for entry in models:

        print(f'Frame {i}/{total_frames}')

        # Check whether the user cancelled the analysis.
        if cancel_event is not None and cancel_event.is_set():
            raise LompeOSSECancelled

        model = entry["model"]
        ct = entry["ct"]
        l1 = entry["l1"]
        l2 = entry["l2"]
        
        # Generate the synthetic LompeOSSE model
        lompeosse = LompeOSSE(model, event_time=ct, timestep=snapshot, time_offset=time_offset)
        osse_model = lompeosse.synthetic_model

        gamera_output = lompeosse.Gamera_object
        gamera_outputs.append({"gamera_output": copy.deepcopy(gamera_output)})

        # Shift the analysis time frame by time_offset
        t0 = entry["t0"] + dt.timedelta(hours=time_offset)
        t1 = entry["t1"] + dt.timedelta(hours=time_offset)

        # cancellation check  
        if cancel_event is not None and cancel_event.is_set():
            raise LompeOSSECancelled
        
        # Run inversion
        print("LompeOSSE inversion...")
        osse_model.run_inversion(l1 = l1, l2 = l2)
        print('Inversion done.')

        # Save osse model for use in plotting function
        osse_models.append({"osse_model": copy.deepcopy(osse_model),
                            "gamera_time": lompeosse.analysis_time, # LompeOSSE analysis time (new ct)
                            "t0": t0,
                            "t1": t1})

        osse_model.clear_model()
        i += 1

    print('Done. Returning LompeOSSE inversion results and Gamera outputs.')

    return osse_models, gamera_outputs


def plot_lompeOSSE_output(osse_models, gamera_outputs, plot_settings, cancel_event=None):
    """
    Plot LompeOSSE reconstructions, Gamera reference fields and validation metrics for each analysis frame along a Swarm trajectory.

    Parameters
    ----------
    osse_models : list of dict
        LompeOSSE inversion results for each analysis frame.
    gamera_outputs : list of dict
        Gamera objects corresponding to each LompeOSSE model, used as the reference ("truth").
    plot_settings : object
        Plotting settings controlling figure size, GIF generation, and GIF speed.
    cancel_event : threading.Event, optional
        Event used to cancel the plotting.

    Returns
    -------
    lompeosse_png_frames : list of pathlib.Path
        Paths to the LompeOSSE PNG frames.
    gamera_png_frames : list of pathlib.Path
        Paths to the Gamera PNG frames.
    validation_png_frames : list of pathlib.Path
        Paths to the validation metric PNG frames.
    """

    print("Plotting LompeOSSE output and calculating validation metrics...")

    lompeosse_png_frames = []
    gamera_png_frames = []
    validation_png_frames = []

    total_frames = len(osse_models)
    i = 1
    for entry, entry2  in zip(osse_models, gamera_outputs):

        print(f'Frame {i}/{total_frames}')

        # cancellation check  
        if cancel_event is not None and cancel_event.is_set():
            raise LompeOSSECancelled
        
        #################
        # LompeOSSE plot
        #################

        osse_model = entry["osse_model"]
        gtime = entry['gamera_time']
        t0 = entry["t0"]
        t1 = entry["t1"]
        apx = apexpy.Apex(gtime, osse_model.refh)
        
        # Save to PNG
        lompeosse_fn = f'lompeosse'
        fn = tmpdir / f"{lompeosse_fn}_{gtime:%Y%m%d_%H%M%S}.png"
        lompeosse_png_frames.append(fn)

        savekw = {"fname": fn, "dpi": 400}
        suptitle = f"LompeOSSE-reconstructed electrodynamics \n {t0.strftime('%Y-%m-%d %H:%M:%S')}  -  {t1.strftime('%Y-%m-%d %H:%M:%S')}"

        fig_lompeosse = lompe.lompeplot(osse_model,include_data=True,
                                        time=gtime, apex=apx,
                                        colorscales={"fac": np.linspace(-2, 2, 40) * 1e-6 * 2,
                                                    "ground_mag": np.linspace(-500, 500, 50) * 1e-9 / 3,
                                                    "hall":       np.linspace(0, 20, 32),
                                                    "pedersen":   np.linspace(0, 20, 32)},
                                        suptitle=suptitle, 
                                        figheight=plot_settings.figh, 
                                        savekw=savekw)

        plt.close(fig_lompeosse)

        # cancellation check  
        if cancel_event is not None and cancel_event.is_set():
            raise LompeOSSECancelled
        
        #################
        # Plot the original Gamera electrodynamics as the reference ("truth") in a lompe-style plot

        #################

        gamera_output = entry2['gamera_output']

        # Save to PNG 
        gamera_fn = f'Gamera'
        fn = tmpdir / f"{gamera_fn}_{gtime:%Y%m%d_%H%M%S}.png" 
        gamera_png_frames.append(fn)

        savekw = {"fname": fn, "dpi": 400} #, "bbox_inches":"tight", "pad_inches":0.2
        suptitle = f'Gamera ("truth") electrodynamics \n {t0.strftime("%Y-%m-%d %H:%M:%S")}  -  {t1.strftime("%Y-%m-%d %H:%M:%S")}'
        fig_gamera = plot_gamera_lompe_style(osse_model, gamera_output, suptitle=suptitle, figheight=plot_settings.figh, savekw=savekw)

        plt.close(fig_gamera)

        # cancellation check  
        if cancel_event is not None and cancel_event.is_set():
            raise LompeOSSECancelled
        
        #################
        # Compare the LompeOSSE reconstruction with the Gamera reference
        #################

        # Save to PNG 
        validation_fn = f'validation_metrics'
        fn = tmpdir / f"{validation_fn}_{gtime:%Y%m%d_%H%M%S}.png"        
        validation_png_frames.append(fn)

        savekw = {"fname": fn, "dpi": 400, "bbox_inches": "tight", "pad_inches": 0.2}
        suptitle = f'Validation of lompe reconstruction'
        fig_validation, _ = validate(osse_model, gamera_output, primary='potential', overlay='fac', suptitle=suptitle, savekw=savekw)

        plt.close(fig_validation)

        i += 1

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