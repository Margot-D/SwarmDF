"""
SwarmDF Toolbox — Graphical User Interface (GUI)

#TODO make this better
This script launches the graphical user interface for the Swarm Data Fusion (SwarmDF) toolbox.
From here, the user can 1) configure input parameters, 2) visualize their defined grid along the Swarm trajectory as well as the available ionospheric data around it, 3) run the Lompe reconstruction process, 
4) visualize the resulting ionospheric electrodynamics, and 5) verify the Lompe output. This serves as the main 
entry point for interacting with the toolbox.
"""

import customtkinter
import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar
from PIL import Image, ImageTk, ImageDraw

from datetime import datetime, date
import os
from pathlib import Path

import webbrowser

from swarm_orbit_and_grid import swarm_trajectory
from data_collect import DataManager
from lompe_analysis import run_lompe, lompe_output
from conductance import compute_conductances
from lompeOSSE_analysis import run_lompeOSSE, lompeOSSE_output
from code_generator import build_config_dict, generate_python_code

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

import warnings
warnings.filterwarnings("ignore", message="Ignoring fixed y limits to fulfill fixed data aspect*")

##########
# TODO:
# add error messages for potential problems
# block user if the swarm trajectoy/their grid goes equatorward of 50 deg lat
# add info boxes when hovering mouse on top of for example "epoch" (short explanation of what this if for)

# fix number of steps for sliders

# Main toolbox class
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("SwarmDF.py") # TODO should be same name as final python module
        self.geometry(f"{1660}x{950}") #{1660}x{870}

        # configure grid layout
        self.grid_columnconfigure((1,2), weight=4)
        self.grid_columnconfigure(3, weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        #############
        # SIDEBAR
        #############

        self.frame_sidebar = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.frame_sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.frame_sidebar.grid_rowconfigure(7, weight=1)

        self.title_sidebar = customtkinter.CTkLabel(self.frame_sidebar, text="SwarmDF \n User interface", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.title_sidebar.grid(row=0, column=0, padx=20, pady=(20, 50))

        # "Show data coverage" checkbox
        self.checkbox_showdata = customtkinter.CTkCheckBox(self.frame_sidebar, text='Show data coverage')
        self.checkbox_showdata.grid(row=2, column=0, padx=20, pady=20)
        self.checkbox_showdata.select()

        # "Run Lompe analysis" checkbox
        self.checkbox_runlompe = customtkinter.CTkCheckBox(master=self.frame_sidebar, text=f"Run Lompe analysis")
        self.checkbox_runlompe.grid(row=3, column=0, padx=20, pady=20)
        self.checkbox_runlompe.select()

        # "Run LompeOSSE validation" checkbox
        self.checkbox_lompeosse = customtkinter.CTkCheckBox(self.frame_sidebar, text='Run LompeOSSE validation')
        self.checkbox_lompeosse.grid(row=4, column=0, padx=20, pady=20)
        # self.checkbox_lompeosse.select()

        # "Generate Python code" switch
        self.var_generate_code = tk.BooleanVar(value=False)
        self.switch_pythoncode = customtkinter.CTkSwitch(master=self.frame_sidebar, text=f"Generate Python code", variable=self.var_generate_code) 
        self.switch_pythoncode.grid(row=5, column=0, padx=20, pady=10)

        # "Run SwarmDF" button
        self.button_runSwarmDF = customtkinter.CTkButton(self.frame_sidebar, 
                                                         command=self.run_swarm_df, 
                                                         text='Run SwarmDF',
                                                         width=160, height=80, font=("Arial", 18))
        self.button_runSwarmDF.grid(row=7, column=0, padx=20, pady=20)
       
        # Apparence mode 
        self.label_appearance_mode = customtkinter.CTkLabel(self.frame_sidebar, text="Appearance Mode:", anchor="w")
        self.label_appearance_mode.grid(row=8, column=0, padx=20, pady=(10, 0))
        self.optmenu_appearance_mode = customtkinter.CTkOptionMenu(self.frame_sidebar, 
                                                                   values=["Light", "Dark", "System"],
                                                                   command=self.change_appearance_mode)
        self.optmenu_appearance_mode.grid(row=9, column=0, padx=20, pady=(10, 10))
        self.optmenu_appearance_mode.set("Dark")

        # Scaling option
        self.label_scaling = customtkinter.CTkLabel(self.frame_sidebar, text="UI Scaling:", anchor="w")
        self.label_scaling.grid(row=10, column=0, padx=20, pady=(10, 0))
        self.optmenu_scaling = customtkinter.CTkOptionMenu(self.frame_sidebar, 
                                                           values=["80%", "90%", "100%", "110%", "120%"],
                                                           command=self.change_scaling)
        self.optmenu_scaling.grid(row=11, column=0, padx=20, pady=(10, 20))
        self.optmenu_scaling.set("100%")

        #############
        # COLUMN 1/TOP ROW (INPUT)
        #############
        
        col1_width = 65

        self.tabview = customtkinter.CTkTabview(self, width=col1_width)
        self.tabview.grid(row=0, column=1, padx=(20, 0), pady=(8, 0), sticky="nsew")
        tab1 = "Main input"
        tab2 = "Datasets"
        tab3 = "Conductances"
        self.tabview.add(tab1)
        self.tabview.add(tab2)
        self.tabview.add(tab3)
        self.tabview.tab(tab1).grid_columnconfigure(0, weight=1)
        self.tabview.tab(tab2).grid_columnconfigure((0,1), weight=2)
        self.tabview.tab(tab3).grid_columnconfigure(0, weight=2)
        self.tabview.grid_propagate(False)

        #######
        # TAB 1 
        
        # TODO add suggestion on okay time range (somwhere between a few minutes and..?) --> test (min time is frame step!)
        # TODO depending on when/where, the gif does not really work... --> test many different options 
        # also, interval can't be too long! (8 hours does not work)

        # Satellite ID
        self.optmenu_satellite = customtkinter.CTkOptionMenu(self.tabview.tab(tab1), dynamic_resizing=False,
                                                             values=["Swarm A", "Swarm B", "Swarm C"])
        self.optmenu_satellite.grid(row=0, column=0, padx=(10,10), pady=(20, 10))
        self.optmenu_satellite.set("Satellite ID")

        # self.label_swarmsat = customtkinter.CTkLabel(self.tabview.tab(tab1), text="Swarm satellite(s):")
        # self.label_swarmsat.grid(row=0, column=0, padx=20, pady=15, sticky="w")  

        # # Frame for checkboxes
        # self.checkbox_frame = customtkinter.CTkFrame(self.tabview.tab(tab1), fg_color="transparent")  # transparent to blend with background
        # self.checkbox_frame.grid(row=0, column=0, padx=(150,0), pady=15, sticky="w")

        # # Variables for checkbox states
        # self.checkbox_swarmA_var = tk.BooleanVar()
        # self.checkbox_swarmB_var = tk.BooleanVar()
        # self.checkbox_swarmC_var = tk.BooleanVar()

        # # Checkboxes inside the frame
        # self.checkbox_swarmA = customtkinter.CTkCheckBox(master=self.checkbox_frame, text="A", variable=self.checkbox_swarmA_var, width=30)
        # self.checkbox_swarmA.grid(row=0, column=0, padx=(0,10))
        # self.checkbox_swarmB = customtkinter.CTkCheckBox(master=self.checkbox_frame, text="B", variable=self.checkbox_swarmB_var, width=30)
        # self.checkbox_swarmB.grid(row=0, column=1, padx=(0,10))
        # self.checkbox_swarmC = customtkinter.CTkCheckBox(master=self.checkbox_frame, text="C", variable=self.checkbox_swarmC_var, width=30)
        # self.checkbox_swarmC.grid(row=0, column=2, padx=(0,10))      
            
        # Start time entry
        self.entry_start_time = DateTimeEntry(self.tabview.tab(tab1), label="Start time:")
        self.entry_start_time.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        # End time
        self.entry_end_time = DateTimeEntry(self.tabview.tab(tab1), label="End time:")
        self.entry_end_time.grid(row=2, column=0, padx=20, pady=3, sticky="w")
        self.entry_end_time.link_datetime_entries(self.entry_start_time, self.entry_end_time)

        # Time step
        self.label_timestep = customtkinter.CTkLabel(self.tabview.tab(tab1), text="Time steps (s):")
        self.label_timestep.grid(row=3, column=0, padx=20, pady=3, sticky="w")
        self.entry_timestep = customtkinter.CTkEntry(self.tabview.tab(tab1), width=40)
        self.entry_timestep.grid(row=3, column=0, pady=15)        
        self.entry_timestep.insert(0, 30) # default: 30s #TODO looks like 10s make things bug. What should be the min? maybe because the swarm data resolution is 10s
        # check if true. if so add info box that syas min = 10

        # "Set example date" button         
        customtkinter.CTkButton(
            self.tabview.tab(tab1),
            text="Use example event",
            command=self.load_example_date,
            width=40,
            height=8,
            fg_color="#888888",      # medium grey background
            hover_color="#AAAAAA",   # slightly lighter on hover
            font=customtkinter.CTkFont(size=13)
        ).grid(row=5, column=0, pady=(15, 10))

        # "Reset date to placeholders" button
        customtkinter.CTkButton(
            self.tabview.tab(tab1),
            text="Reset to placeholders",
            command=self.reset_dates, 
            width=40,
            height=8,
            fg_color="#888888",      # medium grey background
            hover_color="#AAAAAA",   # slightly lighter on hover
            font=customtkinter.CTkFont(size=13)
        ).grid(row=6, column=0, pady=(0, 15))

        # Link to Swarm aurora website
        self.link_find_conjunction = customtkinter.CTkLabel(
            self.tabview.tab(tab1),
            text="Find conjunction with Swarm-Aurora",
            text_color="green",      
            cursor="hand2")
        self.link_find_conjunction.grid(row=7, column=0, padx=35, pady=(5, 5), sticky="nsew") #pady=(25, 5)
        self.link_find_conjunction.bind("<Button-1>", lambda e: webbrowser.open("https://swarm-aurora.com/"))

        #######
        # TAB 2

        # Datasets 
        # TODO add dmsp datasets
        # TODO get the correct electric field data (ask Spencer), this is along-track track, meaning i need a los component (which should simply be the direction of the satellite). kalle said this should be available on viresclient. 

        self.checkbox_swarm_efield = customtkinter.CTkCheckBox(master=self.tabview.tab(tab2), text='Swarm efield')
        self.checkbox_swarm_efield.grid(row=3, column=0, pady=(60, 20), padx=10, sticky="n")

        self.checkbox_swarm_bfield = customtkinter.CTkCheckBox(master=self.tabview.tab(tab2), text='Swarm bfield')
        self.checkbox_swarm_bfield.grid(row=3, column=1, pady=(60, 20), padx=10, sticky="n")

        self.checkbox_supermag = customtkinter.CTkCheckBox(master=self.tabview.tab(tab2), text='SuperMAG')
        self.checkbox_supermag.grid(row=4, column=0, pady=(20, 20), padx=10, sticky="n")

        self.checkbox_superdarn = customtkinter.CTkCheckBox(master=self.tabview.tab(tab2), text='SuperDARN')
        self.checkbox_superdarn.grid(row=4, column=1, pady=(20, 20), padx=10, sticky="n")

        self.checkbox_iridium_ampere = customtkinter.CTkCheckBox(master=self.tabview.tab(tab2), text='Iridium/AMPERE')
        self.checkbox_iridium_ampere.grid(row=5, column=0, pady=(20, 20), padx=10, sticky="n")

        # self.entry_data = customtkinter.CTkEntry(self.tabview.tab(tab2), placeholder_text="myfile.cdf") # TODO remove if not fixed
        # self.entry_data.grid(row=5, column=1, columnspan=1, pady=(20, 20), padx=10, sticky="n")

        # Default: select all datasets
        self.checkbox_swarm_efield.select()
        self.checkbox_swarm_bfield.select()
        self.checkbox_supermag.select()
        self.checkbox_superdarn.select()
        self.checkbox_iridium_ampere.select()

        #######
        # TAB 3

        # Conductance method
        self.label_conductance_optmenu = customtkinter.CTkLabel(self.tabview.tab(tab3), text="Conductance estimates:", wraplength=150)
        self.label_conductance_optmenu.grid(row=1, column=0, columnspan=3, padx=10, pady=(30, 5), sticky="n")
        self.optmenu_conductance = customtkinter.CTkOptionMenu(self.tabview.tab(tab3), dynamic_resizing=True,
                                                        values=["Hardy model", "Zang & Paxton model"])
        self.optmenu_conductance.grid(row=2, column=0, columnspan=3, padx=10, pady=(5, 20))
        self.optmenu_conductance.set("Zang & Paxton model")

        # Make sure the parent grid columns expand nicely
        for i in range(3):
            self.tabview.tab(tab3).grid_columnconfigure(i, weight=1)

        # Kp index (useful for Hardy model)
        self.label_kp = customtkinter.CTkLabel(self.tabview.tab(tab3), text="Kp:")
        self.label_kp.grid(row=6, column=0, padx=(25, 5), pady=(20, 5), sticky="n")
        self.entry_kp = customtkinter.CTkEntry(self.tabview.tab(tab3), width=60)
        self.entry_kp.grid(row=7, column=0, padx=(25, 5), pady=(0, 20), sticky="n")
        self.entry_kp.insert(0, "4")

        # F10.7 solar flux (useful for EUV conductance)
        self.label_f107 = customtkinter.CTkLabel(self.tabview.tab(tab3), text="F10.7:")
        self.label_f107.grid(row=6, column=1, padx=(25, 5), pady=(20, 5), sticky="n")
        self.entry_f107 = customtkinter.CTkEntry(self.tabview.tab(tab3), width=60)
        self.entry_f107.grid(row=7, column=1, padx=(25, 5), pady=(0, 20), sticky="n")
        self.entry_f107.insert(0, "100")

        # Background/starlight (useful for EUV conductance)
        self.label_background = customtkinter.CTkLabel(self.tabview.tab(tab3), text="Background:") # add info/explnanation for all these parameters
        self.label_background.grid(row=6, column=2, padx=(25, 5), pady=(20, 5), sticky="n")
        self.entry_background = customtkinter.CTkEntry(self.tabview.tab(tab3), width=60)
        self.entry_background.grid(row=7, column=2, padx=(25, 5), pady=(0, 20), sticky="n")
        self.entry_background.insert(0, "2")

        #############
        # COLUMN1/ BOTTOM ROW 
        #############

        #######
        # Grid parameters

        self.frame_gridparam = customtkinter.CTkFrame(self, corner_radius=10, width=col1_width)
        self.frame_gridparam.grid(row=1, column=1, padx=(20, 0), pady=(20,0), sticky="nsew")
        self.frame_gridparam.grid_columnconfigure((0,1), weight=1)
        self.frame_gridparam.grid_propagate(False)

        self.label_grid_param = customtkinter.CTkLabel(self.frame_gridparam, text="Grid parameters", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label_grid_param.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        self.grid_input_mode = customtkinter.StringVar(value="manual")

        self.grid_mode_toggle = customtkinter.CTkSegmentedButton(self.frame_gridparam,
                                                                 values=["manual", "sliders"],
                                                                 variable=self.grid_input_mode,
                                                                 command=self.toggle_grid_input_mode)
        self.grid_mode_toggle.grid(row=1, column=0, columnspan=2, pady=10)

        self.label_L = customtkinter.CTkLabel(self.frame_gridparam, text="Length (km):", anchor='center') # cross-track dimension of analysis grid
        self.label_W = customtkinter.CTkLabel(self.frame_gridparam, text="Width (km):", anchor='center') # along-track dimension of analysis grid
        self.label_Lres = customtkinter.CTkLabel(self.frame_gridparam, text="Lres (km):", anchor='center')
        self.label_Wres = customtkinter.CTkLabel(self.frame_gridparam, text="Wres (km):", anchor='center')
        self.label_L.grid(row=2, column=0, padx=10, pady=10, sticky="n")
        self.label_W.grid(row=2, column=1, padx=10, pady=10, sticky="n")
        self.label_Lres.grid(row=4, column=0, padx=10, pady=10, sticky="n")
        self.label_Wres.grid(row=4, column=1, padx=10, pady=10, sticky="n")

        self.entry_L = customtkinter.CTkEntry(self.frame_gridparam, placeholder_text="L", width=70)
        self.entry_W = customtkinter.CTkEntry(self.frame_gridparam, placeholder_text="W", width=70)
        self.entry_Lres = customtkinter.CTkEntry(self.frame_gridparam, placeholder_text="Lres", width=70)
        self.entry_Wres = customtkinter.CTkEntry(self.frame_gridparam, placeholder_text="Wres", width=70)
        self.entry_L.grid(row=3, column=0, padx=10, pady=3)
        self.entry_W.grid(row=3, column=1, padx=10, pady=3)
        self.entry_Lres.grid(row=5, column=0, padx=10, pady=3)
        self.entry_Wres.grid(row=5, column=1, padx=10, pady=3)

        self.var_L = customtkinter.IntVar()
        self.var_W = customtkinter.IntVar()
        self.var_Lres = customtkinter.IntVar()
        self.var_Wres = customtkinter.IntVar()

        # TODO find good max number and good number of steps
        self.slider_L = customtkinter.CTkSlider(self.frame_gridparam, from_=10, to=4000, number_of_steps=200, variable=self.var_L, command=self.update_entry_L)
        self.slider_W = customtkinter.CTkSlider(self.frame_gridparam, from_=10, to=4000, number_of_steps=200, variable=self.var_W, command=self.update_entry_W)
        self.slider_Lres = customtkinter.CTkSlider(self.frame_gridparam, from_=10, to=1000, number_of_steps=10, variable=self.var_Lres, command=self.update_entry_Lres)
        self.slider_Wres = customtkinter.CTkSlider(self.frame_gridparam, from_=10, to=1000, number_of_steps=10, variable=self.var_Wres, command=self.update_entry_Wres)
        self.slider_L.grid(row=3, column=0, padx=(10,10), pady=3)
        self.slider_W.grid(row=3, column=1, padx=(10,10), pady=3)
        self.slider_Lres.grid(row=5, column=0, padx=(10,10), pady=3)
        self.slider_Wres.grid(row=5, column=1, padx=(10,10), pady=3)

        self.toggle_grid_input_mode("manual")

        self.var_L.set(1000)
        self.var_W.set(1000)
        self.var_Lres.set(200)
        self.var_Wres.set(200)

        self.update_entry_L(self.var_L.get())
        self.update_entry_W(self.var_W.get())
        self.update_entry_Lres(self.var_Lres.get())
        self.update_entry_Wres(self.var_Wres.get())

        #########
        # COLUMN2 (OUTPUTS)
        #########

        self.col2_width = 450
        self.output_height = 400

        ######
        # Create icons for GIFs

        # TODO should this have its own class?
        # see if i can avoid repetition between the 2 outputs (data and lompe)
        # see if maybe it's a good idea to link the play/pause and next/previous buttons (if the user pauses one gif, the other one pauses as well)
         
        # Play icon
        play_img = Image.new("RGBA", (25, 25), (0, 0, 0, 0)) # tranparent background
        draw = ImageDraw.Draw(play_img)
        draw.polygon([(6, 5), (20, 12), (6, 19)], fill="black")  # triangle
        self.play_icon = ImageTk.PhotoImage(play_img)

        # Pause icon
        pause_img = Image.new("RGBA", (25, 25), (0, 0, 0, 0)) # tranparent background
        draw = ImageDraw.Draw(pause_img)
        draw.rectangle([5, 5, 10, 20], fill="black")   # left bar
        draw.rectangle([15, 5, 20, 20], fill="black")  # right bar
        self.pause_icon = ImageTk.PhotoImage(pause_img)

        # Previous icon (triangle pointing left)
        prev_img = Image.new("RGBA", (15, 15), (0, 0, 0, 0))
        draw = ImageDraw.Draw(prev_img)
        draw.polygon([(12, 3), (3, 7), (12, 12)], fill="black")
        self.prev_icon = ImageTk.PhotoImage(prev_img)

        # Next icon (triangle pointing right)
        next_img = Image.new("RGBA", (15, 15), (0, 0, 0, 0))
        draw = ImageDraw.Draw(next_img)
        draw.polygon([(3, 3), (12, 7), (3, 12)], fill="black")
        self.next_icon = ImageTk.PhotoImage(next_img)

        ######
        # Satellite track + grid + data distribution
        self.frame_data = customtkinter.CTkFrame(self, width=self.col2_width, height=self.output_height)
        self.frame_data.grid(row=0, column=2, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.frame_data.grid_propagate(False)
        self.frame_data.grid_columnconfigure((0), weight=1)
        self.frame_data.grid_rowconfigure((0), weight=0)
        self.frame_data.grid_rowconfigure((1), weight=1)

        self.header_frame = customtkinter.CTkFrame(self.frame_data, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, pady=(2, 10), sticky="n")
        self.header_frame.grid_columnconfigure(0, weight=0)
        self.header_frame.grid_columnconfigure(1, weight=0)

        self.label_data_frame = customtkinter.CTkLabel(
            self.header_frame,
            text="Grid along satellite track + data distribution",
            font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label_data_frame.grid(row=0, column=0, sticky="w")

        self.info_icon = customtkinter.CTkLabel(self.header_frame, text="ⓘ", width=40, height=40, padx=4, pady=2)
        self.info_icon.grid(row=0, column=1, padx=(6, 0), sticky="w")
        CustomTooltip(self.info_icon, "SuperDARN (green) \n SuperMAG (orange) \n Iridium/AMPERE (blue) \n Swarm efield (black) \n Swarm bfield (purple)")

        self.label_data_gif = customtkinter.CTkLabel(self.frame_data, text="Waiting for trajectory animation...")
        self.label_data_gif.grid(row=1, column=0, pady=(0, 20), sticky='nsew')

        # Play/pause button
        self.btn_play_pause_data = customtkinter.CTkButton(self.frame_data,
                                                           image=self.pause_icon,
                                                           text="",
                                                           width=30,
                                                           height=30,
                                                           fg_color="#FFFFFF",
                                                           border_width=0,
                                                           corner_radius=0,
                                                           command=self.toggle_play_pause)

        self.btn_posy = 0.91
        self.btn_play_pause_data.place(x=0.5, y=self.btn_posy, anchor="center")
        self.btn_play_pause_data.place_forget()  # hide initially

        # Previous/next buttons
        self.btn_next_data = customtkinter.CTkButton(self.frame_data,
                                                     image=self.next_icon,
                                                     text="",
                                                     width=20,
                                                     height=20,
                                                     fg_color="#FFFFFF",
                                                     border_width=0,
                                                     corner_radius=0,
                                                     command=self.next_frame)

        self.btn_prev_data = customtkinter.CTkButton(self.frame_data,
                                                     image=self.prev_icon,
                                                     text="",
                                                     width=20,
                                                     height=20,
                                                     fg_color="#FFFFFF",
                                                     border_width=0,
                                                     corner_radius=0,
                                                    command=self.prev_frame)
        
        self.prev_posx, self.next_posx = 0.08, 0.92
        self.btn_prev_data.place(x=self.prev_posx, y=self.btn_posy, anchor="center") # left side
        self.btn_next_data.place(x=self.next_posx, y=self.btn_posy, anchor="center") # right side
        self.btn_prev_data.place_forget() # hide initially
        self.btn_next_data.place_forget() # hide initially
        
        ######
        # Lompe output
        self.lompe_frame = customtkinter.CTkFrame(self, width=self.col2_width, height=self.output_height)
        self.lompe_frame.grid(row=1, column=2, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.lompe_frame.grid_propagate(False)
        self.lompe_frame.grid_columnconfigure((0), weight=1)
        self.lompe_frame.grid_rowconfigure(0, weight=0) # title
        self.lompe_frame.grid_rowconfigure(1, weight=1) # GIF
        self.lompe_frame.grid_rowconfigure(2, weight=0) # controls
 
        self.label_lompe_frame = customtkinter.CTkLabel(self.lompe_frame,
                                                      text="Lompe output: reconstructed electrodynamics", 
                                                      font=customtkinter.CTkFont(size=14, weight="bold", underline=0))
        self.label_lompe_frame.grid(row=0, column=0, pady=(2, 10), sticky="n")


        self.label_lompe_gif = customtkinter.CTkLabel(self.lompe_frame, text="Waiting for Lompe plot...")
        self.label_lompe_gif.grid(row=1, column=0, pady=(0, 20), sticky='nsew')

        # Play/pause button
        self.btn_play_pause_lompe = customtkinter.CTkButton(self.lompe_frame,                                               image=self.pause_icon, 
                                                            text="",
                                                            width=30,                  # button width
                                                            height=30,                 # button height
                                                            fg_color="#FFFFFF",    # foreground (button face) - CTk supports 'transparent'
                                                            #   hover_color="#67d76e92",   # very light overlay when hovering (optional)
                                                            border_width=0,
                                                            corner_radius=0, 
                                                            command=self.toggle_play_pause)
        self.btn_posy = 0.91
        self.btn_play_pause_lompe.place(relx=0.5, rely=self.btn_posy, anchor="center")
        self.btn_play_pause_lompe.place_forget()  # hide initially

        # Previous/next buttons
        self.btn_next_lompe = customtkinter.CTkButton(self.lompe_frame,
                                                image=self.next_icon,
                                                text="",
                                                width=20,
                                                height=20,
                                                fg_color="#FFFFFF",
                                                border_width=0,
                                                corner_radius=0,
                                                command=self.next_frame)

        self.btn_prev_lompe = customtkinter.CTkButton(self.lompe_frame,
                                                image=self.prev_icon,
                                                text="",
                                                width=20,
                                                height=20,
                                                fg_color="#FFFFFF",
                                                border_width=0,
                                                corner_radius=0,
                                                command=self.prev_frame)
        
        self.prev_posx, self.next_posx = 0.08, 0.92
        self.btn_prev_lompe.place(relx=self.prev_posx, rely=self.btn_posy, anchor="center") # left side
        self.btn_next_lompe.place(relx=self.next_posx, rely=self.btn_posy, anchor="center") # right side
        self.btn_prev_lompe.place_forget() # hide initially
        self.btn_next_lompe.place_forget() # hide initially

        # Make sure main window limits column 3's stretch
        self.grid_columnconfigure(4, weight=0)

        #########
        # COLUMN3
        #########       

        ######
        # GIF parameters #TODO reorganise
     
        col3_width = 200

        self.col3_frame = customtkinter.CTkFrame(self, width=col3_width, corner_radius=10)
        self.col3_frame.grid(row=0, column=3, rowspan=3, padx=(20, 10), pady=(20, 20), sticky="nsew")
        self.col3_frame.grid_propagate(False)

        self.col3_frame.grid_columnconfigure(0, weight=1)
        self.col3_frame.grid_rowconfigure((0, 1, 2), weight=1)

        # GIF speed parameter
        self.gif_section = customtkinter.CTkFrame(self.col3_frame, corner_radius=8)
        self.gif_section.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nsew")
        self.gif_section.grid_columnconfigure(0, weight=1)

        self.gif_section_title = customtkinter.CTkLabel(self.gif_section, text="GIF", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.gif_section_title.grid(row=0, column=0, pady=(5, 5), sticky="ew")

        self.label_gifspeed = customtkinter.CTkLabel(self.gif_section, text="Animation speed (ms/frame):")
        self.label_gifspeed.grid(row=1, column=0, pady=(15, 0), sticky="ew")
        self.entry_gifspeed = customtkinter.CTkEntry(self.gif_section, width=80)
        self.entry_gifspeed.grid(row=2, column=0, pady=(7, 0))        
        self.default_speed = 550 # ms
        self.entry_gifspeed.insert(0, self.default_speed)  
        # CustomTooltip(self.label_gifspeed, text="Time in milliseconds between each frame.\nLower = faster animation.")      

        # Apply button
        self.button_apply = customtkinter.CTkButton(self.gif_section, text="Apply", command=self.apply_gif_parameters)
        self.button_apply.grid(row=3, column=0, pady=(50,20))

        # # Synchronize outputs checkbox
        # self.checkbox_sync = customtkinter.CTkCheckBox(self.gifparam_frame, text='Sync outputs')
        # self.checkbox_sync.grid(row=5, column=1, pady=(50, 0), sticky="n")
        # self.checkbox_sync.select()

        ######
        # Regularization parameters
        self.regul_section = customtkinter.CTkFrame(self.col3_frame, corner_radius=8)
        self.regul_section.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        self.regul_section.grid_columnconfigure(0, weight=0)  # labels (fixed)
        self.regul_section.grid_columnconfigure(1, weight=1)  # sliders (expand!)
        self.regul_section.grid_columnconfigure(2, weight=0)  # values (fixed)

        self.regul_section_title = customtkinter.CTkLabel(self.regul_section, text="Regularization \n parameters", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.regul_section_title.grid(row=0, column=0, columnspan=3, pady=(5, 5), sticky="ew")

        # L1 parameter
        self.label_l1 = customtkinter.CTkLabel(self.regul_section, text="l1:")
        self.label_l1.grid(row=1, column=0, padx=(5, 0), pady=(35,0), sticky="e")

        self.slider_l1 = customtkinter.CTkSlider(self.regul_section,
                                                 from_=-2, to=5,
                                                 number_of_steps=70,
                                                 orientation="horizontal",
                                                 command=self.update_l1_label  # callback when slider moves
                                                 )
        
        self.slider_l1.grid(row=1, column=1, columnspan=1, padx=5, pady=(35,0), sticky="ew")

        # L2 parameter
        self.label_l2 = customtkinter.CTkLabel(self.regul_section, text="l2:")
        self.label_l2.grid(row=2, column=0, padx=(5, 0), pady=(15,0), sticky="e")

        self.slider_l2 = customtkinter.CTkSlider(self.regul_section,
                                                 from_=-2, to=5,
                                                 number_of_steps=70,
                                                 orientation="horizontal",
                                                 command=self.update_l2_label  # callback when slider moves
                                                 )
        
        self.slider_l2.grid(row=2, column=1, columnspan=1, padx=5, pady=(15,0), sticky="ew")

        self.slider_l1.set(0)
        self.slider_l2.set(0)

        # Label to show value
        self.label_value_l1 = customtkinter.CTkLabel(self.regul_section, text=f"{self.slider_l1.get():.1f}")
        self.label_value_l1.grid(row=1, column=2, padx=(5,10), pady=(35,0), sticky="w")

        self.label_value_l2 = customtkinter.CTkLabel(self.regul_section, text=f"{self.slider_l2.get():.1f}")
        self.label_value_l2.grid(row=2, column=2, padx=(5,10), pady=(15,0), sticky="w")

        # Apply button (re-run SwarmDF)
        self.lompe_button2 = customtkinter.CTkButton(master=self.regul_section, text="Apply", command=self.apply_new_regularization)
        CustomTooltip(self.lompe_button2, "This will re-run Lompe \n with the new regularizaton parameters")
        self.lompe_button2.grid(row=3, column=1, pady=(50,20), sticky='ew')

        ######
        # Validation
        self.validation_section = customtkinter.CTkFrame(self.col3_frame, corner_radius=8)
        self.validation_section.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="nsew")
        self.validation_section.grid_columnconfigure(0, weight=1)

        self.validation_section_title = customtkinter.CTkLabel(self.validation_section, text="Output \n validation", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.validation_section_title.grid(row=4, column=0, pady=(5, 5))

        self.button_validate = customtkinter.CTkButton(self.validation_section, text="Validation", command=self.open_validation_window)
        self.button_validate.grid(row=5, column=0, pady=50)       
        CustomTooltip(self.button_validate, "This will run LompeOSSE \n (validation routine for experiment setup)")


# -------------------------------------------------------
# -------------------------------------------------------
# -------------------------------------------------------

    # Helper functions TODO maybe have them all in a dedicated script?)
    #################
    # Sidebar options

    def change_appearance_mode(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    #################
    # Swarm satellite(s)

    def swarm_selection(self):
        selected = []
        if self.checkbox_swarmA_var.get(): selected.append("A")
        if self.checkbox_swarmB_var.get(): selected.append("B")
        if self.checkbox_swarmC_var.get(): selected.append("C")
        return selected
        
    #################
    # Start/end input times

    def get_start_end_times(self):

        input_start = self.entry_start_time.get_datetime()
        input_end   = self.entry_end_time.get_datetime()

        if not input_start or not input_end:
            messagebox.showerror("Error", "⚠️ Please enter valid start and end times.")
            return None, None

        if input_start >= input_end:
            messagebox.showerror("Error", "⚠️ Start time must be earlier than end time.")
            return None, None

        min_seconds = 10 # TODO frame_length + 1s
        if (input_end - input_start).total_seconds() < min_seconds:
            messagebox.showerror("Error", f"⚠️ Time interval must be at least {min_seconds} seconds.")
            return None, None

        return input_start, input_end

    def load_example_date(self):
        # example_start = datetime(2014, 12, 15, 1, 12, 0)
        # example_end   = datetime(2014, 12, 15, 1, 27, 0)
        example_start = datetime(2014, 12, 15, 1, 15, 0)
        example_end   = datetime(2014, 12, 15, 1, 19, 0)      
        self.entry_start_time.set_datetime(example_start)
        self.entry_end_time.set_datetime(example_end)

    def reset_dates(self):
        self.entry_start_time.reset_to_placeholders()
        self.entry_end_time.reset_to_placeholders()

    #################
    # Grid parameters
    def toggle_grid_input_mode(self, mode):
        if mode == "manual":
            self.entry_L.grid()
            self.entry_W.grid()
            self.entry_Lres.grid()
            self.entry_Wres.grid()

            self.slider_L.grid_remove()
            self.slider_W.grid_remove()
            self.slider_Lres.grid_remove()
            self.slider_Wres.grid_remove()

        else:
            self.entry_L.grid_remove()
            self.entry_W.grid_remove()
            self.entry_Lres.grid_remove()
            self.entry_Wres.grid_remove()

            self.slider_L.grid()
            self.slider_W.grid()
            self.slider_Lres.grid()
            self.slider_Wres.grid()

    def update_entry_L(self, value):
        self.entry_L.delete(0, "end")
        self.entry_L.insert(0, str(int(float(value))))

    def update_entry_W(self, value):
        self.entry_W.delete(0, "end")
        self.entry_W.insert(0, str(int(float(value))))

    def update_entry_Lres(self, value):
        self.entry_Lres.delete(0, "end")
        self.entry_Lres.insert(0, str(int(float(value))))

    def update_entry_Wres(self, value):
        self.entry_Wres.delete(0, "end")
        self.entry_Wres.insert(0, str(int(float(value))))

    def get_grid_parameters(self):
        if self.grid_input_mode.get() == "manual":
            try:
                L = float(self.entry_L.get())
                W = float(self.entry_W.get())
                Lres = float(self.entry_Lres.get())
                Wres = float(self.entry_Wres.get())
            except ValueError: 
                L, W, Lres, Wres = None, None, None, None
                print("Invalid manual input")
        else:
            L = self.var_L.get()
            W = self.var_W.get()
            Lres = self.var_Lres.get()
            Wres = self.var_Wres.get()
        
        return L, W, Lres, Wres

    ################# 
    # GIFS (Swarm orbit and lompe plots) 

    def register_animation(self, frames, target_label):
        """ 
        Register a GIF animation as a passive object.
        It does not start animation; it only stores frames and target label.
        """
        state = {"frames": frames, "label": target_label}

        return state
    
    def play(self):
        """
        Advance global frame counter and update all animations.
        This is the single timing loop for the whole GUI (both GIFs).
        """
        if not self.master_state["playing"]:
            return

        self.master_state["current_frame"] = (self.master_state["current_frame"] + 1) % len(self.data_state["frames"])

        self.update_all_gifs()
        self.master_state["job"] = self.after(self.master_state["delay"], self.play)

    def update_all_gifs(self):
        """
        Draw current frame for all registered animations.
        """
        i = self.master_state["current_frame"]

        # Data GIF (always exists)
        frame = self.data_state["frames"][i]
        self.data_state["label"].configure(image=frame, text="")
        # self.data_state["label"].image = frame

        # Lompe GIF
        if hasattr(self, "lompe_state") and self.lompe_state is not None:
            frame = self.lompe_state["frames"][i]
            self.lompe_state["label"].configure(image=frame, text="")
            # self.lompe_state["label"].image = frame

        # LompeOSSE GIF
        if hasattr(self, "lompeosse_state") and self.lompeosse_state is not None:
            frame = self.lompeosse_state["frames"][i]
            self.lompeosse_state["label"].configure(image=frame, text="")

        # Gamera GIF (optional)
        if hasattr(self, "gamera_state") and self.gamera_state is not None:
            frame = self.gamera_state["frames"][i]
            self.gamera_state["label"].configure(image=frame, text="")

    # TODO remove? 
    def apply_gif_parameters(self):
        try:
            new_speed = int(self.entry_gifspeed.get())
            if new_speed <= 0: # handle invalid input
                raise ValueError
        except ValueError:
            new_speed = self.default_speed  # fallback to default if input is invalid
            self.entry_gifspeed.delete(0, "end")
            self.entry_gifspeed.insert(0, str(new_speed))

        print(f"Animation update: applied speed = {new_speed} ms")

        # Update the animation with new speed
        self.start_animation(self.lompe_frames_tk, new_speed, self.label_lompe_gif)
        self.start_animation(self.data_frames_tk, new_speed, self.label_data_gif)

    def toggle_play_pause(self):
        self.master_state["playing"] = not self.master_state["playing"]

        icon = self.pause_icon if self.master_state["playing"] else self.play_icon
        self.btn_play_pause_data.configure(image=icon)
        if hasattr(self, "btn_play_pause_lompe"):
            self.btn_play_pause_lompe.configure(image=icon)

        if self.master_state["playing"]:
            self.play()
        else:
            if self.master_state["job"]:
                self.after_cancel(self.master_state["job"])
                self.master_state["job"] = None

    def next_frame(self):
        self.master_state["playing"] = False
        if self.master_state["job"]:
            self.after_cancel(self.master_state["job"])
            self.master_state["job"] = None

        self.master_state["current_frame"] = (
            self.master_state["current_frame"] + 1
        ) % len(self.data_state["frames"])

        self.update_all_gifs()

    def prev_frame(self):
        self.master_state["playing"] = False
        if self.master_state["job"]:
            self.after_cancel(self.master_state["job"])
            self.master_state["job"] = None

        self.master_state["current_frame"] = (
            self.master_state["current_frame"] - 1
        ) % len(self.data_state["frames"])

        self.update_all_gifs()

    #################
    # Swarm trajectory output

    # TODO fix relative position (currently, pos changes with gui size)
    def show_data_controls(self):
        self.btn_play_pause_data.place(relx=0.5, rely=self.btn_posy, anchor="center")
        self.btn_prev_data.place(relx=self.prev_posx, rely=self.btn_posy, anchor="center")
        self.btn_next_data.place(relx=self.next_posx, rely=self.btn_posy, anchor="center")

    def swarm_trajectory_UI(self):

        # Extract PIL images and individual grids
        self.grids, frames_pil = swarm_trajectory(self.sat_id, self.start_time, self.end_time, self.timestep, self.grid_params, self.datasets, self.speed, self.show_data)
                
        # Convert PIL → Tkinter images
        w = max(self.label_data_gif.winfo_width() - 40, 1)  # 10px margin each side
        h = max(self.label_data_gif.winfo_height(), 1)
        self.data_frames_tk = [customtkinter.CTkImage(light_image=f.resize((w, h), Image.LANCZOS),
                           size=(w, h)) for f in frames_pil]

        # Register/prepare frames for animated GIF
        self.data_state = self.register_animation(self.data_frames_tk, self.label_data_gif)
        print("Trajectory animation frames generated and registered.")

        # UI updates
        self.show_data_controls()

    #################
    # Lompe output

    def show_lompe_controls(self):
        self.btn_play_pause_lompe.place(relx=0.5, rely=self.btn_posy, anchor="center")
        self.btn_prev_lompe.place(relx=self.prev_posx, rely=self.btn_posy, anchor="center")
        self.btn_next_lompe.place(relx=self.next_posx, rely=self.btn_posy, anchor="center")

    def run_lompe_UI(self):
        
        print(f"Running Lompe again  with l1={self.l1:.2f}, l2={self.l2:.2f}") 

        # Run Lompe, get PIL images
        lompe_models = run_lompe(self.start_time, self.end_time, self.timestep, self.grids, 
                                 self.datasets, self.SHs, self.SPs, self.l1, self.l2)
        lompe_frames_pil = lompe_output(lompe_models, self.speed)

        # Convert PIL → Tkinter images
        w = max(self.label_lompe_gif.winfo_width() - 40, 1)  # 10px margin each side
        h = max(self.label_lompe_gif.winfo_height(), 1)
        self.lompe_frames_tk = [customtkinter.CTkImage(light_image=f.resize((w, h), Image.LANCZOS),
                           size=(w, h)) for f in lompe_frames_pil]
        
        # Start animation
        self.lompe_state = self.register_animation(self.lompe_frames_tk, self.label_lompe_gif)
        print("Lompe output animation frames generated and registered.")

        # UI updates
        self.show_lompe_controls()
        
        if self.lompe_button:
            self.lompe_button.grid_forget()
        
        return lompe_models

    #################
    # Regularization parameters for Lompe inversion 

    def update_l1_label(self, slider_val):
        log_val = 10 ** slider_val # log scale
        self.label_value_l1.configure(text=f"{log_val:.2f}")
        # TODO is l1 = exponent or 1**exponent ??

    def update_l2_label(self, slider_val):
        log_val = 10 ** slider_val # log scale
        self.label_value_l2.configure(text=f"{log_val:.2f}")

    def apply_new_regularization(self):

        # Get updated slider values
        slider_l1_value = self.slider_l1.get()
        self.l1 = 10 ** slider_l1_value
        slider_l2_value = self.slider_l2.get()
        self.l2 = 10 ** slider_l2_value

        print(f"Running Lompe with l1={self.l1:.2f}, l2={self.l2:.2f}") 

        # Run lompe with new parameters
        self.run_lompe_UI()

    #################
    # Validation (LompeOSSE)

    def open_validation_window(self):
        self.validation_window = customtkinter.CTkToplevel(self)
        self.validation_window.title("LompeOSSE validation output")
        self.validation_window.geometry(f"{1000}x{500}")   # large window

        self.validation_state = {"frames_lompe": None,
                                 "frames_gamera": None,
                                 "current_frame": 0,
                                 "playing": True,
                                 "job": None,
                                 "delay": self.speed}
        
        # Container for both plots
        self.plots_container = customtkinter.CTkFrame(self.validation_window, 
                                                      width=self.col2_width + self.col2_width/2, 
                                                      height=self.output_height)
        self.plots_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.plots_container.grid_columnconfigure(0, weight=3)  # big
        self.plots_container.grid_columnconfigure(1, weight=2)  # small
        self.plots_container.grid_rowconfigure(0, weight=1)

        # LompeOSSE 
        self.lompe_plot_frame = customtkinter.CTkFrame(self.plots_container)
        self.lompe_plot_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.lompe_label = customtkinter.CTkLabel(self.lompe_plot_frame, text="")
        self.lompe_label.pack(fill="both", expand=True)

        # Gamera quantities
        self.gamera_plot_frame = customtkinter.CTkFrame(self.plots_container)
        self.gamera_plot_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.gamera_label = customtkinter.CTkLabel(self.gamera_plot_frame, text="")
        self.gamera_label.pack(fill="both", expand=True)

        #############
        # Validation window layout
        #############

        self.validation_controls = customtkinter.CTkFrame(self.validation_window, fg_color="transparent")
        self.validation_controls.pack(side="bottom", pady=5)

        self.btn_prev_validation = customtkinter.CTkButton(self.validation_controls,
                                                           image=self.prev_icon,
                                                           text="",
                                                           width=30,
                                                           height=30,
                                                           fg_color="transparent",
                                                           command=self.prev_validation_frame)

        self.btn_play_pause_validation = customtkinter.CTkButton(self.validation_controls,
                                                                 image=self.pause_icon,
                                                                 text="",
                                                                 width=30,
                                                                 height=30,
                                                                 fg_color="transparent",
                                                                 command=self.toggle_play_pause_validation)

        self.btn_next_validation = customtkinter.CTkButton(self.validation_controls,
                                                           image=self.next_icon,
                                                           text="",
                                                           width=30,
                                                           height=30,
                                                           fg_color="transparent",
                                                           command=self.next_validation_frame)

        self.btn_prev_validation.pack(side="left", padx=10)
        self.btn_play_pause_validation.pack(side="left", padx=10)
        self.btn_next_validation.pack(side="left", padx=10)

        # Status label
        self.status_label = customtkinter.CTkLabel(self.validation_window,
                                                   text="Running LompeOSSE…",
                                                   font=customtkinter.CTkFont(size=14, weight="bold"))
        self.status_label.pack(pady=2)

        #############

        # Now run the OSSE and display output in this window
        self.run_lompeOSSE_UI()

    def run_lompeOSSE_UI(self):
      
        #TODO fix hemisphere in run_lompeOSSE

        lompeOSSE_models, gamera_models = run_lompeOSSE(self.lompe_models)
        lompeOSSE_frames_pil, gamera_frames_pil = lompeOSSE_output(lompeOSSE_models, gamera_models, self.speed)

        # Convert PIL → Tkinter images
        self.validation_window.update_idletasks()

        w1 = self.lompe_plot_frame.winfo_width()
        h1 = self.lompe_plot_frame.winfo_height()
        self.lompeOSSE_frames_tk = [customtkinter.CTkImage(light_image=f.resize((w1, h1), Image.LANCZOS),
                           size=(w1, h1)) for f in lompeOSSE_frames_pil]
        
                
        w2 = self.gamera_plot_frame.winfo_width()
        h2 = self.gamera_plot_frame.winfo_height()
        self.gamera_frames_tk = [customtkinter.CTkImage(light_image=f.resize((w2, h2), Image.LANCZOS),
                    size=(w2, h2)) for f in gamera_frames_pil]

        # self.lompeOSSE_label.configure(image=self.lompeOSSE_frames_tk[0])
        self.status_label.configure(text="")

        self.validation_state["frames_lompe"] = self.lompeOSSE_frames_tk
        self.validation_state["frames_gamera"] = self.gamera_frames_tk
        self.validation_state["current_frame"] = 0
        self.update_validation_gifs()
        self.play_validation()


        # # Start animation
        # self.lompeosse_state = self.register_animation(self.lompeOSSE_frames_tk, self.lompe_label)
        # self.gamera_state = self.register_animation(self.gamera_frames_tk, self.gamera_label)
        # print("LompeOSSE output animation frames generated and registered.")

        # self.show_lompeosse_controls()

    def update_validation_gifs(self):
        i = self.validation_state["current_frame"]

        self.lompe_label.configure(image=self.validation_state["frames_lompe"][i])
        self.gamera_label.configure(image=self.validation_state["frames_gamera"][i])
    
    def play_validation(self):
        state = self.validation_state

        if not state["playing"]:
            return

        state["current_frame"] = (state["current_frame"] + 1) % len(state["frames_lompe"])

        self.update_validation_gifs()

        state["job"] = self.validation_window.after(state["delay"], self.play_validation)
    
    def toggle_play_pause_validation(self):
        state = self.validation_state
        state["playing"] = not state["playing"]

        icon = self.pause_icon if state["playing"] else self.play_icon
        self.btn_play_pause_validation.configure(image=icon)

        if state["playing"]:
            self.play_validation()
        else:
            if state["job"]:
                self.validation_window.after_cancel(state["job"])
                state["job"] = None

    def next_validation_frame(self):
        state = self.validation_state
        state["playing"] = False

        if state["job"]:
            self.validation_window.after_cancel(state["job"])
            state["job"] = None

        state["current_frame"] = (
            state["current_frame"] + 1
        ) % len(state["frames_lompe"])

        self.update_validation_gifs()

    def prev_validation_frame(self):
        state = self.validation_state
        state["playing"] = False

        if state["job"]:
            self.validation_window.after_cancel(state["job"])
            state["job"] = None

        state["current_frame"] = (
            state["current_frame"] - 1
        ) % len(state["frames_lompe"])

        self.update_validation_gifs()

        # + plot gamera quantities in the format of a Lompe figure
# -------------------------------------------------------
# -------------------------------------------------------
# -------------------------------------------------------

    #################
    # Run toolbox! TODO make keep this only in this script + the user selections and organize the rest differently (all the stuff to make a nice layout etc should be somewhere else because not relevant to user)
    def run_swarm_df(self):

        # set up progressbar (satellite track animation)
        self.progressbar1 = customtkinter.CTkProgressBar(self.frame_data, mode="indeterminate")
        self.progressbar1.grid(row=1, column=0, pady=(30, 10))
        self.progressbar1.start()

        if self.checkbox_runlompe.get():
            self.progressbar2 = customtkinter.CTkProgressBar(self.lompe_frame, mode="indeterminate")
            self.progressbar2.grid(row=1, column=0, pady=(30, 10))
            self.progressbar2.start()

        # schedule the heavy part of SwarmDF AFTER letting the GUI update
        self.after(100, self._do_swarm_df)
    
    def _do_swarm_df(self):
        """Heavy work here!"""

        ###############
        # Get all input (GUI) info
        ###############

        # satellite ID
        self.sat_id = self.optmenu_satellite.get()
        if self.sat_id == "Satellite ID": #TODO change that to error if empty
            messagebox.showerror("Error", "⚠️ Please select a valid Satellite ID (Swarm A, B, or C) and press Run SwarmDF again.")
            return
    
        # time interval
        self.start_time, self.end_time = self.get_start_end_times()
        self.timestep = int(self.entry_timestep.get()) # frame_length = 60 # frame interval in sec (how much of the orbit is captured in one frame) # HOW TO PICK THAT NUMBER??

        # datasets
        self.datasets2download = []
        if self.checkbox_swarm_efield.get():
            self.datasets2download.append('swarm_efield')
        if self.checkbox_swarm_bfield.get():
            self.datasets2download.append('swarm_mag')
        if self.checkbox_superdarn.get():
            self.datasets2download.append('superdarn')
        if self.checkbox_supermag.get():
            self.datasets2download.append('supermag')
        if self.checkbox_iridium_ampere.get():
            self.datasets2download.append('iridium_ampere')
        # if self.checkbox_dmspssies.isChecked():
        #     selected_sources.append('ssies')
        # TODO add dmsp ssies

        if len(self.datasets2download) == 0: 
            if self.checkbox_runlompe.get():
                self.checkbox_runlompe.deselect()
                messagebox.showwarning("Lompe unavailable", "No valid datasets available for Lompe inversion.")

        # conductance
        kp_value = float(self.entry_kp.get()) 
        f107_value = float(self.entry_f107.get())
        background_value = float(self.entry_background.get())

        self.conductance_params = {"kp": kp_value, "f107": f107_value, "background": background_value}
        self.conductance_method = self.optmenu_conductance.get()

        # grid 
        self.grid_params = self.get_grid_parameters() # Store L,W,Lres,Wres in grid variable TODO add dictionnary
                
        # GIF
        self.speed = int(self.entry_gifspeed.get()) # ms/frame #TODO remove
        self.show_data = self.checkbox_showdata.get() # Returns True if checked, False if unchecked

        # regularization #TODO Ok kalle?
        slider_l1_value = self.slider_l1.get()
        self.l1 = 10 ** slider_l1_value
        slider_l2_value = self.slider_l2.get()
        self.l2 = 10 ** slider_l2_value
        self.regul_params = {'l1': self.l1, 'l2': self.l2}

        # hemisphere
        # TODO find where hemisphere info is decided! Make it an option for the user?
        # hem = grid.lat
        # print('hemisphere', hem)

        # Collect parameters from GUI for generating Python code
        self.config = build_config_dict(self.sat_id, self.start_time, self.end_time, self.timestep,
            self.datasets2download, self.conductance_method, self.conductance_params, self.grid_params, self.regul_params, self.speed, lompeosse=self.checkbox_lompeosse.get())

        ######################
        # Collect data
        ######################

        package_root = Path(__file__).resolve().parents[1]
        data_path = str(package_root / "data" / "sample_datasets") + "/"

        # Fetch and load data
        datahandler = DataManager(self.start_time, data_path, self.datasets2download)
        self.datasets = datahandler.datasets

        ######################
        # Swarm orbit animation
        ######################

        self.swarm_trajectory_UI()

        self.progressbar1.stop()
        self.progressbar1.grid_forget() # hide progressbar

        ######################
        # Define conductances (TODO come back to that --- do it in a different script)
        ######################

        self.SHs, self.SPs = compute_conductances(self.conductance_method, self.start_time, self.end_time, self.timestep, self.grids, self.conductance_params)
                
        ######################
        # Lompe analysis 
        ######################

        self.lompe_button = None

        # If "Run Lompe analysis" was NOT selected, show button that triggers Lompe analysis
        if not self.checkbox_runlompe.get():

            self.lompe_button = customtkinter.CTkButton(master=self.lompe_frame,
                                                        text="Run Lompe analysis",
                                                        command=self.run_lompe_UI,
                                                        width=170,
                                                        height=40)

            self.lompe_button.grid(row=1, column=0, pady=(0, 20))
       
        else: # Run Lompe analysis automatically

            self.lompe_models = self.run_lompe_UI()

            self.progressbar2.stop()
            self.progressbar2.grid_forget() # hide progressbar
        
        ######################
        # GUI-specific: Master animation clock. 
        # Controls the timeline for all GIFs.

        self.master_state = {"current_frame": 0,
                                 "playing": True,
                                 "job": None,
                                 "delay": self.speed}
        self.play()


        ######################
        # Lompe_OSSE validation 
        ######################

        # TODO it opens the validatio window once everything else is done, I would like things to show one after another 
        if self.checkbox_lompeosse.get():
            self.open_validation_window()

        #TODO ALSO ADD POSSIBILITY TO TRIGGER lompeosse when clicking the validation button afterwards
        #TODO check why I don't have access to control buttons once the validation windows shows up. fix that 
        # add lompeosse stuff here
        # Idea: when clicking "validation" button, the lompeOSSE module is triggered. 
        # That means that LompeOSSE runs in the background, reads which data was given to the initial SwarmDF run, and fetches the corresponding gamera data. 
        # With this simulation data, LompeOSSE then renders a new Lompe analysis.
        # We want a pop up window with this new lompe outputs + a plot with the same layout as the lompe figure with the corresponding gamera quantities. 

        ######################
        # Generate Python code
        ######################

        if self.var_generate_code.get():
            generate_python_code(self.config)



# Small info box pops up when hovering widget 
class CustomTooltip:
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay  # delay in ms before showing
        self.tooltip_label = None
        self.after_id = None

        widget.bind("<Enter>", self.schedule_show)
        widget.bind("<Leave>", self.hide_tooltip)
        widget.bind("<Motion>", self.move_tooltip)

    def schedule_show(self, event=None):
        self.after_id = self.widget.after(self.delay, self.show_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_label is not None:
            return  # already showing

        root = self.widget.winfo_toplevel()  # top-level window

        self.tooltip_label = customtkinter.CTkLabel(
            root,  # parent is the top-level window
            text=self.text,
            fg_color="grey90", # background
            text_color="black",
            corner_radius=5,
            font=customtkinter.CTkFont(size=11),
        )

        self.place_tooltip()

    def place_tooltip(self):
        if self.tooltip_label is None:
            return

        # Get widget position relative to root window
        root = self.widget.winfo_toplevel()
        x = self.widget.winfo_rootx() - root.winfo_rootx() + 20
        y = self.widget.winfo_rooty() - root.winfo_rooty() + self.widget.winfo_height() + 5

        # Keep inside root bounds
        root_width = root.winfo_width()
        root_height = root.winfo_height()

        self.tooltip_label.update_idletasks()
        tip_width = self.tooltip_label.winfo_width()
        tip_height = self.tooltip_label.winfo_height()

        if x + tip_width > root_width:
            x = root_width - tip_width - 5
        if y + tip_height > root_height:
            y = root_height - tip_height - 5

        self.tooltip_label.place(x=x, y=y)

    def move_tooltip(self, event=None):
        if self.tooltip_label is not None:
            self.place_tooltip()

    def hide_tooltip(self, event=None):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        if self.tooltip_label:
            self.tooltip_label.destroy()
            self.tooltip_label = None


# TODO make this its own script? or put everything similar into a utils script
class DateTimeEntry(customtkinter.CTkFrame):
    def __init__(self, master, label="Select time", default=None):
        super().__init__(master)

        # Label
        customtkinter.CTkLabel(self, text=label).grid(row=0, column=0, columnspan=13, pady=(0, 5), sticky="w")

        # Placeholder setup
        self.placeholders = ["YYYY", "MM", "DD", "HH", "MM", "SS"]
        self.widths = [47, 35, 32, 32, 35, 32]
        self.entries = []

        # Entry fields
        for i, ph in enumerate(self.placeholders):
            entry = customtkinter.CTkEntry(self, width=self.widths[i], justify="center")
            entry.insert(0, ph)
            entry.bind("<FocusIn>", lambda e, ph=ph: self.on_focus_in(e, ph))
            entry.bind("<FocusOut>", lambda e, ph=ph, i=i: self.on_focus_out(e, ph, i))
            entry.bind("<KeyRelease>", lambda e, i=i: self.auto_advance(e, i))
            entry.grid(row=1, column=i * 2, padx=(1, 1))
            self.entries.append(entry)

            # Add separators visually
            if i == 0 or i == 1:
                sep = customtkinter.CTkLabel(self, text="-")
            elif i == 2:
                sep = customtkinter.CTkLabel(self, text=" ")
            elif i in (3, 4):
                sep = customtkinter.CTkLabel(self, text=":")
            else:
                sep = None
            if sep:
                sep.grid(row=1, column=i * 2 + 1, padx=(0,0))

        # Calendar button
        self.cal_button = customtkinter.CTkButton(self, text="📅", width=20, command=self.open_calendar)
        self.cal_button.grid(row=1, column=12, padx=(7, 0))
        CustomTooltip(self.cal_button, "Pick the date from the calendar. Type YYYY to jump directly to that year.")

        # Force a stable grid layout inside DateTimeEntry
        for i in range(13):  # 6 entries + 6 separators
            self.grid_columnconfigure(i, weight=0)


    def on_focus_in(self, event, placeholder):
        """Remove placeholder when user starts typing"""
        if event.widget.get() == placeholder:
            event.widget.delete(0, "end")
            # event.widget.configure(text_color="white")

    def on_focus_out(self, event, placeholder, index):
        """Put the placeholder back if user leaves the field empty"""
        text = event.widget.get().strip()
        if text == "":
            event.widget.insert(0, placeholder)
            # event.widget.configure(text_color="gray70")
        else:
            # --- Automatic zero-padding ---
            if index > 0:  # skip year
                lengths = [4, 2, 2, 2, 2, 2]
                if text.isdigit() and len(text) < lengths[index]:
                    text = text.zfill(lengths[index])
                    event.widget.delete(0, "end")
                    event.widget.insert(0, text)
            # event.widget.configure(text_color="white")

    def auto_advance(self, event, index):
        lengths = [4, 2, 2, 2, 2, 2]
        if event.widget.get().isdigit() and len(event.widget.get()) >= lengths[index] and index < len(self.entries) - 1:
            self.entries[index + 1].focus()

    def open_calendar(self):

        # Try to read date fields
        y, m, d = None, None, None
        try:
            y = int(self.entries[0].get()) if self.entries[0].get().isdigit() else None
            m = int(self.entries[1].get()) if self.entries[1].get().isdigit() else 1
            d = int(self.entries[2].get()) if self.entries[2].get().isdigit() else 1
        except ValueError:
            pass

        # fallback if not enough info
        if not y:
            today = date.today()
            y, m, d = today.year, today.month, today.day

        # Create popup window
        top = customtkinter.CTkToplevel(self)
        top.title("Select date")

        # Initialize calendar at the provided date
        cal = Calendar(
            top,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            year=y,
            month=m,
            day=d
        )
        cal.pack(padx=10, pady=10)

        def set_date():
            date_str = cal.get_date()  # format: yyyy-mm-dd
            y, m, d = date_str.split("-")
            self.entries[0].delete(0, "end"); self.entries[0].insert(0, y)
            self.entries[1].delete(0, "end"); self.entries[1].insert(0, m)
            self.entries[2].delete(0, "end"); self.entries[2].insert(0, d)
            for i in range(3):
                self.entries[i].configure(text_color="white")
            top.destroy()

        customtkinter.CTkButton(top, text="OK", command=set_date).pack(pady=(0, 10))

    def get_datetime(self):
        try:
            vals = [e.get() for e in self.entries]
            date_str = f"{vals[0]}-{vals[1]}-{vals[2]} {vals[3]}:{vals[4]}:{vals[5]}"
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print("⚠️ Invalid date/time:", e)
            return None

    def link_datetime_entries(self, start, end):
        def mirror(event):
            for i in range(6):
                val = start.entries[i].get()
                ph = start.placeholders[i]

                if val != ph:
                    end.entries[i].delete(0, "end")
                    end.entries[i].insert(0, val)
                    end.entries[i].configure(text_color="white")

        for entry in start.entries:
            entry.bind("<KeyRelease>", mirror)



            # TODO add 00 00 automatically if not written down by user in start and end times
            # TODO add error message if start and end times are the same
            # TODO fix color issue
            # TODO is it possible to change calendar color (very dark right now) 

    def set_datetime(self, dt):
        """Fill all fields with a given datetime object."""
        vals = [
            str(dt.year),
            f"{dt.month:02d}",
            f"{dt.day:02d}",
            f"{dt.hour:02d}",
            f"{dt.minute:02d}",
            f"{dt.second:02d}",
        ]
        for i, v in enumerate(vals):
            self.entries[i].delete(0, "end")
            self.entries[i].insert(0, v)

    def reset_to_placeholders(self):
        """Reset all fields to their default placeholders."""
        for entry, ph in zip(self.entries, self.placeholders):
            entry.delete(0, "end")
            entry.insert(0, ph)
            # entry.configure(text_color="gray70")  # optional if you re-enable color handling


if __name__ == "__main__":
    app = App()
    app.mainloop()


