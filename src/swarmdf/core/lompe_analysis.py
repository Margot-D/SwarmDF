"""
SwarmDF Toolbox — Lompe analysis module

"""

import numpy as np
import apexpy
import matplotlib.pyplot as plt
import pandas as pd 
import datetime as dt
import copy
import tempfile
import os 
from pathlib import Path

import lompe
from lompe.utils.time import yearfrac_to_datetime 

import imageio.v2 as imageio
from PIL import Image, ImageOps

package_root = Path(__file__).resolve().parents[1]  
src_root = package_root.parent  
outputs_path = str(src_root / "outputs")
tmpdir = outputs_path + '/tmp/' #TODO fix

# TODO the lompe analys is is currently not using the Swarm data correctly. Fix that with Fasil
# TODO check with Kalle if it's super important that the time intervals are the same in swamr trajectory and lompe analysis (right now there's a 5sec difference)
# TODO find better name for lompe_fn
# TODO fix docu 

def run_lompe(center_times, DT, grids, datasets, SHs, SPs, l1=1, l2=1):
    """
    Run Lompe analysis for all grids and return Tkinter PhotoImage frames for GIF animation.

    start_time and end_time define the total interval. we define sub-intervals of length DT

    Returns:
        Dictionnary of Lompe models with time and apex parameters, as well as regularization parameters
    """

    epoch = center_times[0].year
    # epoch = start_time.year
    time = yearfrac_to_datetime([epoch])
    apx = apexpy.Apex(time[0].year)

    # # Time step edges of analysis interval
    # times = pd.date_range(start=start_time, end=end_time, freq=f'{DT}S', tz=None)

    # # Central times for each time step
    # center_times = times[:-1] + pd.to_timedelta(DT/2, unit='s')

    # Extract Swarm dataset (used to define the limits of the analysis interval)
    df = datasets['swarm']
    df = df[df['Spacecraft'] == 'A']

    models = []

    print(f"Running Lompe analysis (l1={l1:.2f}, l2={l2:.2f})") 

    for grid, SH, SP, ct in zip(grids, SHs, SPs, center_times):

        # New center time based on Swarm dataset (to match with swarm_orbit_and_grid script)
        idx = df.index.get_loc(ct, method='nearest')
        ct_swarm = df.index[idx]

        # Limits of analysis interval (based on Swarm dataset)
        t0 = df.index[df.index.get_loc(ct_swarm - dt.timedelta(seconds = DT/2), method = 'nearest')]
        t1 = df.index[df.index.get_loc(ct_swarm + dt.timedelta(seconds = DT/2), method = 'nearest')]

        # Build model
        user_model = lompe.Emodel(grid, Hall_Pedersen_conductance = (SH, SP))

        # Prepare data for Lompe inversion
        data_objects = prepare_data(datasets, t0, t1)
    
        if len(data_objects) == 0:
            raise RuntimeError("No valid data available for Lompe inversion")

        # Add data
        for data_obj in data_objects.values():
            user_model.add_data(data_obj)

        # Run inversion
        user_model.run_inversion(l1=l1, l2=l2)

        models.append({"model": copy.deepcopy(user_model),
                        "t0": t0,
                        "t1": t1,
                        "ct": ct_swarm,
                        "apex": apx,
                        "l1":l1,
                        "l2":l2})
        
        user_model.clear_model()

    return models

def lompe_output(models, gif_speed):
    """
    Gives Lompe plot for each grid frame along Swarm trajectory

    Returns: 
        (PNG image for each time step)
        (GIF animation saved on disk)
        list of PIL images for animation in GUI    
    """

    temp_filenames = []
    frames_pil = []

    for entry in models:
        user_model = entry["model"]
        t0 = entry["t0"]
        t1 = entry["t1"]
        ct = entry["ct"]
        apx = entry["apex"]
        l1 = entry["l1"]
        l2 = entry["l2"]

        # Lompe plot
        fig = lompe.lompeplot(user_model, 
                              include_data=True, time=ct, apex=apx,
                              colorscales={"fac": np.linspace(-2, 2, 40) * 1e-6 * 2,
                                          "ground_mag": np.linspace(-500, 500, 50) * 1e-9 / 3,
                                          "hall":       np.linspace(0, 20, 32),
                                          "pedersen":   np.linspace(0, 20, 32)},
                              quiverscales={"ground_mag":      600e-9,
                                           "space_mag_fac":    600e-9,
                                           "space_mag_full":   600e-9,
                                           "electric_current": 1})

        fig.suptitle(f"{t0.strftime('%Y-%m-%d %H:%M:%S')} - {t1.strftime('%Y-%m-%d %H:%M:%S')}",
                fontsize=22, color="black", y=0.98)
        
        # Save to PNG
        lompe_fn = f'lompe_l1-{l1}_l2-{l2}'
        fn = os.path.join(tmpdir, f"{lompe_fn}_{t0.strftime('%Y%m%d_%H%M%S')}.png")
        fig.savefig(fn, dpi=400, pad_inches=0.2)
        temp_filenames.append(fn)

        # Convert figure to PIL (chatGPT) (used for the UI GIF)
        fig.canvas.draw()
        width, height = fig.canvas.get_width_height()
        buf = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8).reshape((height, width, 4))[:, :, 1:4]  # reorder to RGB
        pil_img = Image.fromarray(buf)
        pil_img = ImageOps.expand(pil_img, border=15, fill="white")
        frames_pil.append(pil_img.copy())

        # plt.show()
        plt.close(fig)

    print(f"Lompe output figures for each time step saved in temporary folder: {tmpdir}")

    # Path to save the GIF
    output = outputs_path + f"/{lompe_fn}.gif"

    with imageio.get_writer(output, mode="I", duration=gif_speed) as writer:
        for frame in frames_pil:
            writer.append_data(np.array(frame))  # convert PIL → numpy

    print(f"GIF saved in outputs directory: {output}") # TODO fix path to indicate the user directory 

    return frames_pil

# decide which prepare_data function i want to keep
def prepare_data(datasets, window_start, window_end):
    """
    Prepare data for lompe

    datasets: list of dataset types
    swarm_B, swarm_E, superdarn, supermag, iridium_ampere, dmps_ssies17, dmsp_ssies18

    Returns data objects ready to use for Lompe analysis
    """
    
    lompe_data_dict = {}
    t0, t1 = window_start, window_end

    for key, df in datasets.items():

        if key in ['swarm']:
            continue
    
        elif key in ['swarm_mag']: 
            
            # Magnetic field data from all three Swarm satellite
            sub = df.loc[t0:t1, :].dropna()
            sub = sub[np.abs(sub.Latitude) > 50] 
            
            if sub.empty:
                # print(f'{key} is empty')
                continue

            values = np.vstack((sub.B_e.values, sub.B_n.values, sub.B_u.values)) *1e-9
            coords = np.vstack((sub.Longitude.values, sub.Latitude.values, sub.Radius.values))
            LOS = None
            datatype = 'space_mag_fac' 
            iweight = 0.5 #1.0
            error = 30e-9

        elif key in ['swarm_efield']: #TODO check/fix everything

            print('! need to fix Swarm elec function in prepare_data')

            # Electric field data from all three Swarm satellite
            
            sub = df.loc[t0:t1, :].dropna()
            sub = sub[np.abs(sub.Latitude) > 50]

            if sub.empty:
                # print(f'{key} is empty')
                continue
                
            values = np.vstack((sub.Evx.values, sub.Evy.values, sub.Evz.values)) # TODO need fasil/spencer to fix that
            coords = np.vstack((sub.Longitude.values, sub.Latitude.values, sub.Radius.values))
            LOS = None
            datatype = 'efield' 
            iweight = 1.0
            error = 10e-9

        # Superdarn
        elif key in ['superdarn']:
            sub = df.loc[(df.index >= t0) & (df.index <= t1) & (df.vlos < 2000)].dropna()
            sub = sub[np.abs(sub.glat) > 50]

            if sub.empty:
                # print(f'{key} is empty')
                continue

            values = sub['vlos'].values
            coords = np.vstack((sub['glon'].values, sub['glat'].values))
            LOS = np.vstack((sub['le'].values, sub['ln'].values))     
            datatype = 'convection'
            iweight = 1.0
            error = 50

        # DMSP/SSIES 17
        elif key in ['dmsp_ssies17']: #TODO fix
            sub = df.loc[t0:t1, :].dropna()
            sub = sub[np.abs(sub.gdlat) > 50]

            if sub.empty:
                # print(f'{key} is empty')
                continue
        
            values = np.abs(sub.hor_ion_v).values
            coords = np.vstack((sub.glon.values, sub.gdlat.values)) 
            LOS = np.vstack((sub['le'].values, sub['ln'].values))
            datatype = 'convection'
            iweight = 1.0
            error = 50

        # DMSP/SSIES 18
        elif key in ['dmsp_ssies18']: #TODO fix
            sub = df.loc[t0:t1,:].dropna()
            sub = sub[np.abs(sub.glat) > 50]

            if sub.empty:
                # print(f'{key} is empty')
                continue
            
            values = np.abs(sub.hor_ion_v).values
            coords = np.vstack((sub.glon.values, sub.glat.values)) #glat or gdlat??
            LOS = np.vstack((sub['le'].values, sub['ln'].values))
            datatype = 'convection'
            iweight = 1.0
            error = 50

            # Add large error for F18 poor measurements
            if key == 'dmsp_ssies18' and 'vyqual' in sub.columns:
                error_array = np.zeros(len(sub))
                error_array[sub.vyqual > 2] = 10000
                error = error_array

        # SuperMAG
        elif key in ['supermag']:
            sub = df[df.lat <= 90].loc[t0:t1].dropna()  # TODO what is that for?
            sub = sub[np.abs(sub.lat) > 50]

            if sub.empty:
                # print(f'{key} is empty')
                continue

            values = np.vstack((sub.Be.values, sub.Bn.values, sub.Bu.values)) *1e-9 # from nT to T
            coords = np.vstack((sub.lon.values, sub.lat.values))            
            LOS = None
            datatype = 'ground_mag'
            iweight = 1.0 # or 0.4 ??
            error = 10e-9

        # Iridium/AMPERE
        elif key in ['iridium_ampere']:
            sub = df[(df.time >= t0) & (df.time <= t1)].dropna()
            sub = sub[np.abs(sub.lat) > 50]
            
            if sub.empty:
                # print(f'{key} is empty')
                continue

            values = np.vstack((sub.B_e.values, sub.B_n.values, sub.B_r.values)) *1e-9
            coords = np.vstack((sub.lon.values, sub.lat.values, sub.r.values))
            LOS = None
            datatype = 'space_mag_fac'
            iweight = 1.0
            error = 30e-9

        # Create Lompe Data object
        # print(f'Adding {datatype} to data objects for Lompe inversion')
        lompe_data_dict[key] = lompe.Data(values, coords, LOS=LOS, datatype=datatype, iweight=iweight, error=error)

    return lompe_data_dict


