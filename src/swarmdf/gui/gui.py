"""
SwarmDF Toolbox — Graphical User Interface (GUI)

#TODO make this better
This script launches the graphical user interface for the Swarm Data Fusion (SwarmDF) toolbox.
From here, the user can 1) configure input parameters, 2) visualize their defined grid along the Swarm trajectory as well as the available ionospheric data around it, 3) run the Lompe reconstruction process, 
4) visualize the resulting ionospheric electrodynamics, and 5) verify the Lompe output. This serves as the main 
entry point for interacting with the toolbox.
"""

import matplotlib
matplotlib.use("TkAgg")

from tkinter import messagebox
import threading
import traceback

import customtkinter
customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

from swarmdf import * # core functions
from swarmdf.pipeline import get_data, compute_swarmdf_input, compute_swarmdf_output, compute_swarmdf_validation, render_swarmdf_input, render_swarmdf_output, render_swarmdf_validation

from swarmdf.config import SwarmDFConfig
from swarmdf.gui.ui.sidebar_left import build_left_sidebar
from swarmdf.gui.ui.sidebar_right import build_right_sidebar
from swarmdf.gui.ui.input_panels import build_input_panels
from swarmdf.gui.ui.output_panels import build_plot_panels
from swarmdf.gui.ui.validation_window import open_validation_window
from swarmdf.gui.ui.helpers.image_display import *
from swarmdf.gui.ui.helpers.animation_manager import AnimationManager

class SwarmDFGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        #############
        # Configure GUI window layout

        self.title("SwarmDF.py")
        width, height = 1660, 950
        self.aspect_ratio = 16/9 # width/height
        self.geometry(f"{width}x{height}")
        self.minsize(1450, 780)
        # self.bind("<Configure>", self.enforce_aspect)

        self.grid_columnconfigure(1, weight=0, minsize=365)
        self.grid_columnconfigure(2, weight=4)
        self.grid_columnconfigure(3, weight=0, minsize=300)
        self.grid_rowconfigure((0, 1), weight=1)

        build_left_sidebar(self)
        build_input_panels(self)
        build_plot_panels(self)     
        build_right_sidebar(self)

        #############
        # Check/validate user entries

        self.validators = [(self.entry_timestep, "Timestep", 30, 5, None),
                           (self.entry_kp, "Kp index", 4, 0, 9), 
                           (self.entry_f107, "F107 value (s.f.u)", 100, 30, 400), #TODO values ok Kalle? 
                           (self.entry_background, "Background value", 2, 0, None), # TODO what's a good range Kalle?
                           (self.entry_L, "Grid length (km)", 2000, None, None),
                           (self.entry_W, "Grid width (km)", 1500, None, None),
                           (self.entry_Lres, "Grid length resolution (km)", 200, None, None),
                           (self.entry_Wres, "Grid width resolution (km)", 200, None, None),
                           (self.entry_wshift, "Cross-track shift value (km)", 0, None, None),
                           (self.entry_gifspeed, "Animation speed", 550, 0, None),
                           (self.entry_Gsnapshot, "Gamera snapshot", 0, None, None),
                           (self.entry_Gtimeoff, "Time offset", 0, 0, 23), #TODO ok?
                           ]
        
        # Check and validate values from entries as the user types
        for entry, name, default, min_val, max_val in self.validators:
            entry.bind("<FocusOut>", lambda e, entry=entry, name=name, default=default, min_val=min_val, max_val=max_val: 
                        self.validate_entry(entry, name, default, min_val, max_val))

    #################
    # Run SwarmDF

    def run_swarmdf(self):

        # Disable buttons when SwarmDF starts running 
        self.set_buttons_state("disabled")

        # Check and validate values from all entries before running SwarmDF
        for entry, name, default, min_val, max_val in self.validators:
            self.validate_entry(entry, name, default, min_val, max_val)

       # Collect user input
        self.config = self.build_config_from_gui()

        # Generate a Python script reproducing the SwarmDF workflow from the current configuration
        if self.switch_pythonscript.get():
            fn = self.entry_codename.get() if self.entry_codename.get() else 'SwarmDF_script.py' # default file name
            generate_python_code(self.config, fn)

        # Progress bar for Lompe input panel
        self.progress_input.start() #TODO maybe go back to defining it all here? does not work on re-run right now

        # Initialize animation manager
        self.anim_mgr = AnimationManager()

        # Schedule heavy part of SwarmDF after letting the GUI update
        self.after(100, self._do_swarmdf)
    
    def _do_swarmdf(self):
        """SwarmDF pipeline for GUI"""

        print("--- Running SwarmDF --- ")

        try: 
            # Data
            self.datasets = get_data(self.config)

            # Input to Lompe
            self.input_results = compute_swarmdf_input(self.config, self.datasets) 
            self.display_swarmdf_input(self.input_results)

            # Lompe output
            if self.config.run_lompe_flag:
                self.trigger_lompe_analysis()
            else:
                self.button_runlompe_temp.grid(row=1, column=0, pady=(0, 20))
                self.set_buttons_state("normal")

            # LompeOSSE validation (once Lompe is done)
            if self.config.run_validation_flag:
                self.wait_for_lompe_then_validate()

        except Exception as e:
            print(e)
            messagebox.showerror("SwarmDF failed", str(e)) # TODO for debugging only
            print("SwarmDF failed, the following exception occured:", e) 

# -------------------------------------------------------
# -------------------------------------------------------
# Helper functions 

####################
####################
# # GUI callback and update helpers
        
    def keep_ratio(self, event):
        """
        Maintain fixed aspect ratio for the output frames 
        when the container is resized.
        """
        container_w = event.width
        container_h = event.height

        panel_h = (container_h - 10) // 2

        h = panel_h
        w = int(h * self.aspect_ratio)

        if w > container_w:
            w = container_w
            h = int(w / self.aspect_ratio)

        self.frame_input.configure(width=w, height=h)
        self.frame_output.configure(width=w, height=h)
        
    def validate_entry(self, entry, name, default=None, min_val=None, max_val=None):
        """Read and validate a float value from an entry widget"""

        try:
            value = float(entry.get())
        except ValueError:
            value = default
            messagebox.showwarning("Invalid input", f"{name} is invalid. Using default value: {default}")

        if min_val is not None and value < min_val:
            messagebox.showwarning("Invalid input", f"{name} must be ≥ {min_val}. Using default: {default}")
            value = default
        if max_val is not None and value > max_val:
            messagebox.showwarning("Invalid input", f"{name} must be ≤ {max_val}. Using default: {default}")
            value = default

        # Reflect corrected value in UI
        if default is not None and value == default:
            entry.delete(0, "end")
            entry.insert(0, str(default))

        return # wrong if value is returned!

    def apply_gif_parameters(self, update_state=True):
        """
        Validate and get GIF speed from the entry.
        Optionally update the master/validation state if it exists.
        Returns the validated speed.
        """
        try:
            speed = int(self.entry_gifspeed.get())
        except ValueError:
            speed = self.default_speed

        if speed < 0:
            speed = self.default_speed

        # reflect the final value in the UI
        self.entry_gifspeed.delete(0, "end")
        self.entry_gifspeed.insert(0, str(speed))

        # If it already exists, update the animations with new speed
        if update_state:
            new_speed = speed
            if hasattr(self, "master_state"):
                self.master_state["delay"] = new_speed
            # also update LompeOSSE validation animation
            if hasattr(self, "validation_state"):
                self.validation_state["delay"] = new_speed

            print(f"Animation update: applied speed = {new_speed} ms per frame")

        return speed

    def update_l1_label(self, slider_val):
            log_val = 10 ** slider_val # log scale
            self.value_l1.configure(text=f"{log_val:.2f}")
            # TODO is l1 = exponent or 1**exponent ??

    def update_l2_label(self, slider_val):
            log_val = 10 ** slider_val # log scale
            self.value_l2.configure(text=f"{log_val:.2f}")
            
    def apply_new_regularization(self):

        # Get updated slider values
        self.config.regularization_l1 = 10 ** self.slider_l1.get()
        self.config.regularization_l2 = 10 ** self.slider_l2.get()

        # Run lompe with new parameters
        self.trigger_lompe_analysis()
        
    def update_lompe_input(self):
        self.config.mag_coords_flag = bool(self.checkbox_magcoords.get())
        self.config.show_all_data_flag = bool(self.checkbox_showdata.get())
        self.display_swarmdf_input(self.input_results)

####################
####################
# # Functions for collecting GUI input

    def build_config_from_gui(self):

        # satellite ID
        sat_id = self.optmenu_satellite.get()
        if sat_id == "Satellite ID":
            messagebox.showerror("Error", "⚠️ Please select a valid Satellite ID (Swarm A, B, or C) and press Run SwarmDF again.")
            return

        # time interval
        start_time, end_time = self.get_start_end_times()
        
        # time step (between frames)
        timestepp = float(self.entry_timestep.get())
        unit = self.timestep_unit_var.get()

        if unit == "min":
            timestepp *= 60
        elif unit == "h":
            timestepp *= 3600

        timestep = timestepp

        # datasets
        datasets2download = []
        # if self.checkbox_swarm_efield.get():
        #     datasets2download.append('swarm_efield')
        #TODO add ion flow
        if self.checkbox_swarm_bfield.get():
            datasets2download.append('swarm_mag')
        if self.checkbox_superdarn.get():
            datasets2download.append('superdarn')
        if self.checkbox_supermag.get():
            datasets2download.append('supermag')
        if self.checkbox_iridium_ampere.get():
            datasets2download.append('iridium_ampere')
        if self.checkbox_dmsp_ssies17.get():
            datasets2download.append('dmsp_ssies17')
        if self.checkbox_dmsp_ssies18.get():
            datasets2download.append('dmsp_ssies18')

        if len(datasets2download) == 0: 
            if self.checkbox_runlompe.get():
                self.checkbox_runlompe.deselect()
                messagebox.showwarning("Lompe unavailable", "No valid datasets available for Lompe inversion.")

        # conductance
        kp_value = float(self.entry_kp.get()) 
        f107_value = float(self.entry_f107.get())
        background_value = float(self.entry_background.get())

        conductance_params = {"kp": kp_value, "f107": f107_value, "background": background_value}
        conductance_method = str(self.optmenu_conductance.get())
        print(repr(conductance_method))

        # grid 
        grid_params = self.get_grid_parameters()
        if grid_params is None:
            return

        # Figure size
        figw = float(self.entry_figw.get())
        figh = float(self.entry_figh.get())

        # Polar plot magnetic coordinates
        mag = bool(self.checkbox_magcoords.get())

        # Show global data (outside grid)
        show_data = bool(self.checkbox_showdata.get())

        # GIF speed
        speed = self.apply_gif_parameters(update_state=False) # ms/frame

        # Lompe flag
        run_lompe_flag = bool(self.checkbox_runlompe.get())

        # regularization #TODO Ok kalle?
        l1 = 10 ** self.slider_l1.get()
        l2 = 10 ** self.slider_l2.get()

        # validation (LompeOSSE)
        run_validation_flag = bool(self.checkbox_lompeosse.get())
        timeoff = int(self.entry_Gtimeoff.get())
        snapshot = int(self.entry_Gsnapshot.get())

        # demo mode
        demo_flag = bool(self.switch_demo.get())

        return SwarmDFConfig(sat_id=sat_id,
                             start_time=start_time, end_time=end_time, timestep=timestep,
                             datasets2download=datasets2download,
                             grid_params=grid_params,
                             run_lompe_flag=run_lompe_flag,
                             conductance_method=conductance_method,
                             conductance_params=conductance_params,
                             regularization_l1=l1, regularization_l2=l2,
                             run_validation_flag=run_validation_flag,
                             time_offset=timeoff, snapshot=snapshot,
                             demo_flag=demo_flag,
                             gif_speed=speed,
                             figw=figw, figh=figh,
                             mag_coords_flag=mag,
                             show_all_data_flag=show_data)

    def get_start_end_times(self):

        input_start = self.entry_start_time.get_datetime()
        input_end   = self.entry_end_time.get_datetime()

        if not input_start or not input_end:
            messagebox.showerror("Error", "⚠️ Please enter valid start and end times.")
            return None, None

        if input_start >= input_end:
            messagebox.showerror("Error", "⚠️ Start time must be earlier than end time.")
            return None, None

        min_seconds = 10 # TODO what should be the minimum time? frame_length + 1s at least, but should it be a few minutes? it should be at least 10 sec (swarm measurement frequency)
        if (input_end - input_start).total_seconds() < min_seconds:
            messagebox.showerror("Error", f"⚠️ Time interval must be at least {min_seconds} seconds.")
            return None, None

        return input_start, input_end

    def get_grid_parameters(self):
        try:
            return{'L': float(self.entry_L.get()), 
                   'W': float(self.entry_W.get()),
                   'Lres': float(self.entry_Wres.get()),
                   'Wres': float(self.entry_Lres.get()),
                   'wshift': float(self.entry_wshift.get())}
        except ValueError:
            print("Invalid manual input")
            return None
        
    def set_buttons_state(self, state):
        self.button_runSwarmDF.configure(state=state)
        self.button_replotinput.configure(state=state)
        self.button_apply.configure(state=state)
        self.button_runlompe.configure(state=state)
        self.button_validate.configure(state=state)

    def stop_pb(self, widget):
        """Stop and destroy progressbar if it exists"""
        if widget is not None:
            widget.stop()
            widget.destroy()

####################
####################
## Functions for triggering lompe and lompeOSSE analyses in GUI
            
    def trigger_lompe_analysis(self):
        """
        Runs Lompe when requested
        A thread is used so that the SwarmDF input results can be displayed in the GUI before Lompe is done running
        """

        # Remove intermediate "Run Lompe" button if it exists
        if self.button_runlompe_temp:
            self.button_runlompe_temp.grid_forget()

        # Progress bar for Lompe output panel #TODO see if i can move this to output_panels.py (make input progress bar work first)
        self.progress_output = customtkinter.CTkProgressBar(self.frame_output, mode="indeterminate")
        self.progress_output.grid(row=1, column=0, pady=(30, 10))
        self.progress_output.start()

        # Disable buttons until Lompe is done running
        self.input_ui["button_interactive"].configure(state="disabled")
        self.output_ui["button_interactive"].configure(state="disabled")
        self.set_buttons_state("disabled")

        def lompe_worker():
            try:
                self.output_results = compute_swarmdf_output(self.config, self.input_results) 
                self.after(0, lambda: self.display_swarmdf_output(self.output_results)) # plotting and GUI update must go through after

            except Exception as e:
                print("Lompe run failed:", e)
                # messagebox.showerror("Lompe run failed", str(e))
                self.stop_pb(self.progress_output)

        threading.Thread(target=lompe_worker, daemon=True).start()


    def wait_for_lompe_then_validate(self):
        """This allows showing the Lompe output in the main GUI window before running LompeOSSE (which takes time)"""
        
        if hasattr(self, "output_results"):
            self.after(100, self.trigger_lompeosse_analysis)
        else:
            self.after(300, self.wait_for_lompe_then_validate)
            

    def trigger_lompeosse_analysis(self):
        """Runs LompeOSSE when requested"""

        open_validation_window(self)
        self.update_idletasks()

        self.set_buttons_state("disabled")
        
        def lompeOSSE_worker():
            try:
                validation_results = compute_swarmdf_validation(self.config, self.output_results) #TODO replace with lompe_models
                self.after(0, lambda: self.display_lompeosse_validation(validation_results))

            except Exception as e:
                self.after(0, lambda: messagebox.showerror("LompeOSSE failed", str(e)))

        threading.Thread(target=lompeOSSE_worker, daemon=True).start()
    

####################
####################
# # Functions for displaying output animations in GUI

    def display_swarmdf_input(self, input_to_lompe):

        self.stop_animation(getattr(self, "master_state", None))
        self.master_state = self.init_animation_state(self.after, self.after_cancel)

        try: 
            self.input_pil_frames = render_swarmdf_input(self.config, self.datasets, input_to_lompe)

        except Exception as e:
            print("Can't load PIL images", e)
            traceback.print_exc()

            self.stop_pb(self.progress_input)

            # Display error frame
            error_img = make_error_frame(self.label_input)
            self.label_input.configure(image=error_img, text="An error occurred...")
            self.label_input.image = error_img

            if hasattr(self, "label_output"):
                self.label_output.configure(image=error_img, text="An error occurred...")
                self.label_output.image = error_img
                    
        # Convert to CTkinter images and register frames
        self.input_ctk_frames = pil_to_ctk_images(self.input_pil_frames, self.label_input)
        self.anim_mgr.register_track(self.input_ctk_frames, self.label_input, self.master_state)
        
        if hasattr(self, "frame_outputs_tk"):
            self.anim_mgr.register_track(self.output_ctk_frames, self.label_output, self.master_state)

        self.stop_pb(self.progress_input)

        # Reset play/pause buttons to match new state (useful for re-runs)
        # buttons = [self.button_playpause_input]
        # if hasattr(self, "btn_play_pause_lompe"):
        #     buttons.append(self.btn_play_pause_lompe)
        # self.update_play_pause_icons(buttons, self.master_state["playing"])

        buttons = [self.input_ui["playpause"]]
        if hasattr(self, "output_ui"):
            buttons.append(self.output_ui["playpause"])
        self.update_play_pause_icons(buttons, self.master_state["playing"])

        # Place frame controls and interactive window button
        self.input_ui["frame_controls"].place(relx=0.5, rely=0.97, anchor="center")
        self.input_ui["frame_interactive"].place(relx=0.98, rely=0.97, anchor="e")

        # Play animation
        self.anim_mgr.play_generic(state=self.master_state)


    def display_swarmdf_output(self, lompe_models):

        try:
            # Extract PIL images 
            self.output_pil_frames = render_swarmdf_output(self.config, lompe_models)

        except Exception as e:
            print("Can't load PIL images", e)
            traceback.print_exc()

            self.stop_pb(self.progress_output)

            # Display error frame
            error_img = make_error_frame(self.label_output)
            self.label_output.configure(image=error_img, text="An error occurred...")
            self.label_output.image = error_img

        # Convert to CTkinter images and register frames
        self.output_ctk_frames = pil_to_ctk_images(self.output_pil_frames, self.label_output)
        self.anim_mgr.register_track(self.output_ctk_frames, self.label_output, self.master_state)
        
        self.stop_pb(self.progress_output)

        # Place frame controls and interactive window button
        self.output_ui["frame_controls"].place(relx=0.5, rely=0.97, anchor="center")
        self.output_ui["frame_interactive"].place(relx=0.98, rely=0.97, anchor="e")
        
        # Enable buttons for interactive views once Lompe is finished
        self.input_ui["button_interactive"].configure(state="normal")
        self.output_ui["button_interactive"].configure(state="normal")

        if not self.config.run_validation_flag:
            self.set_buttons_state("normal")


    def display_lompeosse_validation(self, lompeosse_results):

        self.stop_animation(getattr(self, "validation_state", None))
        self.validation_state = self.init_animation_state(self.validation_window.after, self.validation_window.after_cancel)

        try:
            # Extract PIL images 
            self.lompeosse_pil_frames, self.gamera_pil_frames = render_swarmdf_validation(self.config, lompeosse_results)

            # Combine PIL images from both sources into single frames (useful for the interactive window)
            self.validation_combined_pil_frames = combine_validation_frames(self.lompeosse_pil_frames, self.gamera_pil_frames)

        except Exception as e:
            print("Can't load PIL images", e)
            traceback.print_exc()

            self.stop_pb(self.progress_validation)

            # Display error frame
            for label in (self.lompe_label, self.gamera_label):
                error_img = make_error_frame(label)
                label.configure(image=error_img, text="An error occurred...")
                label.image = error_img
        
        # Convert to CTkinter images and register frames
        self.lompeosse_ctk_frames = pil_to_ctk_images(self.lompeosse_pil_frames, self.frame_lompeosse)
        self.gamera_ctk_frames = pil_to_ctk_images(self.gamera_pil_frames, self.frame_gamera)
        self.anim_mgr.register_track(self.lompeosse_ctk_frames, self.lompe_label,  self.validation_state)
        self.anim_mgr.register_track(self.gamera_ctk_frames,    self.gamera_label, self.validation_state)

        self.stop_pb(self.progress_validation)

        # Place frame controls and interactive window button
        self.validation_controls.pack(side="bottom", pady=5)
        self.frame_interactive_window_val.place(relx=0.97, rely=0.92, anchor="e")

        self.set_buttons_state("normal")

        # Update validation window label
        self.status_label.configure(text="")

        # Play animation
        self.anim_mgr.play_generic(state=self.validation_state)   


    def stop_animation(self, state):
        """Stop a running animation loop for the given animation state."""
        if state is not None and state.get("job") is not None:
            self.after_cancel(state["job"])
            # state["job"] = None
            
    def init_animation_state(self, scheduler, cancel):
        """ Initialize common "clock" for input and output animations (controls the timeline for both GIFs i.e, synchronize them)"""
        
        return {"tracks": [],
                "frame_index": 0,
                "playing": True,
                "job": None,
                "delay": self.config.gif_speed, 
                "scheduler": self.after, 
                "cancel": self.after_cancel}
    
    def update_play_pause_icons(self, buttons, is_playing):
        """Update play/pause button icons to match animation state."""

        new_icon = self.icons.pause if is_playing else self.icons.play

        for btn in buttons:
            btn.configure(image=new_icon)

    def toggle_play_pause(self):
        """
        Run the play/pause function
        """
        # buttons = [self.button_playpause_input]
        # if hasattr(self, "btn_play_pause_lompe"):
        #     buttons.append(self.btn_play_pause_lompe)

        buttons = [self.input_ui["playpause"]]
        if hasattr(self, "output_ui"):
            buttons.append(self.output_ui["playpause"])


        is_playing = self.anim_mgr.toggle_play_pause_generic(state=self.master_state)
        self.update_play_pause_icons(buttons, is_playing)
            
    def toggle_play_pause_validation(self):
        
        buttons=[self.button_playpause_val]
        is_playing = self.anim_mgr.toggle_play_pause_generic(state=self.validation_state)
        self.update_play_pause_icons(buttons, is_playing)

    def prev_frame(self):
        self.anim_mgr.step_frame_generic(state=self.master_state, step=-1, toggle_callback=self.toggle_play_pause)
    def next_frame(self):
        self.anim_mgr.step_frame_generic(state=self.master_state, step=+1, toggle_callback=self.toggle_play_pause)

    def prev_frame_validation(self):
        self.anim_mgr.step_frame_generic(state=self.validation_state, step=-1, toggle_callback=self.toggle_play_pause)
    def next_frame_validation(self):
        self.anim_mgr.step_frame_generic(state=self.validation_state, step=+1, toggle_callback=self.toggle_play_pause)

####################
####################
# # Functions for opening matplotlib viewers

    def interactive_window_input(self):
        open_interactive_window(self.input_pil_frames, title="Lompe input")

    def interactive_window_output(self):
        open_interactive_window(self.output_pil_frames, title="Lompe output")

    def interactive_window_validation(self):
        open_interactive_window(self.validation_combined_pil_frames, title="LompeOSSE output (validation)", figsize=(15,10))



if __name__ == "__main__":
    app = SwarmDFGUI()
    app.mainloop()
