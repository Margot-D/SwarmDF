import matplotlib.pyplot as plt
import numpy as np
import copy
import matplotlib.gridspec as gridspec
from datetime import timedelta
import secsy as cs
from pathlib import Path
import os

import imageio.v2 as imageio
from PIL import Image

import lompe
from lompe.model.visualization import *
from lompeosse import LompeOSSE, Gamera_output

package_root = Path(__file__).resolve().parents[1]  
src_root = package_root.parent  
outputs_path = str(src_root / "outputs")
tmpdir = outputs_path + '/tmp/' #TODO fix

def run_lompeOSSE(models):

    print("Running LompeOSSE validation...")

    hemisphere = 'NORTH' #TODO fix that (make it an automatic parameter)

    osse_models = []
    gamera_outputs = []

    for entry in models:
        model = entry["model"]
        ct = entry["ct"]
        l1 = entry["l1"]
        l2 = entry["l2"]

        # Extract Gamera data
        gamera_output = Gamera_output(ct, timestep = 0, hemisphere = hemisphere)
        gamera_outputs.append({"gamera_output": copy.deepcopy(gamera_output)})

        # Derive synthetic model
        osse_object = LompeOSSE(model, gamera_output)
        osse_Emodel = osse_object.make_OSSE_model(time_offset = 0) #TODO what is the point of adding time offset here rather thsn in the class directly? 

        # Run inversion and show output #TODO put into LompeOSSE? like a lompeOSSE_plot function maybe
        osse_Emodel.run_inversion(l1 = l1, l2 = l2) # 1) model norm, and 2) gradient of SECS amplitudes (charges) in magnetic eastward direction
        
        osse_models.append({"osse_model": copy.deepcopy(osse_Emodel),
                            "t0": entry["t0"],
                            "t1": entry["t1"],
                            "ct": ct,
                            "apex": entry["apex"],
                            "l1":l1,
                            "l2":l2})

    return osse_models, gamera_outputs


def lompeOSSE_output(osse_models, gamera_outputs, gif_speed):
    """ 
    input: osse models
    output: lompe plot
    """

    temp_filenames = []
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

        fig_lompeosse = lompe.lompeplot(osse_model,
                            include_data=True,
                            time=ct,
                            apex=apx,
                            colorscales={"fac": np.linspace(-2, 2, 40) * 1e-6 * 2,
                                        "ground_mag": np.linspace(-500, 500, 50) * 1e-9 / 3,
                                        "hall":       np.linspace(0, 20, 32),
                                        "pedersen":   np.linspace(0, 20, 32)},
                            quiverscales={"ground_mag":       600e-9,
                                        "space_mag_fac":    600e-9,
                                        "space_mag_full":   600e-9,
                                        "electric_current": 1})

        fig_lompeosse.suptitle(f"LompeOSSE-reconstructed electrodynamics (GAMERA data) \n {t0.strftime('%Y-%m-%d %H:%M:%S')}  -  {t1.strftime('%Y-%m-%d %H:%M:%S')}",
                fontsize=18, color="black", y=0.98)
        
        # Save to PNG
        lompe_fn = f'lompeOSSE_electrodynamics'
        fn = os.path.join(tmpdir, f"{lompe_fn}_{t0.strftime('%Y%m%d_%H%M%S')}.png")
        fig_lompeosse.savefig(fn, dpi=400, bbox_inches="tight", pad_inches=0.2)
        print('figure saved')
        temp_filenames.append(fn)

        # Convert figure to PIL (chatGPT) (used for the UI GIF)
        fig_lompeosse.canvas.draw()
        width, height = fig_lompeosse.canvas.get_width_height()
        buf = np.frombuffer(fig_lompeosse.canvas.tostring_argb(), dtype=np.uint8).reshape((height, width, 4))[:, :, 1:4]  # reorder to RGB
        pil_img = Image.fromarray(buf)
        frames_pil_lompeosse.append(pil_img.copy())

        plt.show()
        plt.close(fig_lompeosse)

        #################
        # Original Gamera electrodynamic quantities (equivalent to ground truth)
        #################

        gamera_output = entry2['gamera_output']
        grid = osse_model.grid_J # TODO OK???
        gridE = osse_model.grid_E

        ntime = ct
        # ntime = osse_object.timestamp + dt.timedelta(hours=osse_object.time_offset)

        # plotting grid
        sh = np.array(grid.shape)
        NN = 12
        sh = sh // sh.min() * NN 
        ximin  = grid.xi .min() + grid.dxi  / 3
        ximax  = grid.xi .max() - grid.dxi  / 3
        etamin = grid.eta.min() + grid.deta / 3
        etamax = grid.eta.max() - grid.deta / 3
        xi, eta = np.meshgrid(np.linspace(ximin, ximax, sh[1]), np.linspace(etamin, etamax, sh[1]))
        lo, la = grid.projection.cube2geo(xi, eta)

        # GAMERA quantities
        EpotG = gamera_output.get_potential(lo, la, ntime)
        V = EpotG - EpotG.min() - (EpotG.max() - EpotG.min())/2 #TODO is that right? in lompe.plot_potential

        VeG, VnG = gamera_output.get_V(lo, la, ntime)
        x, y, Vx, Vy = grid.projection.vector_cube_projection(VeG, VnG, lo, la)

        facG = gamera_output.get_FAC(lo, la, ntime)

        Be_ground, Bn_ground, Bu_ground = gamera_output.get_B(lo, la, r=np.full_like(lo, 6371*1e3)) #TODO is r ok??
        # #TODO put that in get_B directly maybe?
        # Be_ground = Be_ground.reshape(lo.shape)
        # Bn_ground = Bn_ground.reshape(lo.shape)
        Bmag_ground = np.sqrt(Be_ground**2 + Bn_ground**2).reshape(lo.shape)
        x, y, Bx_ground, By_ground = grid.projection.vector_cube_projection(Be_ground, Bn_ground, lo, la)

        Be_space, Bn_space, Bu = gamera_output.get_B(lo, la, r=np.array(6500e3), no_df_current=True) #TODO is r ok??
        x, y, Bx_space, By_space = grid.projection.vector_cube_projection(Be_space, Bn_space, lo, la)

        HallG = gamera_output.get_Pedersen(lo, la, ntime)

        PedersenG = gamera_output.get_Hall(lo, la, ntime)

        EeG, EnG = gamera_output.get_E(lo, la, ntime)
        x, y, Ex, Ey = grid.projection.vector_cube_projection(EeG, EnG, lo, la)

        # FIGURE
        figheight = 9
        ar = gridE.shape[1] / gridE.shape[0] # aspect ratio
        figsize = ((3 * ar + 1)/2 * figheight * .8, figheight)
        print('figsize', figsize)
        figsize = (8,8)
        fig_gamera = plt.figure(figsize=figsize)
        axes = np.vstack(([plt.subplot2grid((20, 4), ( 0, j), rowspan = 10) for j in range(3)],
                            [plt.subplot2grid((20, 4), (10, j), rowspan = 10) for j in range(3)]))
        for ax in axes.flatten():
            lompe.visualization.format_ax(ax, osse_model, apex = apx)

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

        # Save to PNG
        gamera_fn = f'GAMERA_electrodynamics'
        fn = os.path.join(tmpdir, f"{gamera_fn}_{t0.strftime('%Y%m%d_%H%M%S')}.png")
        fig_gamera.savefig(fn, dpi=400, bbox_inches="tight", pad_inches=0.2)
        print('figure saved')
        temp_filenames.append(fn)

        fig_gamera.canvas.draw()
        width, height = fig_gamera.canvas.get_width_height()
        buf = np.frombuffer(fig_gamera.canvas.tostring_argb(), dtype=np.uint8).reshape((height, width, 4))[:, :, 1:4]  # reorder to RGB
        pil_img = Image.fromarray(buf)
        frames_pil_gamera.append(pil_img.copy())

        plt.show()
        plt.close(fig_gamera)

    print(f"LompeOSSE output figures for each time step saved in temporary folder: {tmpdir}")

    # Path to save the GIF
    output = outputs_path + f"/{lompe_fn}.gif"

    with imageio.get_writer(output, mode="I", duration=gif_speed) as writer:
        for frame in frames_pil_lompeosse:
            writer.append_data(np.array(frame))  # convert PIL → numpy

        for frame in frames_pil_gamera:
            writer.append_data(np.array(frame))  # convert PIL → numpy

    print(f"GIF saved in outputs directory: {output}") # TODO fix path to indicate the user directory 

    return frames_pil_lompeosse, frames_pil_gamera 

# %%
