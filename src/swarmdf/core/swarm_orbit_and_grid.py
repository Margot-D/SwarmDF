"""
SwarmDF Toolbox — Orbit and grid setup

This script downloads Swarm satellite trajectory data for a user-defined time range and satellite ID.
It also sets up the 2D ionospheric grid based on user-defined parameters and generates an animation 
of the satellite track over the grid. This visualization helps illustrate the sampling geometry 
used in the electrodynamics reconstruction.
"""

import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import datetime as dt
from polplot import Polarplot
from secsy import spherical, CSgrid, CSprojection, CSplot
import pandas as pd
import apexpy
import tempfile
import os 
from pathlib import Path

import imageio.v2 as imageio
from PIL import Image

# Earth and ionospheric radii
RE = 6371.2 # Earth radius (km)
h = 110 # height of the ionosphere (km)
RI = RE + h # Ionospheric radius (km)

# For vector calculations
d2r = np.pi / 180

# # VirES client token
# set_token(url="https://vires.services/ows",
#           token="efd9D_HBXj8SetBQxN-CbDYt8fX58Nxi")
# request = SwarmRequest()

# TODO fix Swarm trajectory shifted (not plotted at the grid center) except when grid is super small
# TODO fix temporary directory
# TODO find better name for swarm_fn
# TODO fix documentation 

package_root = Path(__file__).resolve().parents[1]  
src_root = package_root.parent  
outputs_path = str(src_root / "outputs")
tmpdir = outputs_path + '/tmp/' #TODO fix to real temporary folder?

def swarm_trajectory(sat_id, start_time, end_time, DT, grid_parameters, datasets, gif_speed, show_data=True):
    """
    Returns a plot of the Swarm trajectory, the analysis grid along the trajectory.
    Polar plot
    Cubed sphere plot that has the size of the grid, shows the Swarm trajectory and the data distribution within the grid.

    Returns: 
        list of analysis grids along Swarm trajectory 
        (PNG image for each time step)
        (GIF animation saved on disk)
        list of PIL images for animation in GUI
    """

    # tmpdir = 'outputs/tmp/' #TODO fix that

    epoch = start_time.year
    time = dt.datetime(epoch, 1, 1)
    # apx = apexpy.Apex(time, refh=h)

    # -------------- #
    # Get Swarm trajectory and analysis grid frames

    all_swarm_data = datasets['swarm'] 

    # Keep data within time range of interest
    start = pd.to_datetime(start_time)
    end = pd.to_datetime(end_time)
    df_all = all_swarm_data.loc[start:end, :]

    df_all.rename(columns={"Latitude": "swarm_lat", "Longitude": "swarm_lon"}, inplace=True) # TODO is that the geographic geodetic coords?
    # df.rename(columns={"QDLat": "swarm_lat", "QDLon": "swarm_lon"}, inplace=True) # TODO is that the geographic geodetic coords?
    # print(df.head())

    # Hemisphere
    hem = 'north' if df_all['swarm_lat'].all() > 0 else 'south'
    print('hemisphere:', hem)
    hemi = True if hem == 'north' else False

    # Selected satellite
    swarm_sat = sat_id[-1] #A, B or C
    df = df_all[df_all['Spacecraft'] == swarm_sat]
    
    # Keep high latitudes only
    df = df[np.abs(df['swarm_lat'] > 50)] if hemi else df[np.abs(df['swarm_lat'] < -50)]
    
    # Satellite velocity (use geographic geodetic coordinates for that) # TODO (check viresclient for te, tn). 
    te, tn = spherical.tangent_vector(df['swarm_lat'][:-1].values, 
                                    df['swarm_lon'][:-1].values,
                                    df['swarm_lat'][1: ].values, 
                                    df['swarm_lon'][1: ].values)

    df['ve'] = np.hstack((te, np.nan))
    df['vn'] = np.hstack((tn, np.nan))

    # Time step edges of analysis interval
    times = pd.date_range(start=start_time, end=end_time, freq=f'{DT}S', tz=None)

    # Central times for each time step
    center_times = times[:-1] + pd.to_timedelta(DT/2, unit='s')

    grids = []
    frames_pil = []

    print(f'Generating Swarm{swarm_sat} trajectory animation for each time step...')
    # with tempfile.TemporaryDirectory() as tmpdir:

    # Loop through each time step
    for ct in center_times: 

        # Index of central point of analysis interval in dataset (df)
        idx = df.index.get_loc(ct, method='nearest')
        ct_data = df.index[idx]
        
        # Spacecraft position and velocity at central point
        sc_ve0, sc_vn0 = np.array((df.loc[ct_data, 've'], df.loc[ct_data, 'vn']))
        sc_lat0 = df.loc[ct_data, 'swarm_lat'] 
        sc_lon0 = df.loc[ct_data, 'swarm_lon']

        # Limits of analysis interval
        t0 = df.index[df.index.get_loc(ct - dt.timedelta(seconds = DT/2), method = 'nearest')]
        t1 = df.index[df.index.get_loc(ct + dt.timedelta(seconds = DT/2), method = 'nearest')]
        
        # print('ct', ct)
        # print('ct_data', ct_data)
        # print('t0, t1', t0, t1)

        #TODO potentially: fix the fact that, here, i'm using both ct_data AND ct which are not exactly the same. In Lompe I'm using ct

        # Unit vectors pointing at satellite (Cartesian vectors)
        rs = []
        for t in [t0, ct_data, t1]:
            # print('t',t)
            rs.append(np.array([np.cos(df.loc[t, 'swarm_lat'] * d2r) * np.cos(df.loc[t, 'swarm_lon'] * d2r),
                                np.cos(df.loc[t, 'swarm_lat'] * d2r) * np.sin(df.loc[t, 'swarm_lon'] * d2r),
                                np.sin(df.loc[t, 'swarm_lat'] * d2r)]))

        # Slice of the satellite trajectory for this time step
        segment = df.loc[t0:t1] # not doing that means plotting the whole trajectory (betwen start and end times)

        # Grid object
        grid = get_grid(sc_lon0, sc_lat0, sc_ve0, sc_vn0, grid_parameters, rs)
        grids.append(grid)

        # xi0, eta0 = grid.projection.geo2cube(sc_lon0, sc_lat0)
        # print(xi0, eta0) # if 0,0: the grid is EXACTLY centered on the satellite

        ##########################

        fig = plt.figure(figsize = (22,12), constrained_layout=True)
        fig.suptitle(f"{t0.strftime('%Y-%m-%d %H:%M:%S')}  -  {t1.strftime('%Y-%m-%d %H:%M:%S')}",
            fontsize=28, color="black", y=0.98)
        
        axs = {}
        axs['polar'] = fig.add_subplot(121)
        axs['zoom'] = fig.add_subplot(122)

        # POLAR PLOT
        axs['polar'] = Polarplot(axs['polar' ], minlat=50, plotgrid=True, linewidth=1.5, color='grey')
        textargs = {'fontsize':26, 'color':'grey'}
        axs['polar']. writeLTlabels(lat=49, **textargs)
        axs['polar']. writeLATlabels(lt=7 , **textargs)
        plot_kwargs = {'color':'darkgrey', 'zorder':2}
        # axs['polar'].coastlines(time=time, mag=apexpy.Apex(time, 0), resolution='110m', **plot_kwargs, north=hemi) # coastlines in magnetic coordinates
        axs['polar'].coastlines(time, resolution='110m', **plot_kwargs, north=hemi) # coastlines in geographic coordinates

        # Grid frame outline (in black)
        xs = (grid.lon_mesh[0, :], grid.lon_mesh[-1, :], grid.lon_mesh[:, 0], grid.lon_mesh[:, -1]) # geographic
        ys = (grid.lat_mesh[0, :], grid.lat_mesh[-1, :], grid.lat_mesh[:, 0], grid.lat_mesh[:, -1]) # geographic
        outlineargs = {'color':'black', 'zorder':8}
        for i, c in enumerate(zip(xs, ys)):
            lon, lat = c
            axs['polar'].plot(lat, lon/15, linewidth = 3 if i == 0 else 1, **outlineargs) # geographic
            
            # mlat, mlon = apx.geo2apex(lat, lon, h) # h* 1e-3 # to MLAT/MLT coordinates
            # mlt = apx.mlon2mlt(mlon, time)
            # axs['polar'].plot(mlat, mlt, linewidth = 3 if i == 0 else 1, **outlineargs) # magnetic

        # CUBED SPHERE
        axs['zoom'].cla()
        csax0 = CSplot(axs['zoom'], grid, gridtype='geo') #"gridtype='geo'"
        csax0.add_coastlines(color='darkgrey')
        axs['zoom'].spines['bottom'].set_linewidth(5) # bottom of grid frame 

        # # Plot satellite tracks on polar axis (use magnetic QD or apex (almost the same) and mlt)
        # mlat_sat, mlon_sat = apx.geo2apex(df['swarm_lat'].values, df['swarm_lon'].values, h) # h* 1e-3 # Apex coordinates
        # # mlat_sat, mlon_sat = df['QDLat'].values, df['QDLon'].values # QD coordinates
        # mlt_sat = apx.mlon2mlt(mlon_sat, time)
        # axs['polar'].plot(mlat_sat, mlt_sat, color='red', linewidth=2, zorder=3) # magnetic

        # Plot all Swarm satellite trajectories as thin lightred lines
        SwarmA = df_all[df_all['Spacecraft'] == 'A']
        SwarmB = df_all[df_all['Spacecraft'] == 'B']
        SwarmC = df_all[df_all['Spacecraft'] == 'C']

        axs['polar'].plot(SwarmA['swarm_lat'], (SwarmA['swarm_lon']/15) % 24, color='lightcoral', linewidth=1.5, zorder=1) # geographic
        axs['polar'].plot(SwarmB['swarm_lat'], (SwarmB['swarm_lon']/15) % 24, color='lightcoral', linewidth=1.5, zorder=1) # geographic
        axs['polar'].plot(SwarmC['swarm_lat'], (SwarmC['swarm_lon']/15) % 24, color='lightcoral', linewidth=1.5, zorder=1) # geographic

        csax0.plot(SwarmA['swarm_lon'], SwarmA['swarm_lat'], color='lightcoral', alpha=0.4, linewidth=1.5) 
        csax0.plot(SwarmB['swarm_lon'], SwarmB['swarm_lat'], color='lightcoral', alpha=0.4, linewidth=1.5) 
        csax0.plot(SwarmC['swarm_lon'], SwarmC['swarm_lat'], color='lightcoral', alpha=0.4, linewidth=1.5) 

        # Plot selected Swarm satellite trajectory as thick red line
        lat_sat = df['swarm_lat']
        lt_sat = (df['swarm_lon']/15) % 24
        axs['polar'].plot(lat_sat, lt_sat, color='red', linewidth=2, zorder=1) # geographic

        csax0.plot(df['swarm_lon'], df['swarm_lat'], color='red', linewidth=2) 

        # csax0.plot(segment['swarm_lon'], segment['swarm_lat'])
        # axs['polar'].plot(segment['swarm_lat'], (segment['swarm_lon']/15)%24)

        # ------------ #
        # Plot data distribution

        if show_data == True: # TODO remove? don't we always want to show the data coverage?

            for dataset in datasets:
                # TODO: add more data... dmsp?
                try: 
                    if dataset == 'superdarn': # plot SuperDARN in green

                        sd = datasets['superdarn'].loc[t0:t1, :]

                        axs['polar'].scatter(sd.glat.values, sd.glon.values/15, c = 'C2', s = 10, marker = '.')
                        csax0.scatter(sd.glon.values, sd.glat.values, c='C2', s=150, marker='^')

                        # mlat, mlon = apx.geo2apex(sd.glat.values, sd.glon.values, h)
                        # mlt = apx.mlon2mlt(mlon, time)
                        # axs['polar'].scatter(mlat, mlt, c = 'C2', s = 10, marker = '.')

                    if dataset == 'supermag': # plot SuperMAG in orange

                        smag = datasets['supermag'].loc[t0:t1, :]
                        smag = smag[smag.lat > 50] if hemi else smag[smag.lat < -50]
                        
                        axs['polar'].plotpins(np.abs(smag.lat.values), smag.lon.values/15, smag.Bn.values, smag.Be.values,
                                    SCALE = 100, markersize = 10, markercolor ='C1', linewidths = .5, colors ='C1', unit = 'nT')

                        csax0.scatter(smag.lon.values, smag.lat.values, s=100, color="C1", marker='o')
                        csax0.quiver(smag.Be.values, smag.Bn.values, smag.lon.values, smag.lat.values, width=0.002, headwidth=3, color='C1')
                        
                        # mlat, mlon = apx.geo2apex(smag.lat.values, smag.lon.values, h)
                        # mlt = apx.mlon2mlt(mlon, time)
                        # axs['polar'].plotpins(mlat, mlt, smag.Be.values, smag.Bn.values, 
                        #             SCALE = 100, markersize = 10, markercolor = 'C1', linewidths = .5, colors = 'C1', unit = 'nT')
                        
                    if dataset == 'iridium_ampere': # plot Iridium/AMPERE in blue

                        iridium = datasets['iridium_ampere']
                        irid = iridium[(iridium.time >= t0) & (iridium.time <= t1)]
                        irid = irid[irid.lat > 50] if hemi else irid[irid.lat < -50]

                        axs['polar'].plotpins(np.abs(irid.lat.values), irid.lon.values/15, irid.B_n.values, irid.B_e.values, 
                                    SCALE = 100, markersize = 10, markercolor ='C0', linewidths = .5, colors ='C0', unit = 'nT')

                        csax0.scatter(irid.lon.values, irid.lat.values, s=100, color='C0', marker='o')
                        csax0.quiver(irid.B_e.values, irid.B_n.values, irid.lon.values, irid.lat.values, width=0.002, color='C0', scale=400) 
                        
                        # csax0.scatter(x, y, s=100, color="C0", marker='o')

                        # mlat, mlon = apx.geo2apex(irid.lat.values, irid.lon.values, h)
                        # mlt = apx.mlon2mlt(mlon, time)
                        # axs['polar'].plotpins(mlat, mlt, irid.B_e.values, irid.B_n.values, 
                        #             SCALE = 100, markersize = 10, markercolor = 'C0', linewidths = .5, colors = 'C0', unit = 'nT')

                    if dataset == 'swarm_mag': # plot Swarm mag in purple

                        swmag = datasets['swarm_mag'].loc[t0:t1, :] # magnetic field data from all three Swarm satellites

                        axs['polar'].scatter(swmag.Latitude.values, swmag.Longitude.values/15, c = 'purple', s = 10, marker = '.')
                        csax0.scatter(swmag.Longitude.values, swmag.Latitude.values, c='purple', s=200, marker='.')

                        # mlat, mlon = apx.qd2apex(sw.QDLat.values, sw.QDLon.values, h)
                        # mlt = apx.mlon2mlt(mlon, time)
                        # axs['polar'].scatter(mlat, mlt, c = 'purple', s = 10, marker = '.')

                    if dataset == 'swarm_efield': # plot Swarm elec in cyan

                        swelec = datasets['swarm_efield'].loc[t0:t1, :] # electric field data from all three Swarm satellites
                        print(swelec)

                        axs['polar'].scatter(swelec.Latitude.values, swelec.Longitude.values/15, c = 'k', s = 10, marker = '.')
                        csax0.scatter(swelec.Longitude.values, swelec.Latitude.values, c='violet', s=200, marker='p')

                        # mlat, mlon = apx.qd2apex(sw.QDLat.values, sw.QDLon.values, h)
                        # mlt = apx.mlon2mlt(mlon, time)
                        # axs['polar'].scatter(mlat, mlt, c = 'k', s = 10, marker = '.')

                except Exception as e:
                    print(f"Failed to show {dataset} data distribution:", e)

        # Save to PNG
        swarm_fn = f'swarm{swarm_sat}_and_data'
        fn = os.path.join(tmpdir, f"{swarm_fn}_{t0.strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(fn, dpi=400, pad_inches=0.2)  # NO bbox_inches='tight'

        # Convert figure to PIL (chatGPT) (used for the UI GIF)
        fig.canvas.draw()
        width, height = fig.canvas.get_width_height()
        buf = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8).reshape((height, width, 4))[:, :, 1:4]  # reorder to RGB
        pil_img = Image.fromarray(buf)
        frames_pil.append(pil_img.copy())

        plt.show() #TODO remove eventually
        plt.close(fig)

    print(f"Figures with Swarm trajectory, grid, and data distribution for each time step saved in: {tmpdir}")

    # Save GIF
    output = outputs_path + f"/{swarm_fn}.gif" # TODO fix path to indicate the user directory 

    with imageio.get_writer(output, mode="I", duration=gif_speed) as writer:
        for frame in frames_pil:
            writer.append_data(np.array(frame))  # convert PIL → numpy

    print(f"GIF saved in outputs directory: {output}") 

    return grids, frames_pil # returns PIL image


def get_grid(sc_lon0, sc_lat0, sc_ve0, sc_vn0, grid_params, rs):
    """
    Function that returns a grid object aligned with satellite trajectory in the center
    
    grid is in xi, eta coords
    """

    position = (sc_lon0, sc_lat0) # center of the grid
    orientation = (sc_vn0, -sc_ve0) # aligns coordinate system such that xi axis points right wrt satellite velocity vector, and eta along velocity
    projection = CSprojection(position, orientation)
    L, W, Lres, Wres = grid_params # user-defined [km]

    # TODO ask kalle what wshift and W are for
    wshift = 0 # shift the grid center wres km in cross-track direction
    # W = W + RI * np.arccos(np.sum(rs[0]*rs[-1])) * 1e-3 # dimensions across analysis region/grid (km)
    grid = CSgrid(projection, L*1e3, W*1e3, Lres*1e3, Wres*1e3, wshift = wshift, R = RI*1e3) # Lompe takes things in SI units (i.e., meters in this case)
    
    return grid