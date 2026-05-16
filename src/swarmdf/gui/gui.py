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
from PIL import Image
import threading

import customtkinter
customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

from swarmdf import *

from swarmdf.pipeline import get_data, compute_swarmdf_input, compute_swarmdf_output, compute_swarmdf_validation

from swarmdf.gui.config import SwarmDFConfig
from swarmdf.gui.ui.sidebar_left import build_left_sidebar
from swarmdf.gui.ui.sidebar_right import build_right_sidebar
from swarmdf.gui.ui.input_panels import build_input_panels
from swarmdf.gui.ui.output_panels import build_output_panels
from swarmdf.gui.ui.validation_window import open_validation_window
from swarmdf.gui.ui.display_helpers import compute_widget_size, pil_to_ctk_images, open_interactive_window, combine_validation_frames
from swarmdf.gui.ui.utils import validate_entry, make_error_frame, resize_keep_aspect
from swarmdf.gui.ui.animation_manager import AnimationManager
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# TODO remember to fix citation (github)

class SwarmDFGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        #############
        # Configure GUI window layout

        self.title("SwarmDF.py")
        width, height = 1660, 950
        self.aspect_ratio = 16/9 #width/height
        self.geometry(f"{width}x{height}") #{1660}x{870}
        self.minsize(1450, 780)
        # self.bind("<Configure>", self.enforce_aspect)

        self.grid_columnconfigure(1, weight=0, minsize=365)
        self.grid_columnconfigure(2, weight=4)
        self.grid_columnconfigure(3, weight=0, minsize=300)
        self.grid_rowconfigure((0, 1), weight=1)

        build_left_sidebar(self)
        build_input_panels(self)
        build_output_panels(self)     
        build_right_sidebar(self)

        #############
        # Check/validate user entries

        # TODO add more? make this better
        self.validators = [(self.entry_timestep, "Timestep", 30, None, None),
                           (self.entry_kp, "Kp index", 4, 0, 9), 
                           (self.entry_f107, "F107 value", 100, 30, 400), #TODO ok? 
                           (self.entry_background, "Background value", 2, 0, None), # TODO what's a good range?
                           (self.entry_L, "Grid length", 2000, None, None),
                           (self.entry_W, "Grid width", 1500, None, None),
                           (self.entry_Lres, "Grid length resolution", 200, None, None),
                           (self.entry_Wres, "Grid width resolution", 200, None, None),
                           (self.entry_wshift, "wshift value", 0, None, None),
                           (self.entry_gifspeed, "Animation speed", 550, 0, None),
                           (self.entry_Gtimeoff, "Time offset", 0, 0, 23), #TODO ok?
                           (self.entry_Gsnapshot, "Gamera snapshot", 0, None, None),
                           ]
        
        # Check and validate values from entries as the user types
        for entry, name, default, min_val, max_val in self.validators:
            entry.bind("<FocusOut>", lambda e, entry=entry, name=name, default=default, min_val=min_val, max_val=max_val: 
                        validate_entry(entry, name, default, min_val, max_val))
            

    #################
    # Run SwarmDF analysis

    def run_swarm_df(self):
        
        self.button_runSwarmDF.configure(state="disabled")
        self.button_interactive_wdw_input.configure(state="disabled")

        # Check and validate values from all entries before running SwarmDF
        for entry, name, default, min_val, max_val in self.validators:
            validate_entry(entry, name, default, min_val, max_val)

       # Collect user input
        self.config = self.collect_user_config()

        # Generate a Python script reproducing the SwarmDF workflow from the current configuration
        if self.config.generate_script_flag:

            # filename
            if self.entry_codename.get():
                fn= self.entry_codename.get()
            else:
                fn= 'SwarmDF_script.py'
        
            generate_python_code(self.config, fn)

        # Start progress bars
        self.progress_input = customtkinter.CTkProgressBar(self.frame_data, mode="indeterminate")
        self.progress_input.grid(row=1, column=0, pady=(30, 10))
        self.progress_input.start()

        # TODO...
        self.anim_mgr = AnimationManager()

        # Schedule heavy part of SwarmDF AFTER letting the GUI update
        self.after(100, self._do_swarm_df)
    
    def _do_swarm_df(self):
        """SwarmDF pipeline"""

        print("--- Running SwarmDF --- ")

        try: 
            # Data
            datasets = get_data(self.config)

            # Input to Lompe
            self.input_results = compute_swarmdf_input(self.config, datasets) 
            self.display_lompe_input(self.input_results)
            
            # Play animation
            self.play()

            # Lompe output
            if self.config.run_lompe_flag:
                self.lompe_button = None
                self.trigger_lompe_analysis()
            else:
                # Button for triggering Lompe
                self.lompe_button = customtkinter.CTkButton(master=self.lompe_frame, text="Run Lompe analysis", command=self.trigger_lompe_analysis, width=170, height=40)
                self.lompe_button.grid(row=1, column=0, pady=(0, 20))
                self.button_interactive_wdw_input.configure(state="normal")

            # LompeOSSE validation (once Lompe is done)
            if self.config.run_validation_flag:
                self.wait_for_lompe_then_validate()

        except Exception as e:
            print(e)
            messagebox.showerror("SwarmDF failed", str(e)) # TODO for debugging only
            print("SwarmDF failed, the following exception occured:", e) 

        finally: 
            self.button_runSwarmDF.configure(state="normal")


# -------------------------------------------------------
# -------------------------------------------------------

    #################
    # Collect GUI input 

    def collect_user_config(self):

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

        # Python script flag
        generate_script_flag = bool(self.switch_pythoncode.get())
            
        # demo mode
        demo_flag = bool(self.switch_demo.get())

        return SwarmDFConfig(sat_id,
                             start_time, end_time, timestep,
                             datasets2download,
                             conductance_method,
                             conductance_params,
                             grid_params,
                             run_lompe_flag,
                             l1, l2,
                             speed,
                             figw, figh,
                             mag,
                             show_data,
                             run_validation_flag,
                             timeoff, snapshot,
                             generate_script_flag, 
                             demo_flag)

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


    #################
    # Trigger lompe/lompeOSSE analyses

    def trigger_lompe_analysis(self):
        """Runs Lompe when requested"""

        # Progress bar
        self.progress_output = customtkinter.CTkProgressBar(self.lompe_frame, mode="indeterminate")
        self.progress_output.grid(row=1, column=0, pady=(30, 10))
        self.progress_output.start()

        # Disable interactive window buttons until Lompe is done running
        self.button_interactive_wdw_input.configure(state="disabled")
        self.button_interactive_wdw_output.configure(state="disabled")

        def worker():
            try:
                self.output_results = compute_swarmdf_output(self.config, self.input_results)
                self.after(0, lambda: self.display_lompe_output(self.output_results))

            except Exception as e:
                print("Lompe run failed:", e)
                raise RuntimeError from e    
        
        threading.Thread(target=worker, daemon=True).start()


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
        
        def worker():
            try:
                validation_results = compute_swarmdf_validation(self.config, self.output_results)
                self.after(0, lambda: self.display_lompeosse_validation(validation_results))

            except Exception as e:
                self.after(0, lambda: messagebox.showerror("LompeOSSE failed", str(e)))

        threading.Thread(target=worker, daemon=True).start()
        

    #################
    # Display output animations

    def display_lompe_input(self, input_results):

        # Kill old animation loop
        if hasattr(self, "master_state") and self.master_state.get("job") is not None:
            self.after_cancel(self.master_state["job"])
            self.master_state['job'] = None    

        try: 
            # Extract PIL images 
            self.data_frames_pil = input_results.input_PILframes

            # Convert to CTkinter images
            w, h = compute_widget_size(self.label_data_gif)
            self.data_frames_tk = pil_to_ctk_images(self.data_frames_pil, resize_keep_aspect, w, h)

            # Initialize common "clock" for input and output animations (controls the timeline for both GIFs i.e, synchronize them)
            self.master_state = {"tracks": [],
                                "current_frame": 0,
                                "playing": True,
                                "job": None,
                                "delay": self.config.gif_speed, 
                                "scheduler": self.after, 
                                "cancel": self.after_cancel}

        except Exception as e:
            print("Error running display_lompe_input:", e)

            # Replace frames with a single “error” image
            self.error_frame = make_error_frame(self.label_data_gif.winfo_width(), self.label_data_gif.winfo_height())
            error_img = customtkinter.CTkImage(light_image=self.error_frame.resize((w,h), Image.LANCZOS), size=(w,h))
            self.data_frames_tk = [error_img]

            # Display error frame
            self.anim_mgr.register_track(self.data_frames_tk,  self.label_data_gif, self.master_state)
            self.anim_mgr.update_tracks(self.master_state)

            # Also replace Lompe output if it exists from a previous run
            if hasattr(self, "label_lompe_gif"):
                self.lompe_frames_tk = [error_img]
                self.anim_mgr.register_track(self.lompe_frames_tk, self.label_lompe_gif, self.master_state)
                self.anim_mgr.update_tracks(self.master_state)

            raise RuntimeError from e
        
        # Stop progressbar
        if hasattr(self, "progress_input"):
            self.progress_input.stop()
            self.progress_input.destroy()

        # Reset play/pause buttons to match new state
        icon = self.icons.pause if self.master_state["playing"] else self.icons.play
        self.btn_play_pause_data.configure(image=icon)
        if hasattr(self, "btn_play_pause_lompe"):
            self.btn_play_pause_lompe.configure(image=icon)

        # Register/prepare frames for animated GIF
        self.anim_mgr.register_track(self.data_frames_tk,  self.label_data_gif, self.master_state)
        self.anim_mgr.update_tracks(self.master_state)

        # Place frame controls
        self.data_frame_controls.place(relx=0.5, rely=0.97, anchor="center")
        self.interactive_wdw_data.place(relx=0.98, rely=0.97, anchor="e")


    def display_lompe_output(self, output_results):

        try:
            # Extract PIL images 
            self.lompe_frames_pil = output_results.output_PILframes

            # Convert to CTkinter images
            w, h = compute_widget_size(self.label_lompe_gif)
            self.lompe_frames_tk = pil_to_ctk_images(self.lompe_frames_pil, resize_keep_aspect, w, h)

        except Exception as e:
            print("Error running display_lompe_output:", e)

            # Replace frames with a single “error” image
            self.error_frame = make_error_frame(self.label_lompe_gif.winfo_width(), self.label_lompe_gif.winfo_height())
            error_img = customtkinter.CTkImage(light_image=self.error_frame.resize((w,h), Image.LANCZOS), size=(w,h))
            self.lompe_frames_tk = [error_img]

            # Display error frame
            self.anim_mgr.register_track(self.lompe_frames_tk, self.label_lompe_gif, self.master_state)
            self.anim_mgr.update_tracks(self.master_state)

            raise RuntimeError from e
        
        # Stop progressbar
        if hasattr(self, "progress_output"):
            self.progress_output.stop()
            self.progress_output.destroy()
        
        # Register/prepare frames for animated GIF
        self.anim_mgr.register_track(self.lompe_frames_tk, self.label_lompe_gif, self.master_state)
        self.anim_mgr.update_tracks(self.master_state)

        # Place frame controls
        self.lompe_frame_controls.place(relx=0.5, rely=0.97, anchor="center")
        self.interactive_wdw_lompe.place(relx=0.98, rely=0.97, anchor="e")

        # Remove intermediate "Run Lompe" button
        if self.lompe_button:
            self.lompe_button.grid_forget()

        # Enable buttons for interactive views once Lompe is finished
        self.button_interactive_wdw_input.configure(state="normal")
        self.button_interactive_wdw_output.configure(state="normal")


    def display_lompeosse_validation(self, lompeosse_results):
        
        # Kill old animation loop
        if hasattr(self, "validation_state") and self.validation_state.get("job") is not None:
            self.after_cancel(self.validation_state["job"])
            self.validation_state['job'] = None    

        try:
            # Extract PIL images 
            self.lompeosse_frames_pil = lompeosse_results.lompeosse_PILframes
            self.gamera_frames_pil = lompeosse_results.gamera_PILframes

            # .-. TODO
            self.validation_combined_frames_pil = combine_validation_frames(self.lompeosse_frames_pil, self.gamera_frames_pil)
            
            # Convert to CTkinter images
            w1 = max(self.lompe_plot_frame.winfo_width() - 40, 1)  # 10px margin each side
            h1 = max(self.lompe_plot_frame.winfo_height(), 1)
            self.lompeosse_frames_tk = pil_to_ctk_images(self.lompeosse_frames_pil, resize_keep_aspect, w1, h1)
            w2 = max(self.gamera_plot_frame.winfo_width() - 40, 1)  # 10px margin each side
            h2 = max(self.gamera_plot_frame.winfo_height(), 1)    
            self.gamera_frames_tk = pil_to_ctk_images(self.gamera_frames_pil, resize_keep_aspect, w2, h2)

            # Initialize animation
            self.validation_state = {"tracks": [],
                                    "current_frame": 0,
                                    "playing": True,
                                    "job": None,
                                    "delay": self.config.gif_speed,
                                    "scheduler": self.validation_window.after, 
                                    "cancel": self.validation_window.after_cancel}

        except Exception as e:
            print("Error running display_lompe_input:", e)
        
            # Replace frames with a single “error” image
            self.error_frame = make_error_frame(self.lompe_label.winfo_width(), self.lompe_label.winfo_height())
            error_img1 = customtkinter.CTkImage(light_image=self.error_frame.resize((w1,h1), Image.LANCZOS), size=(w1,h1))
            self.lompeosse_frames_tk = [error_img1]
            self.error_frame = make_error_frame(self.gamera_label.winfo_width(), self.gamera_label.winfo_height())
            error_img2 = customtkinter.CTkImage(light_image=self.error_frame.resize((w2,h2), Image.LANCZOS), size=(w2,h2))
            self.gamera_frames_tk = [error_img2]

            # Display error frame
            self.anim_mgr.register_track(self.lompeosse_frames_tk,  self.lompe_label, self.master_state)
            self.anim_mgr.register_track(self.gamera_frames_tk,  self.gamera_label, self.master_state)
            self.anim_mgr.update_tracks(self.master_state)

            raise RuntimeError from e

        if hasattr(self, "progress_validation"):
            self.progress_validation.stop()
            self.progress_validation.destroy()

        # Register/prepare frames for animated GIF
        self.anim_mgr.register_track(self.lompeosse_frames_tk, self.lompe_label,  self.validation_state)
        self.anim_mgr.register_track(self.gamera_frames_tk,    self.gamera_label, self.validation_state)

        # Place frame controls
        self.validation_controls.pack(side="bottom", pady=5)
        self.interactive_wdw_validation.place(relx=0.97, rely=0.92, anchor="e")

        # Update validation window label
        self.status_label.configure(text="")

        # Play animation
        self.play_validation()


#######
# Helper functions 
        
    def keep_ratio(self, event):

        container_w = event.width
        container_h = event.height

        panel_h = (container_h - 10) // 2

        h = panel_h
        w = int(h * self.aspect_ratio)

        if w > container_w:
            w = container_w
            h = int(w / self.aspect_ratio)

        self.frame_data.configure(width=w, height=h)
        self.lompe_frame.configure(width=w, height=h)
        
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
            self.label_value_l1.configure(text=f"{log_val:.2f}")
            # TODO is l1 = exponent or 1**exponent ??

    def update_l2_label(self, slider_val):
            log_val = 10 ** slider_val # log scale
            self.label_value_l2.configure(text=f"{log_val:.2f}")
            
    def apply_new_regularization(self):

        # Get updated slider values
        self.config.l1 = 10 ** self.slider_l1.get()
        self.config.l2 = 10 ** self.slider_l2.get()

        # Run lompe with new parameters
        self.trigger_lompe_analysis()


    def interactive_window_input(self):
        open_interactive_window(self.data_frames_pil, title="Lompe input")

    def interactive_window_output(self):
        open_interactive_window(self.lompe_frames_pil, title="Lompe output")

    def interactive_window_validation(self):
        # open_interactive_window(self.lompeosse_frames_pil, title="LompeOSSE output (validation)")
        open_interactive_window(self.validation_combined_frames_pil, title="LompeOSSE output (validation)", figsize=(15,10))

    def play(self):
        self.anim_mgr.play_generic(state=self.master_state)
    def play_validation(self):
        self.anim_mgr.play_generic(state=self.validation_state)

    def toggle_play_pause(self):
        """
        Run the play/pause function + change the play/pause the icon for the outputs
        """
        buttons = [self.btn_play_pause_data]
        if hasattr(self, "btn_play_pause_lompe"):
            buttons.append(self.btn_play_pause_lompe)

        playing = self.anim_mgr.toggle_play_pause_generic(state=self.master_state, buttons=buttons)

        icon = self.icons.pause if playing else self.icons.play
        for btn in buttons:
            btn.configure(image=icon)

    def toggle_play_pause_validation(self):
        buttons=[self.btn_play_pause_validation]
        
        playing = self.anim_mgr.toggle_play_pause_generic(state=self.validation_state, buttons=buttons)

        icon = self.icons.pause if playing else self.icons.play
        for btn in buttons:
            btn.configure(image=icon)

    def prev_frame(self):
        self.anim_mgr.step_frame_generic(state=self.master_state, step=-1, toggle_callback=self.toggle_play_pause)
    def next_frame(self):
        self.anim_mgr.step_frame_generic(state=self.master_state, step=+1, toggle_callback=self.toggle_play_pause)

    def prev_frame_validation(self):
        self.anim_mgr.step_frame_generic(state=self.validation_state, step=-1, toggle_callback=self.toggle_play_pause)
    def next_frame_validation(self):
        self.anim_mgr.step_frame_generic(state=self.validation_state, step=+1, toggle_callback=self.toggle_play_pause)



if __name__ == "__main__":
    app = SwarmDFGUI()
    app.mainloop()


