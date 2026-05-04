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
from lompeosse import LompeOSSE, Gamera_output

import time as tt
# TODO documentation
# TODO check gamera quantities with Kalle, and the grid used to plot stuff
# TODO check radius stuff in get_B with Kalle

package_root = Path(__file__).resolve().parents[3]  
output_dir = str(package_root / "outputs")
tmpdir = output_dir + '/tmp/' #TODO fix to true temporary folder?

def run_lompeOSSE(models, time_offset=0, snapshot=0):
    """
    """

    print("\n Running LompeOSSE validation...")

    osse_models = []
    gamera_outputs = []

    for entry in models:
        model = entry["model"]
        ct = entry["ct"]
        l1 = entry["l1"]
        l2 = entry["l2"]

        hemi = 'NORTH' if model.grid_E.lat.all() > 0 else 'SOUTH'

        # Extract Gamera data

        t0 = tt.perf_counter()

        gamera_output = Gamera_output(ct, timestep = snapshot, hemisphere = hemi)
        gamera_outputs.append({"gamera_output": copy.deepcopy(gamera_output)})

        t1 = tt.perf_counter()
        print("Gamera_output", t1 - t0)

        # Derive synthetic (OSSE) model
        osse_object = LompeOSSE(model, gamera_output)

        t2 = tt.perf_counter()
        print("LompeOSSE", t2 - t1)

        osse_Emodel = osse_object.make_OSSE_model(time_offset = time_offset) #TODO what is the point of adding time offset here rather thsn in the class directly? 

        t3 = tt.perf_counter()
        print("make_osse_model", t3 - t2)
        
        # Run inversion
        osse_Emodel.run_inversion(l1 = l1, l2 = l2)
        
        # Save model for use in lompeOSSE_output function
        osse_models.append({"osse_model": copy.deepcopy(osse_Emodel),
                            "t0": entry["t0"],
                            "t1": entry["t1"],
                            "ct": ct,
                            "apex": entry["apex"],
                            # "l1": l1,
                            # "l2": l2, 
                            "time_offset": osse_object.time_offset})

    return osse_models, gamera_outputs


def plot_lompeOSSE_output(osse_models, gamera_outputs, figheight=9, gif_speed=550):
    """ 
    input: osse models
    output: lompe plot
    explain that the plot of the origianl gamera electrodynamics is considered as ground truth. The lompeOSSE plot can be compared to that ground truth
    """

    # temp_filenames = []
    frames_pil_lompeosse = []
    frames_pil_gamera = []

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
        
        t11 = tt.perf_counter()

        print("\n Generating LompeOSSE output...")
        print("##", ntime, "##")

        # Save to PNG
        lompeosse_fn = f'lompeOSSE_electrodynamics'
        fn = os.path.join(tmpdir, f"{lompeosse_fn}_{t0.strftime('%Y%m%d_%H%M%S')}.png") 
        savekw = {"fname": fn, "dpi": 400, "bbox_inches":"tight", "pad_inches":0.2}

        fig_lompeosse = lompe.lompeplot(osse_model,
                                        include_data=True,
                                        time=ntime,
                                        apex=apx,
                                        colorscales={"fac": np.linspace(-2, 2, 40) * 1e-6 * 2,
                                                    "ground_mag": np.linspace(-500, 500, 50) * 1e-9 / 3,
                                                    "hall":       np.linspace(0, 20, 32),
                                                    "pedersen":   np.linspace(0, 20, 32)},
                                        quiverscales={"ground_mag":       600e-9,
                                                    "space_mag_fac":    600e-9,
                                                    "space_mag_full":   600e-9,
                                                    "electric_current": 1}, 
                                        figheight=figheight,
                                        savekw=savekw)

        fig_lompeosse.suptitle(f"LompeOSSE-reconstructed electrodynamics (GAMERA data) \n {(t0).strftime('%Y-%m-%d %H:%M:%S')}  -  {t1.strftime('%Y-%m-%d %H:%M:%S')}",
                fontsize=22, color="black", y=0.98)
        # TODO do we need this time to take time offset into account? ask Kalle how the time offset thing is relevant at all here...
        
        fig_lompeosse.subplots_adjust(left=0.08, right=0.95, hspace=.8, wspace=0.2)

        # Save PNG (with title)
        fig_lompeosse.savefig(fn, dpi=400)

        t22 = tt.perf_counter()
        print("lompeosseplot:", t22 - t11)

        # Convert figure to PIL (chatGPT) (used for the UI GIF)
        fig_lompeosse.canvas.draw()
        buf = np.asarray(fig_lompeosse.canvas.buffer_rgba())[:, :, :3]
        pil_img = Image.fromarray(buf)
        pil_img = ImageOps.expand(pil_img, border=15, fill="white")
        frames_pil_lompeosse.append(pil_img.copy())

        #################
        # GAMERA plot 
        #################

        gamera_output = entry2['gamera_output']

        grid = osse_model.grid_J # TODO OK???
        gridE = osse_model.grid_E

        # Plotting grid (from lompe.visualiation.lompeplot)
        sh = np.array(grid.shape)
        NN = 12 # number of data points 
        sh = sh // sh.min() * NN 
        ximin  = grid.xi .min() #+ grid.dxi  / 3
        ximax  = grid.xi .max() #- grid.dxi  / 3
        etamin = grid.eta.min() #+ grid.deta / 3
        etamax = grid.eta.max() #- grid.deta / 3
        xi, eta = np.meshgrid(np.linspace(ximin, ximax, sh[1]), np.linspace(etamin, etamax, sh[1]))
        lo, la = grid.projection.cube2geo(xi, eta)

        # GAMERA QUANTITIES

        # Electric potential
        EpotG = gamera_output.get_potential(lo, la, ntime)
        V = EpotG - EpotG.min() - (EpotG.max() - EpotG.min())/2 #TODO is that right? in lompe.plot_potential

        # Convection velocity
        VeG, VnG = gamera_output.get_V(lo, la, ntime)
        x, y, Vx, Vy = grid.projection.vector_cube_projection(VeG, VnG, lo, la)

        # Field-aligned current 
        facG = gamera_output.get_FAC(lo, la, ntime)

        # Space magnetic field
        Be_space, Bn_space, Bu_space = gamera_output.get_B(lo, la, r=np.array(6500e3), no_df_current=True) #TODO is r ok??
        x, y, Bx_space, By_space = grid.projection.vector_cube_projection(Be_space, Bn_space, lo, la)

        # Ground magnetic field 
        Be_ground, Bn_ground, Bu_ground = gamera_output.get_B(lo, la, r=np.full_like(lo, 6371*1e3)) #TODO is r ok??
        # #TODO put that in get_B directly maybe?
        # Be_ground = Be_ground.reshape(lo.shape)
        # Bn_ground = Bn_ground.reshape(lo.shape)
        Bmag_ground = np.sqrt(Be_ground**2 + Bn_ground**2).reshape(lo.shape)
        x, y, Bx_ground, By_ground = grid.projection.vector_cube_projection(Be_ground, Bn_ground, lo, la)

        # Conductances
        HallG = gamera_output.get_Pedersen(lo, la, ntime)
        PedersenG = gamera_output.get_Hall(lo, la, ntime)

        # Electric currents
        EeG, EnG = gamera_output.get_E(lo, la, ntime)
        x, y, Ex, Ey = grid.projection.vector_cube_projection(EeG, EnG, lo, la)

        # FIGURE
        figheight = 9
        ar = gridE.shape[1] / gridE.shape[0] # aspect ratio
        nrows, ncols = 2, 3
        subplot_height = figheight / nrows
        subplot_width = subplot_height * ar
        figwidth = subplot_width * ncols

        fig_gamera, axes = plt.subplots(nrows, ncols, figsize=(figwidth, figheight))
        
        for ax in axes.flatten():
            lompe.visualization.format_ax(ax, osse_model, apex = apx)

        plt.tight_layout()  # removes extra whitespace between subplots

        # colorscales
        dV = 5 # contour level step size in kV
        potential_levels = np.r_[(V.min()//dV)*dV :(V.max()//dV)*dV + dV:dV]
        fac_levels= np.linspace(-1.95, 1.95, 40) * 1e-6 * 2
        ground_mag_level =  np.linspace(-500, 500, 50) * 1e-9 / 3
        cond_levels = np.linspace(0, 20, 32)

        # fig_gamera = plt.figure(figsize=(8, 6))
        # gs = gridspec.GridSpec(2, 3, height_ratios=[1, 1])
        # gridtype = 'geo'

        # Convection velocity and electric potential
        # ax1 = fig_gamera.add_subplot(gs[0, 0])  
        # csax1 = cs.CSplot(ax1, grid, gridtype=gridtype)
        # csax1.quiver(VeG, VnG, lo, la)
        # csax1.contour(lo, la, EpotG, colors='C0')
        ax1 = axes[0,0]
        ax1.contour(xi, eta, V, colors='C0', linewidths=2, levels=potential_levels) # potential
        ax1.quiver(x, y, Vx, Vy) # convection
        ax1.set_title("Convection velocity \n and electric potential")

        # FAC and space magnetic field
        # ax2 = fig_gamera.add_subplot(gs[0, 1])  
        # csax2 = cs.CSplot(ax2, grid, gridtype=gridtype)
        # csax2.contourf(lo, la, facG*(-1), cmap='bwr', levels=fac_levels*1e6) #TODO fix *(-1) ?
        # csax2.quiver(Be_space, Bn_space, lo, la)
        ax2 = axes[0,1]
        ax2.contourf(xi, eta, facG*(-1), cmap='bwr') #TODO smthg weird with dimension #levels don't work here
        ax2.quiver(x, y, Bx_space, By_space) #, zorder=3, scale=QUIVERSCALES['space_mag_fac'], scale_units="inches"
        ax2.set_title("Field-aligned currents \n and magnetic field")

        # Ground magnetic field (vectors + magnitude)
        # ax3 = fig_gamera.add_subplot(gs[0, 2])
        # csax3 = cs.CSplot(ax3, grid, gridtype=gridtype)
        # csax3.contourf(lo, la, Bmag_ground, cmap='bwr', level=ground_mag_level*1e9)  #TODO fix *(-1) ? #TODO probably need to fix all the stuff about magnetic field
        # csax3.quiver(Be_ground, Bn_ground, lo, la)
        ax3 = axes[0,2]  
        ax3.contourf(xi, eta, Bmag_ground*(-1), cmap='bwr') #TODO smthg weird with dimensions
        ax3.quiver(x, y, Bx_ground, By_ground)
        ax3.set_title("Ground magnetic field")

        # Hall conductance
        # ax4 = fig_gamera.add_subplot(gs[1, 0])  
        # csax4 = cs.CSplot(ax4, grid, gridtype=gridtype, lat_res=5)
        # csax4.contourf(lo, la, HallG, cmap='magma', levels=cond_levels)
        # csax4.add_coastlines(color='darkgrey')
        ax4 = axes[1,0]
        ax4.contourf(xi, eta, HallG, cmap='magma', levels=cond_levels)
        lompe.visualization.plot_coastlines(ax4, osse_model, color = 'grey')
        lompe.visualization.plot_mlt(ax4, osse_model, ntime, apx, color = 'grey')
        ax4.set_title("Hall conductance")

        # Pedersen conductance
        # ax5 = fig_gamera.add_subplot(gs[1, 1])  
        # csax5 = cs.CSplot(ax5, grid, gridtype=gridtype, lat_res=5)
        # csax5.contourf(lo, la, PedersenG, cmap='magma', levels=cond_levels) 
        # csax5.add_coastlines(color='darkgrey')
        ax5 = axes[1,1]
        ax5.contourf(xi, eta, PedersenG, cmap='magma', levels=cond_levels)
        lompe.visualization.plot_coastlines(ax5, osse_model, color = 'grey')
        lompe.visualization.plot_mlt(ax5, osse_model, ntime, apx, color = 'grey')
        ax5.set_title("Pedersen conductance")

        # Electric currents/current densities
        # ax6 = fig_gamera.add_subplot(gs[1, 2])  
        # csax6 = cs.CSplot(ax6, grid, gridtype=gridtype)
        # csax6.quiver(EeG, EnG, lo, la)
        ax6 = axes[1,2]
        ax6.quiver(x, y, Ex, Ey)
        ax6.set_title("Electric currents")

        # for ax in fig_gamera.axes:
        #     ax.set_xticks([])
        #     ax.set_yticks([])
        #     ax.set_xlabel("")
        #     ax.set_ylabel("")

        plt.subplots_adjust(top=0.86, bottom=0.065, left=0.01, right=0.99, hspace=0.1, wspace=0.01) 
        fig_gamera.suptitle(f"Original GAMERA electrodynamics \n {t0.strftime('%Y-%m-%d %H:%M:%S')}  -  {t1.strftime('%Y-%m-%d %H:%M:%S')}",
                fontsize=22, color="black", y=0.98)
        
        # Save to PNG
        gamera_fn = f'GAMERA_electrodynamics'
        fn = os.path.join(tmpdir, f"{gamera_fn}_{t0.strftime('%Y%m%d_%H%M%S')}.png")
        fig_gamera.savefig(fn, dpi=400, bbox_inches="tight", pad_inches=0.2)

        fig_gamera.canvas.draw()
        buf = np.asarray(fig_gamera.canvas.buffer_rgba())[:, :, :3]
        pil_img = Image.fromarray(buf)
        pil_img = ImageOps.expand(pil_img, border=15, fill="white")
        frames_pil_gamera.append(pil_img.copy())

    print(f"LompeOSSE output figures for each time step saved in temporary folder: {tmpdir}")

    # Path to save the GIFs
    output_gam = output_dir + f"/{gamera_fn}.gif"
    output_lomp = output_dir + f"/{lompeosse_fn}.gif"

    with imageio.get_writer(output_lomp, mode="I", duration=gif_speed) as writer:
        for frame in frames_pil_lompeosse:
            writer.append_data(np.array(frame))  # convert PIL → numpy

    with imageio.get_writer(output_gam, mode="I", duration=gif_speed) as writer:
        for frame in frames_pil_gamera:
            writer.append_data(np.array(frame))  # convert PIL → numpy

    print(f"GIF saved in outputs directory: {output_lomp} and {output_gam}") # TODO fix path to indicate the user directory 

    return frames_pil_lompeosse, frames_pil_gamera 
