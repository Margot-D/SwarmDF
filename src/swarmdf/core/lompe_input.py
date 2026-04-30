"""
SwarmDF — Lompe input preparation module

Builds and visualizes inputs for Lompe analysis.

"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch
import datetime
from polplot import Polarplot
from secsy import spherical, CSgrid, CSprojection, CSplot
import pandas as pd
import os 
from pathlib import Path
import apexpy
import dipole # github.com/klaundal/dipole
import warnings
# warnings.simplefilter("always")
from collections import defaultdict

import tkinter as tk
from tkinter import messagebox
import imageio.v2 as imageio
from PIL import Image, ImageOps

import lompe 

# Earth radius
RE = 6371.2 # [km] 
HEIGHT = 110 # ionosphere height # TODO: Check that it is consistent throughout

# Path for saving output files
package_root = Path(__file__).resolve().parents[1]  
src_root = package_root.parent  
outputs_path = str(src_root / "outputs")
tmpdir = outputs_path + '/tmp/' #TODO fix to real temporary folder?

# Vector scales (all SI units) #TODO use the same quiverscales when plotting lompe stuff in lompe_analysis.py 
QUIVERSCALES = {'ground_mag':       600 * 1e-9 , # ground magnetic field scale [T]
                'space_mag_fac':    200 * 1e-9 , # FAC magnetic field scale [T] # 600 * 1e-9
                'convection':       1000       , # convection velocity scale [m/s] # 2000
                'efield':           100  * 1e-3, # electric field scale [V/m]
                'electric_current': 1000 * 1e-3, # electric surface current density [A/m] Ohm's law 
                'secs_current':     1000 * 1e-3, # electric surface current density [A/m] SECS 
                'space_mag_full':   600 * 1e-9 } # FAC magnetic field scale [T]

class LompeInput:
    """
    Prepare Lompe input from multi-instrument datasets by:
        - extracting relevant segments of a Swarm trajectory
        - constructing analysis grids along the track
        - preparing data objects for inversion

    Parameters
    ----------
    sat_id : str
        Swarm satellite identifier (e.g. 'SwarmA', 'SwarmB', 'SwarmC').    
    start_time : datetime-like
        Start of the user-defined time interval used to generate analysis
        center times. The actual data extraction window extends beyond this
        time to ensure full satellite passes and grid coverage.
    end_time : datetime-like
        End of the user-defined time interval used to generate analysis
        center times. The actual data extraction window may extend beyond
        this time depending on the selected grids and data availability.
    datasets : dict
        Dictionary of pandas DataFrames containing all datasets.
        Keys correspond to dataset names (e.g. 'swarm_mag', 'superdarn').
    """

    def __init__(self, sat_id, start_time, end_time, datasets, mag_coords=False):

        self.sat_id = sat_id
        self.start_time = start_time
        self.end_time = end_time
        self.mid_time = self.start_time + (self.end_time - self.start_time) / 2 # interpreting this as the time of the current snapshot
        self.datasets = datasets

        self.mag = mag_coords
        self.apx = apexpy.Apex(self.start_time.year, refh = HEIGHT)
        self.dpl = dipole.Dipole(self.start_time.year)

        # Select Swarm data within an extended time window (ensures full satellite pass is captured) and assign pass IDs per spacecraft
        window_start = pd.to_datetime(start_time) - pd.to_timedelta(45, 'm')
        window_end   = pd.to_datetime(end_time)   + pd.to_timedelta(45, 'm')

        swarm = datasets['swarm_mag'].loc[window_start:window_end].copy()
        #TODO find out what the problem is here? 
        self.all_swarm = swarm.groupby('Spacecraft', group_keys=False).apply(self.add_pass_id)
                
        # User-selected satellite only
        self.one_swarm = self.all_swarm[self.all_swarm['Spacecraft'] == sat_id[-1]]

    def _scatter(self, pax, lat, lon, **kwargs):
        """ scatter plot in polar coordinates, converting to magnetic if necessary """

        if self.mag: # convert to magnetic and plot
            mlat, mlon = self.apx.geo2apex(lat.to_numpy(), lon.to_numpy(), HEIGHT)
            mlt = self.dpl.mlon2mlt(mlon, self.mid_time)
            pax.scatter(mlat, mlt, **kwargs)
        else: # plot in geographic
            lt = lon/15
            pax.scatter(lat, lt, **kwargs)

    # TODO fix this now
    def _plotpins(self, pax, lat, lon, east, hemisign, north, **kwrds):
        """ plot pins in polar coords, converting to magnetic if necessary """

        if self.mag: # convert coordinates and components to magnetic and plot
            f1, f2 = self.apx.basevectors_qd(lat, lon, HEIGHT, coords = 'geo')
            f1 = f1 / np.linalg.norm(f1, axis = 0) # normalize
            f2 = f2 / np.linalg.norm(f2, axis = 0)
            mlat, mlon = self.apx.geo2apex(lat, lon, HEIGHT)
            mlt = self.dpl.mlon2mlt(mlon, self.mid_time)
            east = f1[0] * east + f1[1] * north
            north = f2[0] * east + f2[1] * north
            pax.plotpins(np.abs(mlat), mlt, north*hemisign, east, **kwrds)
        else: # keep geographic
            lt = lon/15
            pax.plotpins(np.abs(lat), lt, north*hemisign, east, **kwrds)


    # ------------------------------------------------------------------
    # Swarm pass handling # TODO put that in datadownloader I think
    # ------------------------------------------------------------------

    def add_pass_id(self, df): 
        """
        Assign pass IDs to a polar-orbiting satellite trajectory.

        A new pass is defined when the satellite crosses the equator
        (i.e., changes hemisphere).

        Parameters
        ----------
        df : pandas.DataFrame
            Satellite data sorted by time.

        Returns
        -------
        pandas.DataFrame
            DataFrame with an added 'pass_id' column.
        """

        df = df.sort_index().copy()

        lat = df['Latitude'].values

        # Hemisphere sign (+1 north, -1 south)
        hemi = np.sign(lat)
        hemi[hemi == 0] = np.nan
        hemi = pd.Series(hemi).ffill().bfill().values

        # Detect hemisphere transitions
        pass_id = np.zeros(len(df), dtype=int)
        changes = np.where(np.diff(hemi) != 0)[0] + 1

        for idx in changes:
            pass_id[idx:] += 1

        df['pass_id'] = pass_id

        return df

    def get_current_pass(self, df, time):
        """
        Extract the satellite pass closest to a given time.

        Parameters
        ----------
        df : pandas.DataFrame
            Satellite dataset with 'pass_id'.
        time : datetime-like
            Reference time.

        Returns
        -------
        current_pass : pandas.DataFrame
            Data corresponding to the selected pass.
        pass_id : int
            Identifier of the selected pass.
        """
               
        df = df.sort_index()

        idx = df.index.get_indexer([time], method='nearest')[0]
        pid = df.iloc[idx]['pass_id']

        current_pass = df[df['pass_id'] == pid]

        return current_pass, pid
    
    # ------------------------------------------------------------------
    # Grid construction
    # ------------------------------------------------------------------

    def build_grids_around_swarm(self, dt, grid_params):
        """
        Construct analysis grids along the Swarm trajectory.

        Grids are centered along the satellite track and aligned
        with its velocity vector.

        Parameters
        ----------
        dt : float
            Time step between grids [seconds].
        grid_params : dict
            Grid definition (all values in km):
                - L, W : grid dimensions
                - Lres, Wres : resolution
                - wshift : horizontal cross-track shift of the grid center

        Returns
        -------
        grids : list
            List of grid objects.
        analysis_times : dict
            Dictionary with keys ['ct', 't0', 't1']:
                - ct : grid center times
                - t0, t1 : time bounds of data inside grid
        """

        # Estimate satellite velocity (use geographic geodetic coordinates for that) # TODO check viresclient for te, tn? 
        te, tn = spherical.tangent_vector(self.one_swarm['Latitude'][:-1].values, 
                                        self.one_swarm['Longitude'][:-1].values,
                                        self.one_swarm['Latitude'][1: ].values, 
                                        self.one_swarm['Longitude'][1: ].values)

        self.one_swarm['ve'] = np.hstack((te, np.nan))
        self.one_swarm['vn'] = np.hstack((tn, np.nan))

        # Time sampling
        times = pd.date_range(start=self.start_time, end=self.end_time, freq=f'{dt}S', tz=None)
        
        # Grid centers
        center_times = times[:-1] + pd.to_timedelta(dt/2, unit='s')

        grids = []
        analysis_times = {'ct':[], 't0': [], 't1': []}

        # with tempfile.TemporaryDirectory() as tmpdir:

        # Loop over time steps
        for ct in center_times: 

            # Nearest available satellite timestamp
            idx = self.one_swarm.index.get_loc(ct, method='nearest') #TODO make nearest the point before instead of after?
            ct_swarm = self.one_swarm.index[idx]
            
            # Spacecraft position and velocity at center
            sc_lat0 = self.one_swarm.loc[ct_swarm, 'Latitude'] 
            sc_lon0 = self.one_swarm.loc[ct_swarm, 'Longitude']
            sc_ve0, sc_vn0 = np.array((self.one_swarm.loc[ct_swarm, 've'], self.one_swarm.loc[ct_swarm, 'vn']))

            # Grid object centered on center time
            grid = self.get_grid(sc_lon0, sc_lat0, sc_ve0, sc_vn0, grid_params)

            # Reject low-latitude grids
            skipped = 0
            if np.min(np.abs(grid.lat)) < 48:
                # print(f"Grid centered at {grid.projection.lat0:.2f}° latitude extends equatorward of |48|°, skipping")
                skipped += 1
                continue

            # Determine data time bounds within grid
            swarm_pass, _ = self.get_current_pass(self.one_swarm, ct_swarm)
            mask = grid.ingrid(swarm_pass.Longitude.values, swarm_pass.Latitude.values) 
            swarm_inside_grid = swarm_pass.loc[mask] # portion of the Swarm trajectory that falls inside the grid
            t0, t1 = swarm_inside_grid.index[0], swarm_inside_grid.index[-1]

            print(f'Time interval around Swarm center time ({ct_swarm}): {t0} - {t1}') #TODO remove eventually?

            grids.append(grid)
            analysis_times['ct'].append(ct_swarm)
            analysis_times['t0'].append(t0)
            analysis_times['t1'].append(t1)

        if skipped > 0:
            print(f"Skipped {skipped} low-latitude grid(s) (extending equatorward of |48|°)") #TODO remove?

        if not grids:
            msg = "⚠️ No valid grids were created. Try a different time interval."
            show_error_popup(msg)
            raise RuntimeError(msg)
        
        return grids, analysis_times
    
    def get_grid(self, sc_lon, sc_lat, sc_ve, sc_vn, grid_params, RI=RE+HEIGHT): #TODO RI OK?
        """
        Create a cubed-sphere grid aligned with satellite motion.

        Parameters
        ----------
        sc_lon, sc_lat : float
            Grid center coordinates.
        sc_ve, sc_vn : array-like
            Satellite velocity (east, north).
        grid_params : dict
            Grid definition in km.

        Returns
        -------
        grid : CSgrid
            Grid object to be used in Lompe (in xi, eta coordinates)
        """

        position = (sc_lon, sc_lat) # grid center
        orientation = (sc_vn, -sc_ve) # aligns coordinate system such that xi axis points right wrt satellite velocity vector, and eta along velocity
        projection = CSprojection(position, orientation)
        grid = CSgrid(projection, grid_params["L"]*1e3, grid_params["W"]*1e3, grid_params["Lres"]*1e3, grid_params["Wres"]*1e3, wshift = grid_params["wshift"]*1e3, R = RI*1e3) # in [m]

        return grid

    # ------------------------------------------------------------------
    # Lompe data preparation
    # ------------------------------------------------------------------

    def prepare_lompe_input(self, grids, time_bounds):
        """
        Build Lompe data objects for each grid.

        Parameters
        ----------
        grids : list
            List of grid objects.
        time_bounds : dict
            Output from build_grids_around_swarm.

        Returns
        -------
        list
            List of dictionaries containing Lompe Data objects.
        """

        data_per_grid = []

        for grid, t0, t1 in zip(grids, time_bounds['t0'], time_bounds['t1']):

            data_objects = self.make_data_objects(self.datasets, grid, t0, t1)

            if len(data_objects) == 0:
                raise RuntimeError("No valid data available for Lompe inversion.")
            
            data_per_grid.append(data_objects)
        
        return data_per_grid
    
    def make_data_objects(self, datasets, grid, t0, t1): 
        """
        Build Lompe Data objects for all datasets within a grid and time interval.

        Parameters
        ----------
        datasets : dict
            Dictionary of pandas DataFrames keyed by dataset name.
        grid : CSgrid
            Analysis grid.
        t0, t1 : datetime-like
            Time interval for data selection.

        Returns
        -------
        dict
            Dictionary of lompe.Data objects keyed by dataset name.
            Only datasets with valid data inside the grid are included.
        """
        
        data_objects_for_lompe = {}

        for key, df in datasets.items():
        
            # Magnetic field data from Swarm satellites (A, B and C)
            if key in ['swarm_mag']: 

                sub = df.loc[t0:t1]
                sub = sub[grid.ingrid(sub.Longitude, sub.Latitude)]

                if sub.empty:
                    # print(f'{key} is empty')
                    continue

                values = np.vstack((sub.B_e.values, sub.B_n.values, sub.B_u.values)) * 1e-9
                coords = np.vstack((sub.Longitude.values, sub.Latitude.values, sub.Radius.values))
                LOS = None
                datatype = 'space_mag_fac' 
                iweight = 0.5 #1.0
                error = 30e-9

            # Electric field data from Swarm satellites (A, B and C)
            elif key in ['swarm_efield']: #TODO check/fix everything

                print('! need to fix Swarm elec function in prepare_data')

                sub = df.loc[t0:t1]
                sub = sub[grid.ingrid(sub.Longitude, sub.Latitude)]

                if sub.empty:
                    continue
                    
                values = np.vstack((sub.Evx.values, sub.Evy.values, sub.Evz.values))
                coords = np.vstack((sub.Longitude.values, sub.Latitude.values, sub.Radius.values))
                LOS = None
                datatype = 'efield' 
                iweight = 1.0
                error = 10e-9

            # Ground magnetometer data from SuperMAG 
            elif key in ['supermag']:

                sub = df.loc[t0:t1]
                sub = sub[grid.ingrid(sub.lon, sub.lat)]

                if sub.empty:
                    continue

                values = np.vstack((sub.Be.values, sub.Bn.values, sub.Bu.values)) * 1e-9 # from nT to T
                coords = np.vstack((sub.lon.values, sub.lat.values))            
                LOS = None
                datatype = 'ground_mag'
                iweight = 1.0 # or 0.4 ??
                error = 10e-9

            # Convection data from SuperDARN
            elif key in ['superdarn']:

                sub = df[(df.index >= t0) & (df.index <= t1)]
                sub = sub[(grid.ingrid(sub.glon, sub.glat)) & (sub.vlos < 2000)] 

                if sub.empty:
                    continue

                values = sub['vlos'].values
                coords = np.vstack((sub['glon'].values, sub['glat'].values))
                LOS = np.vstack((sub['le'].values, sub['ln'].values))     
                datatype = 'convection'
                iweight = 1.0
                error = 50

            # Convection data from DMSP/SSIES (F17 & F18)
            elif key in ['dmsp_ssies17', 'dmsp_ssies18']:

                sub = df.loc[t0:t1]
                sub = sub[grid.ingrid(sub.glon, sub.gdlat)]

                if sub.empty:
                    continue

                values = np.abs(sub.hor_ion_v).values
                coords = np.vstack((sub.glon.values, sub.gdlat.values)) 
                LOS = np.vstack((sub['le'].values, sub['ln'].values))
                datatype = 'convection'
                iweight = 1.0
                error = 100

                # # Add large error for F18 poor measurements
                # if key == 'dmsp_ssies18' and 'vyqual' in sub.columns:
                #     error_array = np.zeros(len(sub))
                #     error_array[sub.vyqual > 2] = 10000
                #     error = error_array

            # Magnetometer data from Iridium/AMPERE
            elif key in ['iridium_ampere']:

                sub = df[(df.time >= t0) & (df.time <= t1)]
                sub = sub[grid.ingrid(sub.lon, sub.lat)]

                if sub.empty:
                    continue

                values = np.vstack((sub.B_e.values, sub.B_n.values, sub.B_r.values)) * 1e-9
                coords = np.vstack((sub.lon.values, sub.lat.values, sub.r.values))
                LOS = None
                datatype = 'space_mag_fac'
                iweight = 1.0
                error = 30e-9

            # Create and store Lompe data object for each dataset
            data_objects_for_lompe[key] = lompe.Data(values, coords, LOS=LOS, datatype=datatype, iweight=iweight, error=error)

        return data_objects_for_lompe
    
    # ------------------------------------------------------------------
    # Plotting input (data and grids)
    # ------------------------------------------------------------------

    def _init_figure(self, t0, t1):
        """Create figure and base axes."""

        fig = plt.figure(figsize = (12.2,9), constrained_layout=True) #(22,12) 12,9
        fig.suptitle(f"{t0.strftime('%Y-%m-%d %H:%M:%S')}  -  {t1.strftime('%Y-%m-%d %H:%M:%S')}",
                        fontsize=22, color="black", y=0.98)
        
        axs = {"polar": fig.add_subplot(121), "zoom": fig.add_subplot(122)}
        
        return fig, axs
    
    def _setup_plot_frames(self, axs, grid, hem): #TODO decide if I want to keep magnetic coordinate stuff, if not remove comments
        """Configure polar and cubed-sphere axes. Write labels. Plot coastlines and grid outline."""
        
        nh = True if hem == 'north' else False
        coords = 'magnetic' if self.mag else 'geographic'

        textargs = {'fontsize':18, 'color':'grey'}
        outlineargs = {'color':'black', 'zorder':8}

        # --------------- # 
        # POLAR PLOT

        axs['polar'] = Polarplot(axs['polar'], minlat=50, plotgrid=True, linewidth=0.8, color='grey')
        axs['polar'].writeLTlabels(lat=49, degrees = not self.mag, **textargs)
        axs['polar'].coastlines(resolution='110m', color='darkgrey', zorder=2, north=nh, mag = self.apx if self.mag else None)
        axs['polar'].ax.text(0.5, 0.85, f"Polar projection (in {coords} coordinates)", transform=axs['polar'].ax.transAxes, ha="center", fontsize=11)
        
        # lt_label = (one_swarm_pass['Longitude'][0] + 6) % 24 # place latitude labels away from grid/satellite track (compute once per pass)
        # axs['polar'].writeLATlabels(lt=lt_label, **textargs) #TODO fix!!
        
        # Grid outline
        xs = (grid.lon_mesh[0, :], grid.lon_mesh[-1, :], grid.lon_mesh[:, 0], grid.lon_mesh[:, -1]) # geographic
        ys = (grid.lat_mesh[0, :], grid.lat_mesh[-1, :], grid.lat_mesh[:, 0], grid.lat_mesh[:, -1]) # geographic
    
        xs, ys = np.asarray(xs), np.asarray(ys)

        if self.mag: # convert grid coordinates to mlat, mlt
            #TODO fix things here...
            xs, ys = np.concatenate(xs), np.concatenate(ys)
            _la, mlon = self.apx.geo2apex(ys, xs, HEIGHT)
            _lo = self.dpl.mlon2mlt(mlon, self.mid_time)
        else: # keep geographic, but divide longitudes by 15
            _la, _lo = ys, xs/15

        for i, (lt,lat) in enumerate(zip(_lo, _la)):
            axs['polar'].plot(lat, lt, linewidth = 3 if i == 0 else 1, **outlineargs)
        
        # --------------- # 
        # CUBED SPHERE (grid outline)

        sh = True if hem == 'south' else False # view the cubed sphere projection from above/below in NH/SH
        csax0 = CSplot(axs['zoom'], grid, gridtype='geo', view_from_below=sh)
        csax0.add_coastlines(color='darkgrey')
        axs['zoom'].spines['bottom'].set_linewidth(5) # bottom of grid frame 
        axs['zoom'].set_title("Cubed sphere projection (in geographic coordinates)", fontsize=11)

        return axs['polar'], csax0

    def _plot_swarm_tracks(self, polar_ax, cs_ax, ct, legend_stuff):
        """Plot Swarm A/B/C tracks for the current pass around ct and highlight selected satellite."""

        # Current pass data and ID
        one_swarm_pass, current_pass_id = self.get_current_pass(self.one_swarm, ct)

        # All three Swarm tracks (thin lightred lines) -- current pass only 
        all_swarm_pass = self.all_swarm[self.all_swarm['pass_id'] == current_pass_id]        

        for satid in ['A', 'B', 'C']:
            sw = all_swarm_pass[all_swarm_pass['Spacecraft'] == satid]

            if self.mag:
                satlat, mlon = self.apx.geo2apex(sw.Latitude.to_numpy(), sw.Longitude.to_numpy(), HEIGHT)
                satphi = self.dpl.mlon2mlt(mlon, self.mid_time)
            else: # geographic
                satlat, satphi = sw.Latitude, (sw.Longitude/15) % 24

            polar_ax.plot(satlat, satphi, color='lightcoral', alpha=0.4, linewidth=1.5, zorder=1) 
            cs_ax.plot(sw.Longitude, sw.Latitude, color='lightcoral', alpha=0.4, linewidth=1.5) 

        # Selected Swarm satellite track (thicker red line) -- current pass only
        if self.mag: 
            one_satlat, mlon = self.apx.geo2apex(one_swarm_pass.Latitude.to_numpy(), one_swarm_pass.Longitude.to_numpy(), HEIGHT)
            one_satphi = self.dpl.mlon2mlt(mlon, self.mid_time)
        else:
            one_satlat, one_satphi = one_swarm_pass.Latitude, (one_swarm_pass.Longitude/15) % 24

        polar_ax.plot(one_satlat, one_satphi, color='coral', linewidth=2, zorder=1)
        cs_ax.plot(one_swarm_pass.Longitude, one_swarm_pass.Latitude, color='coral', linewidth=2) 

        # Legend
        added = legend_stuff['added']
        legend_handles = legend_stuff['legend_handles']

        if 'swarm_tracks' not in added:
            legend_handles.append(Line2D([0], [0], color='lightcoral', alpha=0.5, lw=1.7, label='Swarm tracks'))
            legend_handles.append(Line2D([0], [0], color='coral', lw=1.7, label=f'Swarm {self.sat_id[-1]}'))
            added.update(['swarm_tracks'])

    def _plot_dataset(self, dataset, ds, data_object, t0, t1, hem, show_global_data, polar_ax, cs_ax, legend_stuff, quiverscales):
        """
        Plot dataset on polar and cubed-sphere axes.
        Includes:
            - vector data inside the analysis grid
            - optional: all available data within [t0, t1]
        """

        added = legend_stuff['added']
        cs_quivers = legend_stuff['cs_quivers']
        polar_quivers = legend_stuff['polar_quivers']
        legend_handles = legend_stuff['legend_handles']

        hemisign = +1 if hem == 'north' else -1

        # SuperDARN
        if (dataset == 'superdarn'): 

            c='C2'

            # All available data within time interval
            if show_global_data:
                sub = ds.loc[t0:t1, :]
                sub = sub[sub.glat >0] if hem=='north' else sub[sub.glat <0]
                self._scatter(polar_ax, sub.glat, sub.glon, color=c, s=3, marker='^')

            # Data in grid only
            lat = data_object.coords['lat'] #actually glat
            lon = data_object.coords['lon'] #actually glon
            Ve = data_object.values * data_object.los[0] # m/s
            Vn = data_object.values * data_object.los[1]
            
            #1800
            self._plotpins(polar_ax, lat, lon, Ve, Vn, hemisign, SCALE = quiverscales['convection'], markersize = 1, markercolor =c, linewidths = .5, colors =c) #TODO , unit='m/s'
            cs_ax.quiver(Ve, Vn, lon, lat, width=0.002, headwidth=3, color=c, scale=quiverscales['convection'], scale_units='inches')

            # Add to legend once
            if dataset not in added:
                legend_handles.append(Line2D([0], [0], marker='^', color=c, lw=0, markersize=8, label='SuperDARN'))
                added.add(dataset)

            cs_quivers[dataset] = (c, quiverscales['convection'], 'm/s', "Convection")
            polar_quivers[dataset] = (c, quiverscales['convection'], 'm/s')

        # SuperMAG
        elif (dataset == 'supermag'): 

            c='magenta'

            if show_global_data:
                sub = ds.loc[t0:t1, :]
                sub = sub[sub.lat >0] if hem=='north' else sub[sub.lat <0]
                self._scatter(polar_ax, sub.lat, sub.lon, color=c, s=3, marker='^')

            lat = data_object.coords['lat']
            lon = data_object.coords['lon']
            Be = data_object.values[0] #*1e9 # T
            Bn = data_object.values[1] #*1e9

            # 150 *1-9
            self._plotpins(polar_ax, lat, lon, Be, Bn, hemisign, SCALE = quiverscales['ground_mag'], markersize = 1, markercolor =c, linewidths = .5, colors =c) #, unit = 'nT')
            cs_ax.quiver(Be, Bn, lon, lat, width=0.002, headwidth=3, color=c, scale=quiverscales['ground_mag']) #, scale_units='inches'

            if dataset not in added:
                legend_handles.append(Line2D([0], [0], marker='^', color=c, lw=0, markersize=8, label='SuperMAG'))
                added.add(dataset)

            cs_quivers[dataset] = (c, quiverscales['ground_mag']*1e9, 'nT', "Ground mag")
            polar_quivers[dataset] = (c, quiverscales['ground_mag']*1e9, 'nT')

        # Iridium/AMPERE
        elif (dataset == 'iridium_ampere'): 
            
            c='crimson'

            if show_global_data:
                sub = ds[(ds.time >= t0) & (ds.time <= t1)]
                sub = sub[sub.lat >0] if hem=='north' else sub[sub.lat <0]
                self._scatter(polar_ax, sub.lat, sub.lon, color =c, s=3, marker='o')

            lat = data_object.coords['lat']
            lon = data_object.coords['lon']
            Be = data_object.values[0] #*1e9 # T
            Bn = data_object.values[1] #*1e9

            # 250*1e-9
            self._plotpins(polar_ax, lat, lon, Be, Bn, hemisign, SCALE = quiverscales['space_mag_fac'], markersize = 1, markercolor =c, linewidths = .5, colors =c)
            cs_ax.quiver(Be, Bn, lon, lat, width=0.002, color=c, scale=quiverscales['space_mag_fac'], scale_units='inches') 
            
            if dataset not in added:
                legend_handles.append(Line2D([0], [0], marker='o', color=c, lw=0, markersize=8, label='AMPERE'))
                added.add(dataset)

            cs_quivers[dataset] = (c, quiverscales['space_mag_fac']*1e9, 'nT', "Space mag")
            polar_quivers[dataset] = (c, 300, 'nT')

        # Swarm magnetic field
        elif (dataset == 'swarm_mag'): 

            c='mediumpurple'

            if show_global_data:
                sub = ds.loc[t0:t1]
                sub = sub[sub.Latitude >0] if hem=='north' else sub[sub.Latitude <0]
                self._scatter(polar_ax, sub.Latitude, sub.Longitude, color =c, s=3, marker='o')

            lat = data_object.coords['lat']
            lon = data_object.coords['lon']
            Be = data_object.values[0] #*1e9 # T
            Bn = data_object.values[1] #*1e9
            
            #300*1e-9
            self._plotpins(polar_ax, lat, lon, Be, Bn, hemisign, SCALE =quiverscales['space_mag_fac'], markersize = 1, markercolor =c, linewidths = .5, colors =c)
            cs_ax.quiver(Be, Bn, lon, lat, width=0.004, color=c, scale=quiverscales['space_mag_fac'], scale_units='inches') 

            # # highlight central point
            # sc_lat0 = self.one_swarm.loc[ct, 'Latitude'] 
            # sc_lon0 = self.one_swarm.loc[ct, 'Longitude']
            # cs_ax.scatter(sc_lon0, sc_lat0, c='blue', s=400, marker='.')

            if dataset not in added:
                legend_handles.append(Line2D([0], [0], marker='o', color=c, lw=0, markersize=8, label='Swarm mag'))
                added.add(dataset)

            cs_quivers[dataset] = (c, quiverscales['space_mag_fac']*1e9, 'nT', 'Space mag')
            polar_quivers[dataset] = (c, quiverscales['space_mag_fac']*1e9, 'nT')

        # Swarm electric field #TODO fix when I have data
        elif (dataset == 'swarm_efield'): 

            print("fix swarm electric field file! \n")

            c='cyan'

            if show_global_data:
                sub = ds.loc[t0:t1]
                sub = sub[sub.Latitude >0] if hem=='north' else sub[sub.Latitude <0]
                self._scatter(polar_ax, sub.Latitude, sub.Longitude, color =c, s=3, marker='o')

            # electric field data from all three Swarm satellites
            lat = data_object.coords['lat']
            lon = data_object.coords['lon']
            Ee = data_object.values[0]
            En = data_object.values[1]

            self._plotpins(polar_ax, lat, lon, Ee, En, hemisign, SCALE = quiverscales['efield'], markersize = 1, markercolor =c, linewidths = .5, colors =c)
            cs_ax.quiver(Ee, En, lon, lat, width=0.004, color=c, scale=quiverscales['efield'], scale_units='inches') 

            if dataset not in added:
                legend_handles.append(Line2D([0], [0], marker='p', color=c, lw=0, markersize=8, label='Swarm elec'))
                added.add(dataset)
            
            cs_quivers[dataset] = (c, quiverscales['efield'], 'V/m', "Efield")
            polar_quivers[dataset] = (c, quiverscales['efield'], 'V/m')

        # DMSP/SSIES 17 & 18
        elif dataset in ['dmsp_ssies17', 'dmsp_ssies18']:

            if dataset == 'dmsp_ssies17':
                c = 'green'
                label = 'DMSP17'
            else:
                c = 'limegreen'
                label = 'DMSP18'

            if show_global_data:
                sub = ds.loc[t0:t1]
                sub = sub[sub.gdlat > 0] if hem == 'north' else sub[sub.gdlat < 0]
                self._scatter(polar_ax, sub.gdlat, sub.glon, color=c, s=3, marker='o')

            lat = data_object.coords['lat'] #actually gdlat
            lon = data_object.coords['lon'] #actually glon
            Ve = data_object.values * data_object.los[0] # m/s
            Vn = data_object.values * data_object.los[1]

            # 1800
            self._plotpins(polar_ax, lat, lon, Ve, Vn, hemisign, SCALE=quiverscales['convection'], markersize=1, markercolor=c, linewidths=.5, colors=c)
            cs_ax.quiver(Ve, Vn, lon, lat, width=0.002, headwidth=3, color=c, scale=quiverscales['convection'], scale_units='inches')

            if dataset not in added:
                legend_handles.append(Line2D([0], [0], marker='o', color=c, lw=0, markersize=8, label=label))
                added.add(dataset)

            # cs_quivers[dataset] = (c, quiverscales['convection'], 'm/s', "Convection")
            
    def plot_lompe_input(self, grids, time_bounds, data_objects_per_grid, gif_speed = 550, show_global_data=True):
        """
        Visualize Lompe input data along a Swarm satellite trajectory.

        For each analysis grid, this function:
            - plots the Swarm satellite tracks for the current pass
            - overlays data from all available datasets
            - shows data inside the grid and optionally all available data within analysis interval
            - saves each frame as a PNG and compiles them into a GIF animation

        Parameters
        ----------
        grids : list
            List of analysis grid objects aligned with the satellite trajectory.
        time_bounds : dict
            Dictionary containing time information for each grid:
                - 'ct' : central times
                - 't0' : start times of data within each grid
                - 't1' : end times of data within each grid
        data_objects_per_grid : list
            List of dictionaries containing Lompe data objects for each grid.
        gif_speed : int, optional
            Duration of each frame in the output GIF (in milliseconds).
        show_global_data : bool, optional
            If True, plot all available data within [t0, t1] in addition to grid-filtered data.

        Returns
        -------
        frames_pil : list
            List of PIL images corresponding to each frame, useful for GUI display.

        Notes
        -----
        - Figures are saved as PNG files in a temporary directory.
        - A GIF animation summarizing the data coverage is saved to disk.
        """
        
        frames_pil = []

        legend_stuff = {"legend_handles": [], # matplotlib legend entries
                        "added": set(), # track which datasets are already in legend
                        "cs_quivers": {}, # quiver scale info per dataset
                        "polar_quivers": {}, # quiver scale info per dataset
                        }
        
        for grid, ct, t0, t1, data_objects in zip(grids, time_bounds['ct'], time_bounds['t0'], time_bounds['t1'], data_objects_per_grid):
            
            # Hemisphere
            hem = 'north' if grid.projection.lat0 > 0 else 'south' 

            # --------------- # 
            # Initialize figure and axes

            fig, axes = self._init_figure(t0, t1)
            polax, csax = self._setup_plot_frames(axes, grid, hem)
            
            # --------------- # 
            # Plot Swarm trajectories
            
            self._plot_swarm_tracks(polax, csax, ct, legend_stuff)

            # --------------- # 
            # Plot data distribution 

            for dn, data_object in data_objects.items():
                ds = self.datasets[dn]
                self._plot_dataset(dn, ds, data_object, t0, t1, hem, show_global_data, polax, csax, legend_stuff, QUIVERSCALES)

            # --------------- # 
            # Draw legend
            # TODO add legend for both plots (polar and cs)

            # Handles
            fig.legend(handles=legend_stuff['legend_handles'], markerfirst=True, columnspacing=.7, loc="lower left", ncol=6, fontsize=15)    

            # Vectors 
            arrowax = fig.add_axes([0.12, 0.08, 0.25, 0.08])  # position in figure
            arrowax.set_axis_off()
            arrowax.quiver(.1, .5, 1, 0, scale = 2, scale_units = 'inches', color='black',  width=0.005) # This arrow has a fixed visual length, and for each dataset, that length corresponds to a different physical value
            arrowax.set_ylim(0, 1)
            arrowax.set_xlim(0, 20)
        
            y = 0.88
            groups = defaultdict(list)
            for dataset, (color, value, unit, label) in legend_stuff['cs_quivers'].items():
                groups[label].append((color, value, unit))
            for label, items in groups.items():
                arrowax.text(5, y, f"{label}:", fontsize=15, va='top')
                x = 15
                for color, value, unit in items:
                    arrowax.text(x, y, f"{value//2:.0f} {unit}",
                                color=color, fontsize=14, va='top')
                    x += 6  # spacing between entries
                y -= 0.28

            # arrowax2 = fig.add_axes([0.15, 0.1, 0.25, 0.08])  # position in figure
            # arrowax2.set_axis_off()
            # arrowax2.quiver(.1, .5, 1, 0, scale = 2, scale_units = 'inches', color='black',  width=0.004)
            # arrowax2.set_ylim(0, 1)
            # arrowax2.set_xlim(0, 20)
            # # arrowax.text(3, 0.8, f"{sm_scale:.0f} nT (SuperMAG)\n" f"{sd_scale:.0f} m/s (SuperDARN)\n" f"{amp_scale:.0f} nT (AMPERE)", fontsize=15, va='top')
            # y = 0.8
            # for key, (color, scale, unit) in legend_stuff['polar_quivers'].items():
            #     arrowax2.text(4, y, f"{scale:.0f} {unit}", color=color, fontsize=15, va='top')
            #     y -= 0.28

            # --------------- # 
            # Save output

            # Save to PNG
            swarm_fn = f'lompe-input_swarm{self.sat_id[-1]}'
            fn = os.path.join(tmpdir, f"{swarm_fn}_{ct.strftime('%Y%m%d_%H%M%S')}.png")
            plt.savefig(fn, dpi=400, pad_inches=0.2)  # NO bbox_inches='tight'

            # Convert figure to PIL (used for the UI GIF)
            fig.canvas.draw()
            buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
            pil_img = Image.fromarray(buf)
            pil_img = ImageOps.expand(pil_img, border=15, fill="white")
            frames_pil.append(pil_img.copy())
            
            plt.close(fig)

        print(f"Figures with Swarm tracks, analysis grid, and data distribution for each time step saved in: {tmpdir}")

        # Save GIF
        output = outputs_path + f"/{swarm_fn}.gif" 

        with imageio.get_writer(output, mode="I", duration=gif_speed) as writer:
            for frame in frames_pil:
                writer.append_data(np.array(frame))  # convert PIL → numpy

        print(f"GIF saved in outputs directory as: {output}") 

        return frames_pil # returns PIL images for display in GUI

def show_error_popup(msg):
    root = tk._default_root
    created_root = False

    if root is None:
        root = tk.Tk()
        root.withdraw()
        created_root = True
    messagebox.showerror("Error", msg)

    if created_root:
        root.destroy()