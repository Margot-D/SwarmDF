"""
SwarmDF Toolbox — Graphical User Interface (GUI)

This module provides the main graphical user interface for the Swarm Data
Fusion (SwarmDF) toolbox. It is the main entry point for interacting with
SwarmDF through the GUI.

The GUI allows users to:
    1. Configure the SwarmDF input parameters.
    2. Visualize the analysis grid and available ionospheric data along the
       Swarm trajectory.
    3. Run the Lompe reconstruction.
    4. Visualize the resulting ionospheric electrodynamics.
    5. Validate the Lompe reconstruction results.
"""

import matplotlib
matplotlib.use("TkAgg") # TkAgg is required for displaying Matplotlib figures within the Tkinter GUI

import threading
import traceback
from tkinter import messagebox

import customtkinter
customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

from PIL import Image, ImageOps

from swarmdf.pipeline import get_data, compute_swarmdf_input, compute_swarmdf_output, compute_swarmdf_validation, render_swarmdf_input, render_swarmdf_output, render_swarmdf_validation
from swarmdf.gui.ui.sidebar_left import build_left_sidebar
from swarmdf.gui.ui.sidebar_right import build_right_sidebar
from swarmdf.gui.ui.input_panels import build_input_panels
from swarmdf.gui.ui.output_panels import build_plot_panels
from swarmdf.config import SwarmDFConfig, SwarmDFPlotSettings
from swarmdf.core.lompeosse_analysis import LompeOSSECancelled
import swarmdf # core functions
from swarmdf.gui.ui.helpers.animation_manager import AnimationManager
from swarmdf.gui.ui.helpers.image_display import combine_validation_frames, pil_to_ctk_images, make_error_frame, open_interactive_window
from swarmdf.gui.ui.lompeosse_validation_window import open_lompeosse_window

class SwarmDFGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # ----------------------------
        # Configure the main GUI window
        # ----------------------------
        
        self.title("SwarmDF.py")

        width, height = 1660, 950
        self.aspect_ratio = 16 / 9 # width / height
        self.geometry(f"{width}x{height}")
        self.minsize(1450, 780)
        # self.bind("<Configure>", self.enforce_aspect)

        self.grid_columnconfigure(1, weight=0, minsize=365) # left sidebar
        self.grid_columnconfigure(2, weight=4)              # central input/output panels
        self.grid_columnconfigure(3, weight=0, minsize=300) # right sidebar
        self.grid_rowconfigure((0, 1), weight=1)

        # ----------------------------
        # Build GUI components
        # ----------------------------

        build_left_sidebar(self)
        build_input_panels(self)
        build_plot_panels(self)      
        build_right_sidebar(self)

        # ----------------------------
        # Set up user input validation
        # ----------------------------

        self.setup_input_validation()

    # ----------------------------
    # Build SwarmDF configuration and plot settings
    # ----------------------------

    def build_config_from_gui(self):
        """Build the SwarmDF configuration from the current GUI inputs"""

        # Satellite ID
        sat_id = self.optmenu_satellite.get()
        
        # Time interval
        start_time = self.entry_start_time.get_datetime()
        end_time   = self.entry_end_time.get_datetime()
        
        # Time step (between frames)
        timestepp = int(self.entry_timestep.get())

        # Convert time step to seconds
        unit = self.var_timestep_unit.get()

        if unit == "min":
            timestepp *= 60
        elif unit == "h":
            timestepp *= 3600

        timestep = timestepp

        # Datasets
        datasets2download = []

        if self.checkbox_swarm_mag.get():
            datasets2download.append('swarm_mag')
        if self.checkbox_swarm_efi.get():
            datasets2download.append('swarm_efi')
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
                messagebox.showwarning("Warning", "No valid datasets available for Lompe inversion.")

        # Conductance model parameters
        kp_value = int(self.entry_kp.get()) 
        f107_value = float(self.entry_f107.get())
        background_value = float(self.entry_background.get())

        conductance_params = {"kp": kp_value, "f107": f107_value, "background": background_value}
        conductance_method = str(self.optmenu_conductance.get())

        # Grid parameters
        grid_params = {'L': float(self.entry_L.get()), 
                       'W': float(self.entry_W.get()),
                       'Lres': float(self.entry_Lres.get()),
                       'Wres': float(self.entry_Wres.get()),
                       'wshift': float(self.entry_wshift.get())}

        # Lompe reconstruction options
        run_lompe_flag = bool(self.checkbox_runlompe.get())
        l1 = 10 ** self.slider_l1.get() # convert the log10 slider values to the regularization values used by Lompe
        l2 = 10 ** self.slider_l2.get()

        # LompeOSSE validation options
        run_validation_flag = bool(self.checkbox_lompeosse.get())
        time_offset = int(self.entry_Gtimeoff.get())
        snapshot = int(self.optmenu_Gsnapshot.get())

        return SwarmDFConfig(sat_id=sat_id,
                             start_time=start_time, end_time=end_time, timestep=timestep,
                             datasets2download=datasets2download,
                             grid_params=grid_params,
                             run_lompe_flag=run_lompe_flag,
                             conductance_method=conductance_method,
                             conductance_params=conductance_params,
                             regularization_l1=l1, regularization_l2=l2,
                             run_validation_flag=run_validation_flag,
                             time_offset=time_offset, snapshot=snapshot)

    def build_plot_settings_from_gui(self):
        """Build the SwarmDF plotting settings from the current GUI inputs"""

        # Figure size
        figh = float(self.entry_figh.get())

        # Coordinate system used for the polar plot
        mag = bool(self.checkbox_magcoords.get())

        # Show data outside the selected grid
        show_data = bool(self.checkbox_showdata.get())

        # GIF speed
        speed = self.apply_gif_parameters(update_state=False) # ms/frame

        return SwarmDFPlotSettings(generate_input_plots=True,
                                   mag_coords_flag=mag,
                                   show_all_data_flag=show_data,
                                   figh=figh,
                                   generate_gifs=True,
                                   gif_speed=speed)

    # ----------------------------
    # Input validation
    # ----------------------------
        
    def setup_input_validation(self):
        """Set up validation rules and validate entries when focus leaves a field"""

        # Define validation rules, default values, and allowed ranges for GUI entries 
        self.validators = [("satellite", self.optmenu_satellite), 
                           ("time interval", self.entry_start_time, self.entry_end_time),
                           ("other entries", self.entry_timestep, "Timestep", self.default_timestep, 5, None),
                           ("other entries", self.entry_kp, "Kp index", self.default_kp, 0, 9), 
                           ("other entries", self.entry_f107, "F10.7 value (s.f.u)", self.default_f107, 30, 400),
                           ("other entries", self.entry_background, "Background value", self.default_background, 0, None), 
                           ("other entries", self.entry_L, "Grid along-track dimension", self.default_L, None, None),
                           ("other entries", self.entry_W, "Grid cross-track dimension", self.default_W, None, None),
                           ("other entries", self.entry_Lres, "Grid along-track resolution", self.default_Lres, None, None),
                           ("other entries", self.entry_Wres, "Grid cross-track resolution", self.default_Wres, None, None),
                           ("other entries", self.entry_wshift, "Cross-track shift value", self.default_wshift, None, None),
                           ("other entries", self.entry_gifspeed, "Animation speed", self.default_gif_speed, 0, None),
                           ("other entries", self.entry_Gtimeoff, "Time offset", self.default_Gtimeoff, 0, 23)]

        # Validate entries automatically when the user leaves the corresponding field
        for args in self.validators:
            kind = args[0]
            if kind == "other entries":
                entry, name, default, min_val, max_val = args[1:]
                entry.bind("<FocusOut>", lambda e, entry=entry, name=name, default=default, min_val=min_val, max_val=max_val: 
                           self.validate_entry("other entries", entry, name, default, min_val, max_val))

    def validate_entry(self, kind, *args):
        """Validate a GUI input and return whether it is valid"""

        if kind == "satellite":
            widget = args[0]
            value = widget.get()

            if value == "Satellite ID":
                messagebox.showerror("Invalid input", 
                                     "Please select a valid Satellite ID (Swarm A, B, or C) and press Run SwarmDF again.", 
                                     icon='warning')
                return False
            
            return True
        
        elif kind == "time interval":
            start_widget, end_widget = args

            start = start_widget.get_datetime()
            end = end_widget.get_datetime()

            if not start or not end:
                messagebox.showerror("Invalid input", "Please enter valid start and end times.", icon='warning')
                return False

            if start >= end:
                messagebox.showerror("Invalid input", "Start time must be earlier than end time.", icon='warning')
                return False

            # Require an interval long enough to contain at least one valid Swarm measurement interval (swarm measurement frequency)
            min_seconds = 5
            if (end - start).total_seconds() < min_seconds:
                messagebox.showerror("Invalid input", f"Time interval must be at least " f"{min_seconds} seconds.")
                return False

            return True
        
        elif kind == "other entries":
            entry, name, default, min_val, max_val = args

            try:
                value = float(entry.get())
            except ValueError:
                value = default
                messagebox.showwarning("Invalid input", f"{name} is invalid. Using default value: {default}")
                
                # Replace the invalid value with the default in the GUI
                entry.delete(0, "end")
                entry.insert(0, str(default))

                return False

            if min_val is not None and value < min_val:
                messagebox.showwarning("Invalid input", f"{name} must be ≥ {min_val}. Using default: {default}")
                value = default

                # Replace the out-of-range value with the default in the GUI
                entry.delete(0, "end")
                entry.insert(0, str(default))

                return False
            
            if max_val is not None and value > max_val:
                messagebox.showwarning("Invalid input", f"{name} must be ≤ {max_val}. Using default: {default}")
                value = default

                # Replace the out-of-range value with the default in the GUI
                entry.delete(0, "end")
                entry.insert(0, str(default))

                return False

        return True

    # ----------------------------
    # GUI state and updates
    # ----------------------------

    def set_buttons_state(self, state):
        """Enable or disable GUI buttons"""

        self.button_runSwarmDF.configure(state=state)
        self.button_replotinput.configure(state=state)
        self.button_apply.configure(state=state)
        self.button_runlompe.configure(state=state)
        self.button_validate.configure(state=state)
        self.button_expl_event.configure(state=state)
        self.button_reset_event.configure(state=state)

    def apply_gif_parameters(self, update_state=True):
        """Udate animation state with new GIF speed"""

        speed = int(self.entry_gifspeed.get())

        if update_state:
            if hasattr(self, "master_state"):
                self.master_state["delay"] = speed
            if hasattr(self, "validation_state"):
                self.validation_state["delay"] = speed

            print(f"Animation speed set to {speed} ms per frame")

        return speed
    
    def update_lompe_input(self):
        """Apply updated input-plot settings and refresh the input display"""

        self.plot_settings.mag_coords_flag = bool(self.checkbox_magcoords.get())
        self.plot_settings.show_all_data_flag = bool(self.checkbox_showdata.get())
        self.plot_settings.figh = float(self.entry_figh.get())

        self.display_swarmdf_input(self.input_results)

    def update_l1_label(self, slider_val):
        """Update the displayed L1 regularization value"""

        log_val = 10 ** slider_val # log scale
        self.value_l1.configure(text=f"{log_val:.2f}")

    def update_l2_label(self, slider_val):
        """Update the displayed L2 regularization value"""

        log_val = 10 ** slider_val # log scale
        self.value_l2.configure(text=f"{log_val:.2f}")

    def apply_new_regularization(self):
        """Apply the selected regularization values and rerun Lompe"""

        self.config.regularization_l1 = 10 ** self.slider_l1.get()
        self.config.regularization_l2 = 10 ** self.slider_l2.get()

        self.trigger_lompe_analysis()

    def stop_progressbar(self, widget):
        """Stop and hide progressbar if it exists"""
        
        if widget is None:
            return
        
        widget.stop()

        if widget.winfo_manager() == "grid":
            widget.grid_remove()
        elif widget.winfo_manager() == "pack":
            widget.pack_forget()
        elif widget.winfo_manager() == "place":
            widget.place_forget()

    # ----------------------------
    # SwarmDF workflow
    # ----------------------------

    def start_swarmdf(self):
        """Initiate a SwarmDF run"""

        # Revalidate all inputs before starting the workflow 
        for validator in self.validators:
            ok = self.validate_entry(*validator)
            if not ok:
                return
            
        # Build the SwarmDF configuration and plotting settings from the GUI
        self.config = self.build_config_from_gui()
        self.plot_settings = self.build_plot_settings_from_gui()

        # Optionally generate a standalone Python script reproducing the current SwarmDF workflow and configuration
        if self.switch_pythonscript.get():
            fn = self.entry_filename.get() if self.entry_filename.get() else 'SwarmDF_script.py' # default file name
            swarmdf.generate_python_code(self.config, self.plot_settings, fn)

        # Disable buttons while SwarmDF is running 
        self.set_buttons_state("disabled")

        # Start the input progress indicator
        self.progress_input.grid()
        self.progress_input.start()

        # Create the animation manager used to handle generated plots/GIFs
        self.anim_mgr = AnimationManager()

        # Give Tkinter time to update the GUI before starting the SwarmDF pipeline
        self.after(100, self._run_swarmdf_pipeline)
    
    def _run_swarmdf_pipeline(self):
        """Run the SwarmDF workflow"""

        print("--- Running SwarmDF --- ")

        lompe_started = False

        try: 
            # Retrieve input data using either the selected datasets or demo data
            is_demo = bool(self.switch_demo.get())
            self.datasets = get_data(self.config, use_sample_data=is_demo)

            # Prepare the data required for the Lompe reconstruction
            self.input_results = compute_swarmdf_input(self.datasets, self.config) 
            self.display_swarmdf_input(self.input_results)

            # Start the Lompe reconstruction if requested
            if self.config.run_lompe_flag:
                lompe_started = True
                self.trigger_lompe_analysis()
            else:
                self.button_runlompe_temp.grid()

            # Start validation once the Lompe reconstruction is complete, if requested
            if self.config.run_validation_flag:
                self.wait_for_lompe_then_validate()

        except Exception as e:
            messagebox.showerror("Error", f"SwarmDF failed: {str(e)}", icon='error')
            print("SwarmDF failed, the following exception occurred:", e) 

        finally:
            # Stop the input progress indicator when the initial processing finishes
            self.stop_progressbar(self.progress_input)

            # Re-enable controls if no Lompe analysis is running
            if not lompe_started:
                self.set_buttons_state("normal")

    # ----------------------------
    # Lompe and LompeOSSE workflow 
    # ----------------------------

    def finish_lompe(self):
        self.set_buttons_state("normal")
        self.stop_progressbar(self.progress_output)

    def trigger_lompe_analysis(self):
        """
        Run the Lompe reconstruction in a background thread (keeps GUI responsive while Lompe is running)
        """

        # Remove intermediate "Run Lompe" button if it exists
        if self.button_runlompe_temp:
            self.button_runlompe_temp.grid_remove()

        # Start the Lompe progress indicator
        self.progress_output.grid()
        self.progress_output.start()

        # Disable buttons while Lompe is running
        self.input_ui["button_interactive"].configure(state="disabled")
        self.output_ui["button_interactive"].configure(state="disabled")
        self.set_buttons_state("disabled")

        def lompe_worker():
            try:
                self.output_results = compute_swarmdf_output(self.input_results, self.config) 
                self.after(0, lambda: self.display_swarmdf_output(self.output_results)) # Plotting and GUI updates must run on the Tkinter main thread

            except Exception as e:
                print("Lompe run failed:", e)
                self.after(0, lambda e=e: messagebox.showerror("Error", f"Lompe run failed: {e}"))

            finally:
                self.after(0, self.finish_lompe)

        threading.Thread(target=lompe_worker, daemon=True).start()

    def wait_for_lompe_then_validate(self):
        """
        Start LompeOSSE validation once the Lompe results are available.
        This allows the Lompe output to be displayed before the validation starts.
        """
        
        if hasattr(self, "output_results"):
            self.after(100, self.trigger_lompeosse_analysis)
        else:
            self.after(300, self.wait_for_lompe_then_validate)

    def finish_lompeosse(self, close_window):
        """Finish the LompeOSSE analysis and optionally close the window"""

        self.lompeosse_running = False
        self.set_buttons_state("normal")
        self.stop_progressbar(self.progress_lompeosse)

        if close_window and self.lompeosse_window.winfo_exists():
            self.lompeosse_window.destroy()

    def trigger_lompeosse_analysis(self):
        """Run the LompeOSSE validation in a background thread"""

        # Update validation parameters from the GUI
        self.config.time_offset = int(self.entry_Gtimeoff.get())
        self.config.snapshot = int(self.optmenu_Gsnapshot.get())

        open_lompeosse_window(self)
        self.update_idletasks()

        self.set_buttons_state("disabled")

        self.lompeosse_running = True
        self.lompeosse_cancel_event = threading.Event()
        
        def lompeOSSE_worker():
            try:
                validation_results = compute_swarmdf_validation(self.output_results, self.config, cancel_event=self.lompeosse_cancel_event)
                # self.after(0, lambda: self.display_lompeosse(validation_results)) # Plotting and GUI updates must run on the Tkinter main thread

                # Display the result if the analysis completed normally
                self.after(0, lambda: self.display_lompeosse(validation_results)) # Plotting and GUI updates must run on the Tkinter main thread

                self.after(0, self.finish_lompeosse, False)

            except LompeOSSECancelled:
                print("LompeOSSE analysis cancelled!")

                # Close the window after cancellation
                self.after(0, self.finish_lompeosse, True)

            except Exception as e:
                print("LompeOSSE run failed:", e)
                self.after(0, lambda e=e: messagebox.showerror("Error", f"LompeOSSE run failed: {e}"))

                # Close the window after an error
                self.after(0, self.finish_lompeosse, True)

            # finally:
            #     self.after(0, self.finish_lompeosse)

        threading.Thread(target=lompeOSSE_worker, daemon=True).start()

    # ----------------------------
    # Display and animation
    # ----------------------------

    def display_swarmdf_input(self, input_to_lompe):
        """Render and display SwarmDF input results in the GUI"""

        # Stop any existing input animation and create a new animation state
        self.stop_animation(getattr(self, "master_state", None))
        self.master_state = self.init_animation_state(self.after, self.after_cancel)

        try: 
            # Render input results and load the generated images
           input_png_frames = render_swarmdf_input(input_to_lompe, self.plot_settings)
           self.input_pil_frames = [ImageOps.expand(Image.open(fn), border=15, fill="white") for fn in input_png_frames]

        except Exception as e:
            print("Can't load PIL images", e)
            traceback.print_exc()

            # self.stop_progressbar(self.progress_input)

            # Display error frame
            error_img = swarmdf.make_error_frame(self.label_input)
            self.label_input.configure(image=error_img, text="An error occurred...")
            self.label_input.image = error_img

            if hasattr(self, "label_output"):
                self.label_output.configure(image=error_img, text="An error occurred...")
                self.label_output.image = error_img
                    
        # Convert images to CTkImage and register them with the animation manager
        self.input_ctk_frames = pil_to_ctk_images(self.input_pil_frames, self.label_input)
        self.anim_mgr.register_track(self.input_ctk_frames, self.label_input, self.master_state)
        
        if hasattr(self, "frame_outputs_tk"): #TODO check if useful?? i think it is for when running lompe after intial swarmdf run 
            self.anim_mgr.register_track(self.output_ctk_frames, self.label_output, self.master_state)

        # Update animation icons
        buttons = [self.input_ui["playpause"]]
        if hasattr(self, "output_ui"):
            buttons.append(self.output_ui["playpause"])
        self.update_play_pause_icons(buttons, self.master_state["playing"])

        # Place controls and interactive window button
        self.input_ui["frame_controls"].place(relx=0.5, rely=0.97, anchor="center")
        self.input_ui["frame_interactive"].place(relx=0.98, rely=0.97, anchor="e")

        # Play animation
        self.anim_mgr.play_generic(state=self.master_state)

    def display_swarmdf_output(self, lompe_output):
        """Render and display Lompe output results in the GUI"""

        try:
            # Render input results and load the generated images
            output_png_frames = render_swarmdf_output(lompe_output, self.plot_settings)
            self.output_pil_frames = [ImageOps.expand(Image.open(fn), border=15, fill="white") for fn in output_png_frames]

        except Exception as e:
            print("Can't load PIL images", e)
            traceback.print_exc()

            # self.stop_progressbar(self.progress_output)

            # Display error frame
            error_img = make_error_frame(self.label_output)
            self.label_output.configure(image=error_img, text="An error occurred...")
            self.label_output.image = error_img

        # Convert images to CTkImage and register them with the animation manager
        self.output_ctk_frames = pil_to_ctk_images(self.output_pil_frames, self.label_output)
        self.anim_mgr.register_track(self.output_ctk_frames, self.label_output, self.master_state)
        
        # Place controls and interactive window button
        self.output_ui["frame_controls"].place(relx=0.5, rely=0.97, anchor="center")
        self.output_ui["frame_interactive"].place(relx=0.98, rely=0.97, anchor="e")
        
        # Enable buttons for interactive views once Lompe is finished
        self.input_ui["button_interactive"].configure(state="normal")
        self.output_ui["button_interactive"].configure(state="normal")

    def display_lompeosse(self, swarmdf_validation):
        """Render and display LompeOSSE analysis results in the GUI"""

        # Stop any existing input animation and create a new animation state
        self.stop_animation(getattr(self, "validation_state", None))
        self.validation_state = self.init_animation_state(self.lompeosse_window.after, self.lompeosse_window.after_cancel)

        try:
            # Render input results and load the generated images
            lompeosse_png_frames, gamera_png_frames, self.validation_png_frames = render_swarmdf_validation(swarmdf_validation, self.plot_settings)
            self.lompeosse_pil_frames = [ImageOps.expand(Image.open(fn), border=15, fill="white") for fn in lompeosse_png_frames]
            self.gamera_pil_frames = [ImageOps.expand(Image.open(fn), border=15, fill="white") for fn in gamera_png_frames]

            # Combine LompeOSSE and Gamera frames for the interactive viewer
            self.validation_combined_pil_frames = combine_validation_frames(self.lompeosse_pil_frames, self.gamera_pil_frames)

        except Exception as e:
            print("Can't load PIL images", e)
            traceback.print_exc()

            # self.stop_progressbar(self.progress_lompeosse)

            # Display error frame
            for label in (self.label_lompeosse, self.label_gamera):
                error_img = make_error_frame(label)
                label.configure(image=error_img, text="An error occurred...")
                label.image = error_img
        
        # Convert images to CTkImage and register them with the animation manager
        self.lompeosse_ctk_frames = pil_to_ctk_images(self.lompeosse_pil_frames, self.frame_lompeosse)
        self.gamera_ctk_frames = pil_to_ctk_images(self.gamera_pil_frames, self.frame_gamera)
        self.anim_mgr.register_track(self.lompeosse_ctk_frames, self.label_lompeosse, self.validation_state)
        self.anim_mgr.register_track(self.gamera_ctk_frames, self.label_gamera, self.validation_state)

        # Update animation icons
        buttons = [self.button_playpause_lompeosse]
        self.update_play_pause_icons(buttons, self.validation_state["playing"])

        # Place controls, interactive window button and validation metrics button
        self.bottom_panel_lompeosse.pack(side="bottom", fill="x", pady=2)
        self.plot_container.pack_configure(fill="both",
                                        expand=True
                                    )
        self.lompeosse_window.update_idletasks()

        # Update lompeosse window label
        self.status_label.configure(text="")

        # Play animation
        self.anim_mgr.play_generic(state=self.validation_state)   

    def display_validation(self):
        """Display the LompeOSSE validation metrics in the GUI"""

        # Convert images to CTkImage and register them with the animation manager
        self.validation_pil_frames = [ImageOps.expand(Image.open(fn), border=15, fill="white") for fn in self.validation_png_frames]
        self.validation_ctk_frames = pil_to_ctk_images(self.validation_pil_frames, self.frame_validation)
        self.validation_track = self.anim_mgr.register_track(self.validation_ctk_frames, self.label_validation, self.validation_state)

        # Show the current shared frame immediately
        i = self.validation_state["frame_index"]
        frame = self.validation_ctk_frames[i % len(self.validation_ctk_frames)]
        self.label_validation.configure(image=frame, text="")
        self.label_validation.image = frame

        # Update animation icons
        buttons = [self.button_playpause_val]
        self.update_play_pause_icons(buttons, self.validation_state["playing"])

    # ----------------------------
    # Animation controls
    # ----------------------------

    def stop_animation(self, state):
        """Stop a running animation loop for the given animation state"""
        if state is not None and state.get("job") is not None:
            self.after_cancel(state["job"])
            # state["job"] = None
            
    def init_animation_state(self, scheduler, cancel):
        """Create shared state for synchronized animations"""

        return {"tracks": [],
                "frame_index": 0,
                "playing": True,
                "job": None,
                "delay": self.plot_settings.gif_speed, 
                "scheduler": scheduler, #self.after, 
                "cancel": cancel} #self.after_cancel}
    
    def update_play_pause_icons(self, buttons, is_playing):
        """Update play/pause button icons to match animation state"""

        new_icon = self.icons.pause if is_playing else self.icons.play

        for btn in buttons:
            btn.configure(image=new_icon)

    def toggle_play_pause(self):
        """Toggle the input/output animation and update their buttons"""

        buttons = [self.input_ui["playpause"]]
        if hasattr(self, "output_ui"):
            buttons.append(self.output_ui["playpause"])

        is_playing = self.anim_mgr.toggle_play_pause_generic(state=self.master_state)
        self.update_play_pause_icons(buttons, is_playing)
            
    def toggle_play_pause_validation(self):
        """Toggle the shared LompeOSSE/validation animation and update both buttons"""

        is_playing = self.anim_mgr.toggle_play_pause_generic(state=self.validation_state)

        buttons = []

        if hasattr(self, "button_playpause_lompeosse"):
            buttons.append(self.button_playpause_lompeosse)

        if (hasattr(self, "button_playpause_val") 
            and self.button_playpause_val is not None
            and self.button_playpause_val.winfo_exists()):
            buttons.append(self.button_playpause_val)

        self.update_play_pause_icons(buttons, is_playing)

    def prev_frame(self):
        """Show the previous input/output animation frame"""
        self.anim_mgr.step_frame_generic(state=self.master_state, step=-1, toggle_callback=self.toggle_play_pause)

    def next_frame(self):
        """Show the next input/output animation frame"""
        self.anim_mgr.step_frame_generic(state=self.master_state, step=+1, toggle_callback=self.toggle_play_pause)

    def prev_frame_validation(self):
        """Show the previous LompeOSSE/validation animation frame"""
        self.anim_mgr.step_frame_generic(state=self.validation_state, step=-1, toggle_callback=self.toggle_play_pause_validation)

    def next_frame_validation(self):
        """Show the next LompeOSSE/validation animation frame"""
        self.anim_mgr.step_frame_generic(state=self.validation_state, step=+1, toggle_callback=self.toggle_play_pause_validation)

    # ----------------------------
    # Interactive plot viewers
    # ----------------------------

    def interactive_window_input(self):
        open_interactive_window(self.input_pil_frames, title="Lompe input")

    def interactive_window_output(self):
        open_interactive_window(self.output_pil_frames, title="Lompe output")

    def interactive_window_lompeosse(self):
        open_interactive_window(self.validation_combined_pil_frames, title="LompeOSSE output", figsize=(15,10))

    def interactive_window_validation(self):
        open_interactive_window(self.validation_pil_frames, title="LompeOSSE validation metrics", figsize=(15,10))

    # ----------------------------
    # GUI layout
    # ----------------------------

    def keep_ratio(self, event):
        """Maintain the output frame aspect ratio when the window is resized"""

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

def main():
    app = SwarmDFGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
