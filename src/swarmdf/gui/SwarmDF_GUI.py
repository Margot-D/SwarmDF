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
from PIL import Image, ImageTk, ImageDraw, ImageFont

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np

from datetime import datetime, date
import os

import webbrowser

from swarmdf import *

from ui_helpers.icons import Icons
from ui_helpers.tooltip import CustomTooltip

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import time as tt

# TODO remember to fix citation (github)

# Main toolbox class
class SwarmDFGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("SwarmDF.py")
        width, height = 1660, 950
        self.aspect_ratio = 16/9 #width/height
        self.geometry(f"{width}x{height}") #{1660}x{870}
        self.minsize(1450, 780)
        # self.bind("<Configure>", self.enforce_aspect)

        # configure grid layout
        self.grid_columnconfigure(1, weight=0, minsize=365)
        self.grid_columnconfigure(2, weight=4)
        self.grid_columnconfigure(3, weight=0, minsize=300)
        self.grid_rowconfigure((0, 1), weight=1)
        # self.grid_rowconfigure((0), weight=1, minsize=450)
        # self.grid_rowconfigure((1), weight=1, minsize=450)

        #############
        # SIDEBAR
        #############

        self.frame_sidebar = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.frame_sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")

        self.title_sidebar = customtkinter.CTkLabel(self.frame_sidebar, text="SwarmDF \n User interface", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.title_sidebar.grid(row=0, column=0, padx=20, pady=(20, 50))

        # "Run Lompe analysis" checkbox
        self.checkbox_runlompe = customtkinter.CTkCheckBox(master=self.frame_sidebar, text=f"Run Lompe analysis")
        self.checkbox_runlompe.grid(row=3, column=0, padx=20, pady=(20,20))
        self.checkbox_runlompe.select()
        # CustomTooltip(self.checkbox_runlompe, text="When not selected, SwarmDF collects the requested data and show the data coverage around Swarm.")      

        # "Run LompeOSSE validation" checkbox
        self.checkbox_lompeosse = customtkinter.CTkCheckBox(self.frame_sidebar, text='Run LompeOSSE validation')
        self.checkbox_lompeosse.grid(row=4, column=0, padx=20, pady=(20,20))
        # self.checkbox_lompeosse.select()

        # "Generate Python code" switch
        self.switch_pythoncode = customtkinter.CTkSwitch(master=self.frame_sidebar, text=f"Generate Python code") 
        self.switch_pythoncode.grid(row=5, column=0, padx=20, pady=(20,5))

        # User filename for generated Python code
        self.entry_codename = customtkinter.CTkEntry(master=self.frame_sidebar, placeholder_text="MyFile.py")
        self.entry_codename.grid(row=6, column=0, padx=20, pady=5)
        CustomTooltip(self.entry_codename, "Filename for generated script (default: SwarmDF_script.py")

        # "Run SwarmDF" button
        self.button_runSwarmDF = customtkinter.CTkButton(self.frame_sidebar, 
                                                         command=self.run_swarm_df, 
                                                         text='Run SwarmDF',
                                                         width=160, height=80, font=("Arial", 18))
        self.button_runSwarmDF.grid(row=7, column=0, padx=20, pady=(100,10))

        # Demo mode switch
        self.switch_demo = customtkinter.CTkSwitch(master=self.frame_sidebar, text=f"Demo mode", command=self.load_example_date) 
        self.switch_demo.grid(row=8, column=0, padx=20, pady=(10,100))
        CustomTooltip(self.switch_demo, "Use sample datasets for example event and skip data collection")

        # Apparence mode
        self.frame_sidebar.grid_rowconfigure(9, weight=1)
        self.label_appearance_mode = customtkinter.CTkLabel(self.frame_sidebar, text="Appearance Mode:", anchor="w")
        self.label_appearance_mode.grid(row=10, column=0, padx=20, pady=(10, 0))
        self.optmenu_appearance_mode = customtkinter.CTkOptionMenu(self.frame_sidebar, 
                                                                   values=["Light", "Dark", "System"],
                                                                   command=self.change_appearance_mode)
        self.optmenu_appearance_mode.grid(row=11, column=0, padx=20, pady=(10, 10))
        self.optmenu_appearance_mode.set("Dark")

        # Scaling option
        self.label_scaling = customtkinter.CTkLabel(self.frame_sidebar, text="UI Scaling:", anchor="w")
        self.label_scaling.grid(row=12, column=0, padx=20, pady=(10, 0))
        self.optmenu_scaling = customtkinter.CTkOptionMenu(self.frame_sidebar, 
                                                           values=["80%", "90%", "100%", "110%", "120%"],
                                                           command=self.change_scaling)
        self.optmenu_scaling.grid(row=13, column=0, padx=20, pady=(10, 20))
        self.optmenu_scaling.set("100%")

        #############
        # COLUMN 1/TOP ROW (INPUT)
        #############
        
        col1_width = 150 #65

        self.tabview = customtkinter.CTkTabview(self, corner_radius=10) #, width=col1_width
        self.tabview.grid(row=0, column=1, padx=(20, 0), pady=(3, 0), sticky="nsew")
        tab1 = "Main input"
        tab2 = "Datasets"
        tab3 = "Conductances"
        self.tabview.add(tab1)
        self.tabview.add(tab2)
        self.tabview.add(tab3)
        self.tabview.tab(tab1).grid_columnconfigure(0, weight=1)
        self.tabview.tab(tab2).grid_columnconfigure((0,1), weight=2)
        self.tabview.tab(tab3).grid_columnconfigure(0, weight=2)
        self.tabview.configure(height=500)
        # self.tabview.grid_propagate(False)

        #######
        # TAB 1 - Main input
        
        # Satellite ID
        self.optmenu_satellite = customtkinter.CTkOptionMenu(self.tabview.tab(tab1), dynamic_resizing=False,
                                                             values=["Swarm A", "Swarm B", "Swarm C"])
        self.optmenu_satellite.grid(row=0, column=0, padx=(10,10), pady=(30, 10))
        self.optmenu_satellite.set("Satellite ID")

        # Start time entry
        self.entry_start_time = DateTimeEntry(self.tabview.tab(tab1), label="Start time:      ⓘ")
        self.entry_start_time.grid(row=1, column=0, padx=20, pady=20, sticky="w")

        # End time
        self.entry_end_time = DateTimeEntry(self.tabview.tab(tab1), label="End time:        ⓘ")
        self.entry_end_time.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.entry_end_time.link_datetime_entries(self.entry_start_time, self.entry_end_time)

        # Time step
        self.label_timestep = customtkinter.CTkLabel(self.tabview.tab(tab1), text="Time steps:")
        self.label_timestep.grid(row=3, column=0, padx=20, pady=40, sticky="w")
        self.entry_timestep = customtkinter.CTkEntry(self.tabview.tab(tab1), width=50)
        self.entry_timestep.grid(row=3, column=0, pady=20)        
        self.entry_timestep.insert(0, 30) # default: 30 s
        CustomTooltip(self.entry_timestep, "Time between frames. \n Use the dropdown to select seconds, minutes, or hours. \n Min value: 10 sec")

        self.timestep_unit_var = customtkinter.StringVar(value="s")
        self.timestep_unit_menu = customtkinter.CTkOptionMenu(self.tabview.tab(tab1), values=["s", "min", "h"], variable=self.timestep_unit_var, width=60, button_color="#A0A0A0", fg_color="#A0A0A0")
        self.timestep_unit_menu.grid(row=3, column=0, padx=(180,30), pady=20)

        # "Set example date" button         
        customtkinter.CTkButton(self.tabview.tab(tab1),
                                text="Use example event",
                                command=self.load_example_date,
                                width=40,
                                height=8,
                                fg_color="#888888",      # medium grey background
                                hover_color="#AAAAAA",   # slightly lighter on hover
                                font=customtkinter.CTkFont(size=13)).grid(row=5, column=0, pady=(25, 10))

        # "Reset date to placeholders" button
        customtkinter.CTkButton(self.tabview.tab(tab1),
                                text="Reset to placeholders",
                                command=self.reset_dates, 
                                width=40,
                                height=8,
                                fg_color="#888888",      # medium grey background
                                hover_color="#AAAAAA",   # slightly lighter on hover
                                font=customtkinter.CTkFont(size=13)).grid(row=6, column=0, pady=(0, 15))

        # Link to Swarm aurora website
        self.link_find_conjunction = customtkinter.CTkLabel(self.tabview.tab(tab1), text="Find conjunction with Swarm-Aurora", text_color="green", cursor="hand2")
        self.link_find_conjunction.grid(row=7, column=0, padx=35, pady=(5, 0), sticky='n') #pady=(25, 5)
        self.link_find_conjunction.bind("<Button-1>", lambda e: webbrowser.open("https://swarm-aurora.com/"))

        #######
        # TAB 2 - Datasets 

        # TODO get the correct electric field data (ask Spencer), this is along-track track, meaning i need a los component (which should simply be the direction of the satellite). kalle said this should be available on viresclient. 

        self.checkbox_swarm_bfield = customtkinter.CTkCheckBox(master=self.tabview.tab(tab2), text='Swarm mag')
        self.checkbox_swarm_bfield.grid(row=3, column=0, pady=(60, 20), padx=10, sticky="n")
        CustomTooltip(self.checkbox_swarm_bfield, "Space magnetic field")

        self.checkbox_swarm_conv = customtkinter.CTkCheckBox(master=self.tabview.tab(tab2), text='Swarm ion flow')
        self.checkbox_swarm_conv.grid(row=3, column=1, pady=(60, 20), padx=10, sticky="n")
        CustomTooltip(self.checkbox_swarm_conv, "Cross-track ion drift")

        # self.checkbox_swarm_efield = customtkinter.CTkCheckBox(master=self.tabview.tab(tab2), text='Swarm elec')
        # self.checkbox_swarm_efield.grid(row=4, column=0, pady=(20, 20), padx=10, sticky="n")
        # CustomTooltip(self.checkbox_swarm_efield, "...")

        self.checkbox_supermag = customtkinter.CTkCheckBox(master=self.tabview.tab(tab2), text='SuperMAG')
        self.checkbox_supermag.grid(row=4, column=1, pady=(20, 20), padx=10, sticky="n")
        CustomTooltip(self.checkbox_supermag, "Ground magnetometer")

        self.checkbox_superdarn = customtkinter.CTkCheckBox(master=self.tabview.tab(tab2), text='SuperDARN')
        self.checkbox_superdarn.grid(row=4, column=0, pady=(20, 20), padx=10, sticky="n")
        CustomTooltip(self.checkbox_superdarn, "Convection velocities")

        self.checkbox_iridium_ampere = customtkinter.CTkCheckBox(master=self.tabview.tab(tab2), text='Iridium/AMPERE')
        self.checkbox_iridium_ampere.grid(row=6, column=0, pady=(20, 20), padx=10, sticky="n")
        CustomTooltip(self.checkbox_iridium_ampere, "Space magnetic perturbations")

        self.checkbox_dmsp_ssies17 = customtkinter.CTkCheckBox(master=self.tabview.tab(tab2), text='DMSP/SSIES 17')
        self.checkbox_dmsp_ssies17.grid(row=5, column=0, pady=(20, 20), padx=10, sticky="n")
        CustomTooltip(self.checkbox_dmsp_ssies17, "Ion drift")

        self.checkbox_dmsp_ssies18 = customtkinter.CTkCheckBox(master=self.tabview.tab(tab2), text='DMSP/SSIES 18')
        self.checkbox_dmsp_ssies18.grid(row=5, column=1, pady=(20, 20), padx=10, sticky="n")
        CustomTooltip(self.checkbox_dmsp_ssies18, "Ion drift")

        # self.entry_data = customtkinter.CTkEntry(self.tabview.tab(tab2), placeholder_text="myfile.cdf") # TODO remove if not fixed
        # self.entry_data.grid(row=5, column=1, columnspan=1, pady=(20, 20), padx=10, sticky="n")

        # Default: select all datasets
        # self.checkbox_swarm_efield.select()
        self.checkbox_swarm_bfield.select()
        # self.checkbox_swarm_conv.select()
        self.checkbox_supermag.select()
        self.checkbox_superdarn.select()
        self.checkbox_iridium_ampere.select()
        self.checkbox_dmsp_ssies17.select()
        self.checkbox_dmsp_ssies18.select()

        # Link to data documentation TODO fix link!
        self.link_data_docu = customtkinter.CTkLabel(self.tabview.tab(tab2), text="Data documentation", text_color="green", cursor="hand2")
        self.link_data_docu.grid(row=9, column=0, columnspan=2, padx=35, pady=(25, 0), sticky='nsew') #pady=(25, 5)
        self.link_data_docu.bind("<Button-1>", lambda e: webbrowser.open(""))

        #######
        # TAB 3 - Conductance method

        self.label_conductance_optmenu = customtkinter.CTkLabel(self.tabview.tab(tab3), text="Conductance estimates:", wraplength=150)
        self.label_conductance_optmenu.grid(row=1, column=0, columnspan=3, padx=10, pady=(30, 5), sticky="n")
        self.optmenu_conductance = customtkinter.CTkOptionMenu(self.tabview.tab(tab3), dynamic_resizing=True,
                                                        values=["Hardy model", "Zang & Paxton model"])
        self.optmenu_conductance.grid(row=2, column=0, columnspan=3, padx=10, pady=(5, 20))
        self.optmenu_conductance.set("Zang & Paxton model")

        for i in range(3):
            self.tabview.tab(tab3).grid_columnconfigure(i, weight=1) # Make columns expand nicely

        # Kp index (useful for Hardy model)
        self.label_kp = customtkinter.CTkLabel(self.tabview.tab(tab3), text="Kp:")
        self.label_kp.grid(row=6, column=0, padx=(25, 5), pady=(20, 5), sticky="n")
        self.entry_kp = customtkinter.CTkEntry(self.tabview.tab(tab3), width=60)
        self.entry_kp.grid(row=7, column=0, padx=(25, 5), pady=(0, 20), sticky="n")
        self.entry_kp.insert(0, 4)
        CustomTooltip(self.entry_kp, "Indicator of disturbances in the Earth's magnetic field")

        # F10.7 solar flux (useful for EUV conductance)
        self.label_f107 = customtkinter.CTkLabel(self.tabview.tab(tab3), text="F10.7 (s.f.u):")
        self.label_f107.grid(row=6, column=1, padx=(25, 5), pady=(20, 5), sticky="n")
        self.entry_f107 = customtkinter.CTkEntry(self.tabview.tab(tab3), width=60)
        self.entry_f107.grid(row=7, column=1, padx=(25, 5), pady=(0, 20), sticky="n")
        self.entry_f107.insert(0, 100)
        CustomTooltip(self.entry_f107, "Solar radio flux at 10.7 cm (solar activity indicator)")

        # Background/starlight (useful for EUV conductance)
        self.label_background = customtkinter.CTkLabel(self.tabview.tab(tab3), text="Background:") # add info/explnanation for all these parameters
        self.label_background.grid(row=6, column=2, padx=(25, 5), pady=(20, 5), sticky="n")
        self.entry_background = customtkinter.CTkEntry(self.tabview.tab(tab3), width=60)
        self.entry_background.grid(row=7, column=2, padx=(25, 5), pady=(0, 20), sticky="n")
        self.entry_background.insert(0, 2)
        CustomTooltip(self.entry_background, "Background conductance - somthg about starlight? fix")

        #############
        # COLUMN1/ BOTTOM ROW (Grid parameters)
        #############

        self.frame_gridparam = customtkinter.CTkFrame(self, corner_radius=10) #, width=col1_width
        self.frame_gridparam.grid(row=1, column=1, padx=(20, 0), pady=(10, 20), sticky="nsew")
        self.frame_gridparam.grid_columnconfigure((0,1), weight=1)
        # self.frame_gridparam.grid_propagate(False)

        self.label_grid_param = customtkinter.CTkLabel(self.frame_gridparam, text="Grid parameters", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label_grid_param.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        self.label_L = customtkinter.CTkLabel(self.frame_gridparam, text="Along-track \n dimension (km):", anchor='center') # but in reality cross-track dimension of analysis grid
        self.label_W = customtkinter.CTkLabel(self.frame_gridparam, text="Cross-track \n dimension (km):", anchor='center') # along-track dimension of analysis grid
        self.label_L.grid(row=2, column=0, padx=10, pady=10, sticky="n")
        self.label_W.grid(row=2, column=1, padx=10, pady=10, sticky="n")

        self.entry_L = customtkinter.CTkEntry(self.frame_gridparam, width=70)
        self.entry_W = customtkinter.CTkEntry(self.frame_gridparam, width=70)
        self.entry_L.grid(row=3, column=0, padx=10, pady=3)
        self.entry_W.grid(row=3, column=1, padx=10, pady=3)

        self.label_Lres = customtkinter.CTkLabel(self.frame_gridparam, text="Along-track \n resolution (km):", anchor='center')
        self.label_Wres = customtkinter.CTkLabel(self.frame_gridparam, text="Cross-track \n resolution (km):", anchor='center')
        self.label_Lres.grid(row=4, column=0, padx=10, pady=(30,10), sticky="n")
        self.label_Wres.grid(row=4, column=1, padx=10, pady=(30,10), sticky="n")

        self.entry_Lres = customtkinter.CTkEntry(self.frame_gridparam, width=70)
        self.entry_Wres = customtkinter.CTkEntry(self.frame_gridparam, width=70)
        self.entry_Lres.grid(row=5, column=0, padx=10, pady=3)
        self.entry_Wres.grid(row=5, column=1, padx= 10, pady=3)

        self.entry_L.insert(0, "2000")
        self.entry_W.insert(0, "1500")
        self.entry_Lres.insert(0, "200")
        self.entry_Wres.insert(0, "200")

        # # mirror entries
        # self.link_grid_entries(self.entry_L, self.entry_W)
        # self.link_grid_entries(self.entry_Lres, self.entry_Wres)

        # shift the grid center wres km in cross-track direction
        # TODO Kalle: what does "unit of R" mean? (in CSgrid)
        self.label_wshift = customtkinter.CTkLabel(self.frame_gridparam, text="Shift center (km):", anchor='center')
        self.label_wshift.grid(row=6, column=0, padx=(10,0), pady=30, sticky='e')
        self.entry_wshift = customtkinter.CTkEntry(self.frame_gridparam, width=55)
        self.entry_wshift.grid(row=6, column=1, padx=(7,0), pady=15, sticky='w')
        self.entry_wshift.insert(0, 0)
        CustomTooltip(self.entry_wshift, "Shift the grid center horizontally (cross-track) to align the Swarm track \n (positive = left, negative = right)")

        #########
        # COLUMN2 (OUTPUTS)
        #########

        self.col2_width = 450
        self.output_height = 400

        self.output_container = customtkinter.CTkFrame(self,  fg_color="transparent")
        self.output_container.grid(row=0, column=2, rowspan=2, padx=(20,0), pady=(20,20), sticky="nsew")

        self.output_container.grid_rowconfigure(0, weight=1)
        self.output_container.grid_rowconfigure(1, weight=1)
        self.output_container.grid_columnconfigure(0, weight=1)

        self.output_container.bind("<Configure>", self.keep_ratio)

        ######
        # Satellite track + grid + data distribution

        self.frame_data = customtkinter.CTkFrame(self.output_container)
        self.frame_data.grid(row=0, column=0, sticky="ns", pady=(0,10))

        self.frame_data.grid_propagate(False)
        self.frame_data.grid_columnconfigure((0), weight=1)
        self.frame_data.grid_rowconfigure((0), weight=0)
        self.frame_data.grid_rowconfigure((1), weight=1)

        self.header_frame = customtkinter.CTkFrame(self.frame_data, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, pady=(2, 10), sticky="n")
        self.header_frame.grid_columnconfigure(0, weight=0)
        self.header_frame.grid_columnconfigure(1, weight=0)

        self.label_data_frame = customtkinter.CTkLabel(self.header_frame, text="Input to Lompe: analysis region along satellite track and data distribution", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.label_data_frame.grid(row=0, column=0, sticky="w")

        self.info_icon_gif1 = customtkinter.CTkLabel(self.header_frame, text="ⓘ", width=40, height=40, padx=4, pady=2)
        self.info_icon_gif1.grid(row=0, column=1, padx=(6, 0), sticky="w")
        CustomTooltip(self.info_icon_gif1, "\n Swarm magnetic perturbations (purple) \n Swarm electric field (black)  \n SuperDARN and DMSP/SSIES LOS velocities (green) \n SuperMAG ground magnetic perturbations (orange) \n Iridium/AMPERE magnetic perturbations (blue) \n")

        self.label_data_gif = customtkinter.CTkLabel(self.frame_data, text="Waiting for trajectory animation...")
        self.label_data_gif.grid(row=1, column=0, pady=(0, 30), sticky='nsew')

        # Add output gif controls
        self.icons = Icons()

        self.data_frame_controls = customtkinter.CTkFrame(self.frame_data, fg_color="transparent") #"#FFFFFF"
        self.data_frame_controls.place(relx=0.5, rely=0.97, anchor="center")

        # Play/pause button
        self.btn_play_pause_data = customtkinter.CTkButton(self.data_frame_controls,
                                                           image=self.icons.pause,
                                                           text="",
                                                           width=30,
                                                           height=30,
                                                           fg_color="transparent",
                                                           border_width=0,
                                                           corner_radius=0,
                                                           command=self.toggle_play_pause)

        # Previous/next buttons
        self.btn_next_data = customtkinter.CTkButton(self.data_frame_controls,
                                                     image=self.icons.next,
                                                     text="",
                                                     width=20,
                                                     height=20,
                                                     fg_color="transparent",
                                                     border_width=0,
                                                     corner_radius=0,
                                                     command=self.next_frame)

        self.btn_prev_data = customtkinter.CTkButton(self.data_frame_controls,
                                                     image=self.icons.previous,
                                                     text="",
                                                     width=20,
                                                     height=20,
                                                     fg_color="transparent",
                                                     border_width=0,
                                                     corner_radius=0,
                                                    command=self.prev_frame)
        

        self.btn_prev_data.pack(side="left", padx=5)
        self.btn_play_pause_data.pack(side="left", padx=8)
        self.btn_next_data.pack(side="left", padx=5)

        self.data_frame_controls.place_forget() # hide initially
        
        # Option to open interactive plots
        self.interactive_wdw_data = customtkinter.CTkFrame(self.frame_data, fg_color="transparent") #"#FFFFFF"
        self.interactive_wdw_data.place(relx=0.98, rely=0.97, anchor="e")
        self.btn_int_data = customtkinter.CTkButton(self.interactive_wdw_data,
                                                text="Interactive plots",
                                                width=30,
                                                height=30,
                                                fg_color="transparent",
                                                border_width=0,
                                                corner_radius=0,
                                                command=self.interactive_window_input)
        self.btn_int_data.pack(side="right", padx=5)
        self.interactive_wdw_data.place_forget()

        ######
        # Lompe output

        self.lompe_frame = customtkinter.CTkFrame(self.output_container)
        self.lompe_frame.grid(row=1, column=0, sticky="ns")

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
        self.label_lompe_gif.grid(row=1, column=0, pady=(0, 30), sticky='nsew')

        self.lompe_frame_controls = customtkinter.CTkFrame(self.lompe_frame, fg_color="transparent") #"#FFFFFF"
        self.lompe_frame_controls.place(relx=0.5, rely=0.97, anchor="center")

        # Play/pause button
        self.btn_play_pause_lompe = customtkinter.CTkButton(self.lompe_frame_controls,                                               
                                                            image=self.icons.pause, 
                                                            text="",
                                                            width=30,                  # button width
                                                            height=30,                 # button height
                                                            fg_color="transparent",    # foreground (button face) - CTk supports 'transparent'
                                                            #   hover_color="#67d76e92",   # very light overlay when hovering (optional)
                                                            border_width=0,
                                                            corner_radius=0, 
                                                            command=self.toggle_play_pause)
        
        # Previous/next buttons
        self.btn_next_lompe = customtkinter.CTkButton(self.lompe_frame_controls,
                                                image=self.icons.next,
                                                text="",
                                                width=20,
                                                height=20,
                                                fg_color="transparent",
                                                border_width=0,
                                                corner_radius=0,
                                                command=self.next_frame)

        self.btn_prev_lompe = customtkinter.CTkButton(self.lompe_frame_controls,
                                                image=self.icons.previous,
                                                text="",
                                                width=20,
                                                height=20,
                                                fg_color="transparent",
                                                border_width=0,
                                                corner_radius=0,
                                                command=self.prev_frame)
        
        self.btn_prev_lompe.pack(side="left", padx=5)
        self.btn_play_pause_lompe.pack(side="left", padx=8)
        self.btn_next_lompe.pack(side="left", padx=5)

        self.lompe_frame_controls.place_forget() # hide initially

        # Option to open interactive plots
        self.interactive_wdw_lompe = customtkinter.CTkFrame(self.lompe_frame, fg_color="transparent") #"#FFFFFF"
        self.interactive_wdw_lompe.place(relx=0.98, rely=0.97, anchor="e")
        self.btn_int_lompe = customtkinter.CTkButton(self.interactive_wdw_lompe,
                                                text="Interactive plots",
                                                width=30,
                                                height=30,
                                                fg_color="transparent",
                                                border_width=0,
                                                corner_radius=0,
                                                command=self.interactive_window_output)
        self.btn_int_lompe.pack(side="right", padx=5)
        self.interactive_wdw_lompe.place_forget()


        # Make sure main window limits column 3's stretch
        self.grid_columnconfigure(4, weight=0)

        #########
        # COLUMN3
        #########       

        col3_width = 200

        self.col3_frame = customtkinter.CTkFrame(self, width=col3_width, corner_radius=10, fg_color="transparent")
        self.col3_frame.grid(row=0, column=3, rowspan=2, padx=(20, 10), pady=(20, 20), sticky="nsew")
        self.col3_frame.grid_propagate(False)

        self.col3_frame.grid_columnconfigure(0, weight=1)
        self.col3_frame.grid_rowconfigure((0, 1, 2), weight=1)

        ######
        # Plotting/GIF settings

        self.tabview_fig = customtkinter.CTkTabview(self.col3_frame, corner_radius=8)
        self.tabview_fig.grid(row=0, column=0, pady=(0, 5), sticky="nsew")
        self.tab_plot = self.tabview_fig.add("Plot options")
        self.tab_gif = self.tabview_fig.add("GIF")
        self.tab_plot.grid_columnconfigure((0, 1), weight=1)
        self.tab_gif.grid_columnconfigure(0, weight=1)

        # TAB1
        self.figsize_frame = customtkinter.CTkFrame(self.tab_plot, fg_color="transparent")
        self.figsize_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")
        self.figsize_frame.grid_columnconfigure((0, 1), weight=1)

        # Option to adjust figure size
        # TODO add hspace and wspace? keep only figheight like in lompe? 
        self.label_figh = customtkinter.CTkLabel(self.figsize_frame, text="Fig height:")
        self.label_figh.grid(row=0, column=0, pady=(0, 3))
        self.entry_figh = customtkinter.CTkEntry(self.figsize_frame, width=40)
        self.entry_figh.grid(row=1, column=0, padx=5)
        self.entry_figh.insert(0, 9)
        CustomTooltip(self.entry_figh, "Figure height (inches). Adjust if the plot looks stretched or compressed (which can happen depending on grid shape/size).")

        self.label_figw = customtkinter.CTkLabel(self.figsize_frame, text="Fig width:")
        self.label_figw.grid(row=0, column=1, pady=(0, 3))
        self.entry_figw = customtkinter.CTkEntry(self.figsize_frame, width=40)
        self.entry_figw.grid(row=1, column=1, padx=5)
        self.entry_figw.insert(0, 12.2)
        CustomTooltip(self.entry_figw, "Figure width (inches). Adjust if the plot looks stretched or compressed (which can happen depending on grid shape/size).")

        # Option to switch between geographic and magnetic coords (polar plot)
        self.checkbox_magcoords = customtkinter.CTkCheckBox(self.tab_plot, text='Polar plot in magnetic coords')
        self.checkbox_magcoords.grid(row=2, column=0, columnspan=2, padx=15, pady=(30, 0), sticky="ew")
        CustomTooltip(self.checkbox_magcoords, "The polar plot (top panel) will be shown in magnetic coordinates. Default is geographic") #TODO change that to opposite

        # "Show global data coverage" checkbox
        self.checkbox_showdata = customtkinter.CTkCheckBox(self.tab_plot, text='Show global data coverage')
        self.checkbox_showdata.grid(row=3, column=0, columnspan=2, padx=20, pady=(30, 0), sticky="ew")
        self.checkbox_showdata.select()

        # Re-run SwarmDF button
        self.button_runSwarmDF2 = customtkinter.CTkButton(self.tab_plot, command=self.run_swarm_df, text='Run SwarmDF')
        self.button_runSwarmDF2.grid(row=4, column=0, columnspan=2, pady=(35, 10))

        # TAB2
        # GIF speed parameter 
        self.label_gifspeed = customtkinter.CTkLabel(self.tab_gif, text="Animation speed (ms/frame):")
        self.label_gifspeed.grid(row=1, column=0, pady=(15, 0), sticky="ew")
        self.entry_gifspeed = customtkinter.CTkEntry(self.tab_gif, width=50)
        self.entry_gifspeed.grid(row=2, column=0, pady=(7, 0))
        self.default_speed = 550  # ms
        self.entry_gifspeed.insert(0, self.default_speed)
        CustomTooltip(self.label_gifspeed, text="Time in milliseconds between each frame.\nLower = faster animation (0 stops the GIF).")

        # Apply button
        self.button_apply = customtkinter.CTkButton(self.tab_gif, text="Apply", command=self.apply_gif_parameters)
        self.button_apply.grid(row=3, column=0, pady=(45, 10))

        ######
        # Regularization parameters
        self.regul_section = customtkinter.CTkFrame(self.col3_frame, corner_radius=8)
        self.regul_section.grid(row=1, column=0, pady=5, sticky="nsew")

        self.regul_section.grid_columnconfigure(0, weight=0)  # labels (fixed)
        self.regul_section.grid_columnconfigure(1, weight=1)  # sliders (expand)
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
        
        self.slider_l1.grid(row=1, column=1, columnspan=1, padx=5, pady=(40,0), sticky="ew")

        # L2 parameter
        self.label_l2 = customtkinter.CTkLabel(self.regul_section, text="l2:")
        self.label_l2.grid(row=2, column=0, padx=(5, 0), pady=(15,0), sticky="e")

        self.slider_l2 = customtkinter.CTkSlider(self.regul_section,
                                                 from_=-2, to=5,
                                                 number_of_steps=70,
                                                 orientation="horizontal",
                                                 command=self.update_l2_label  # callback when slider moves
                                                 )
        
        self.slider_l2.grid(row=2, column=1, columnspan=1, padx=5, pady=(20,0), sticky="ew")

        self.slider_l1.set(0)
        self.slider_l2.set(0)

        # Label to show value
        self.label_value_l1 = customtkinter.CTkLabel(self.regul_section, text=f"{self.slider_l1.get():.1f}")
        self.label_value_l1.grid(row=1, column=2, padx=(5,10), pady=(35,0), sticky="w")

        self.label_value_l2 = customtkinter.CTkLabel(self.regul_section, text=f"{self.slider_l2.get():.1f}")
        self.label_value_l2.grid(row=2, column=2, padx=(5,10), pady=(15,0), sticky="w")

        # Apply button (re-run SwarmDF)
        self.lompe_button2 = customtkinter.CTkButton(master=self.regul_section, text="Apply", command=self.apply_new_regularization)
        self.lompe_button2.grid(row=3, column=0, columnspan=3, padx=(10,10), pady=(50,10))
        CustomTooltip(self.lompe_button2, "This will re-run Lompe \n with the new regularizaton parameters")

        ######
        # Validation
        self.validation_section = customtkinter.CTkFrame(self.col3_frame, corner_radius=8)
        self.validation_section.grid(row=2, column=0, pady=(5, 0), sticky="nsew")
        self.validation_section.grid_columnconfigure(0, weight=1)

        self.validation_section_title = customtkinter.CTkLabel(self.validation_section, text="Output \n validation", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.validation_section_title.grid(row=0, column=0, pady=(5, 5))

        # Gamera snapshot
        self.label_Gsnapshot = customtkinter.CTkLabel(self.validation_section, text="Gamera snapshot number:")
        self.label_Gsnapshot.grid(row=1, column=0, padx=(27,0), pady=(35, 0), sticky="w")
        CustomTooltip(self.label_Gsnapshot, "Gamera simulation snapshot index. \n Each index represents a different physical state. \n See the LompeOSSE documentation for details. ")
        self.entry_Gsnapshot = customtkinter.CTkEntry(self.validation_section, width=30)
        self.entry_Gsnapshot.grid(row=1, column=0, padx=(0,25), pady=(38, 0), sticky='e')        
        self.entry_Gsnapshot.insert(0, 0)        

        # Gamera time offset
        self.label_Gtimeoff = customtkinter.CTkLabel(self.validation_section, text="Time offset (hours):")
        self.label_Gtimeoff.grid(row=3, column=0, padx=(40,0), pady=(35, 0), sticky="w")
        CustomTooltip(self.label_Gtimeoff, "Rotates the Gamera snapshot in magnetic local time. \n See the LompeOSSE documentation for details.")
        self.entry_Gtimeoff = customtkinter.CTkEntry(self.validation_section, width=30)
        self.entry_Gtimeoff.grid(row=3, column=0, padx=(0,25), pady=(38, 0), sticky='e')        
        self.entry_Gtimeoff.insert(0, 0) # in hours  

        # Run validation button
        self.button_validate = customtkinter.CTkButton(self.validation_section, text="Validation", command=self.open_validation_window)
        self.button_validate.grid(row=4, column=0, pady=(50, 10))       
        CustomTooltip(self.button_validate, "This will run LompeOSSE \n (validation routine for experiment setup)")

        # Link to LompeOSSE documentation TODO fix link!
        self.link_lompeosse_docu = customtkinter.CTkLabel(self.validation_section, text="LompeOSSE documentation", text_color="green", cursor="hand2")
        self.link_lompeosse_docu.grid(row=5, column=0, columnspan=2, padx=35, pady=(25, 0), sticky='nsew')
        self.link_lompeosse_docu.bind("<Button-1>", lambda e: webbrowser.open(""))

        # ------------ # 
        # check and validate entries

        # TODO add more?
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
        
        for entry, name, default, min_val, max_val in self.validators:
            entry.bind("<FocusOut>", lambda e, entry=entry, name=name, default=default, min_val=min_val, max_val=max_val: 
                        self.validate_entry(entry, name, default, min_val, max_val))
            
# -------------------------------------------------------
# -------------------------------------------------------
# -------------------------------------------------------
# Helper functions 

# TODO move runswarmdf before the helper functions ?
        
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

    def validate_entry(self, entry, name, default=None, min_val=None, max_val=None):
        """
        Safely read a float from an entry widget.
        
        Parameters
        ----------
        entry : Tkinter Entry
            The entry widget to read from.
        name : str
            Name of the parameter (used in error messages)
        default : float, optional
            Value to use if parsing fails
        min_val, max_val : float, optional
            Optional bounds to check
        """

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

        # reflect corrected value in UI
        if default is not None and value == default:
            entry.delete(0, "end")
            entry.insert(0, str(default))

        return True

    #################
    # Sidebar options

    def change_appearance_mode(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

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

        min_seconds = 10 # TODO what should be the minimum time? frame_length + 1s at least, but should it be a few minutes? it should be at least 10 sec (swarm measurement frequency)
        if (input_end - input_start).total_seconds() < min_seconds:
            messagebox.showerror("Error", f"⚠️ Time interval must be at least {min_seconds} seconds.")
            return None, None

        return input_start, input_end

    def load_example_date(self):
        # example_start = datetime(2014, 12, 15, 1, 12, 0)
        # example_end   = datetime(2014, 12, 15, 1, 27, 0)
        example_start = datetime(2014, 12, 15, 1, 15, 0)
        example_end   = datetime(2014, 12, 15, 1, 16, 0)      
        self.entry_start_time.set_datetime(example_start)
        self.entry_end_time.set_datetime(example_end)

    def reset_dates(self):
        self.entry_start_time.reset_to_placeholders()
        self.entry_end_time.reset_to_placeholders()

    #################
    # Grid parameters

    # def link_grid_entries(self, entry_L, entry_W):
    #     def mirror(event):

    #         val = entry_L.get()

    #         # Ignore empty / placeholder-like states
    #         if val.strip():

    #             entry_W.delete(0, "end")
    #             entry_W.insert(0, val)
            
    #     entry_L.bind("<KeyRelease>", mirror)

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
    # GIF functions

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
                self.validation_state["delay"] = new_speed #TODO check if it works!

            print(f"Animation update: applied speed = {new_speed} ms per frame")

        return speed

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

    def interactive_window_input(self):

        plt.switch_backend("TkAgg")
        
        frames = [np.array(f) for f in self.data_frames_pil]

        fig, ax = plt.subplots(figsize=(12, 9))
        ax.axis("off")

        im = ax.imshow(frames[0])

        state = {"i": 0}

        ax.set_title(f"Frame 1 / {len(frames)}", fontsize=15, color='gray', pad=15)
        ax.text(0.5, 1.0001,"< use keyboard navigation >", transform=ax.transAxes, ha="center", fontsize=9, color="gray")

        def update():
            im.set_data(frames[state["i"]])
            ax.set_title(f"Frame {state['i']+1} / {len(frames)}", fontsize=15, color='gray', pad=15)
            fig.canvas.draw_idle()

        def on_key(event):
            if event.key == "right":
                state["i"] = (state["i"] + 1) % len(frames)
                update()
            elif event.key == "left":
                state["i"] = (state["i"] - 1) % len(frames)
                update()
            elif event.key == " ":
                # quick play (hold space vibe)
                state["i"] = (state["i"] + 1) % len(frames)
                update()

        fig.canvas.mpl_connect("key_press_event", on_key)

        plt.show()

    def interactive_window_output(self):

        plt.switch_backend("TkAgg")
        
        frames = [np.array(f) for f in self.lompe_frames_pil]

        fig, ax = plt.subplots(figsize=(12, 9))
        ax.axis("off")

        im = ax.imshow(frames[0])

        state = {"i": 0}

        ax.set_title(f"Frame 1 / {len(frames)}", fontsize=15, color='gray', pad=15)
        ax.text(0.5, 1.0001,"< use keyboard navigation >", transform=ax.transAxes, ha="center", fontsize=9, color="gray")

        def update():
            im.set_data(frames[state["i"]])
            ax.set_title(f"Frame {state['i']+1} / {len(frames)}", fontsize=15, color='gray', pad=15)
            fig.canvas.draw_idle()

        def on_key(event):
            if event.key == "right":
                state["i"] = (state["i"] + 1) % len(frames)
                update()
            elif event.key == "left":
                state["i"] = (state["i"] - 1) % len(frames)
                update()
            elif event.key == " ":
                # quick play (hold space vibe)
                state["i"] = (state["i"] + 1) % len(frames)
                update()

        fig.canvas.mpl_connect("key_press_event", on_key)

        plt.show()

    #################
    # Lompe input

    def lompe_input_UI(self):

        self.error_frame = self.make_error_frame(self.label_data_gif.winfo_width(), self.label_data_gif.winfo_height())

        # Stop previous animation loop
        if hasattr(self, "master_state") and self.master_state.get("job") is not None:
            self.after_cancel(self.master_state["job"])    

        try: 
            # Extract PIL images and individual grids #TODO fix comment!
            lompe_input = LompeInput(self.sat_id, self.start_time, self.end_time, self.datasets, self.mag)
            self.grids, self.analysis_times = lompe_input.build_grids_around_swarm(self.timestep, self.grid_params)
            self.data_objects_per_grid = lompe_input.prepare_lompe_input(self.grids, self.analysis_times) 
            self.data_frames_pil = lompe_input.plot_lompe_input(self.grids, self.analysis_times, self.data_objects_per_grid, self.figh, self.figw, self.speed, self.show_data)

            # # Convert PIL → Tkinter images
            # self.label_data_gif.update_idletasks()
            # w = max(self.label_data_gif.winfo_width() - 40, 1) 
            # h = max(self.label_data_gif.winfo_height(), 1)
            # self.data_frames_tk = [customtkinter.CTkImage(light_image=f.resize((w, h), Image.LANCZOS), size=(w, h)) for f in self.data_frames_pil]

            # Convert PIL → Tkinter images
            self.label_data_gif.update_idletasks()
            w = max(self.label_data_gif.winfo_width() - 40, 1)  # 10px margin each side
            h = max(self.label_data_gif.winfo_height(), 1)
            self.data_frames_tk = [customtkinter.CTkImage(light_image=self.resize_keep_aspect(f, w, h), size=self.resize_keep_aspect(f, w, h).size) for f in self.data_frames_pil]


            # Initialize common "clock" for swarm_trajectory and lompe outputs (controls the timeline for both GIFs i.e, synchronize them)
            self.master_state = {"tracks": [],
                                "current_frame": 0,
                                "playing": True,
                                "job": None,
                                "delay": self.speed, 
                                "scheduler": self.after, 
                                "cancel": self.after_cancel}

        except Exception as e:
            print("Error running lompe_input_UI:", e)

            # replace frames with a single “error” image
            w = max(self.label_data_gif.winfo_width() - 40, 1)
            h = max(self.label_data_gif.winfo_height(), 1)
            error_img = customtkinter.CTkImage(light_image=self.error_frame.resize((w,h), Image.LANCZOS), size=(w,h))
            self.data_frames_tk = [error_img]

            # Display error frame
            self.anim_mgr.register_track(self.data_frames_tk,  self.label_data_gif, self.master_state)
            self.anim_mgr.update_tracks(self.master_state)

            # also replace output if it exists from a previous run
            if hasattr(self, "label_lompe_gif"):
                self.lompe_frames_tk = [error_img]
                self.anim_mgr.register_track(self.lompe_frames_tk, self.label_lompe_gif, self.master_state)
                self.anim_mgr.update_tracks(self.master_state)

            raise RuntimeError from e
        
        # Reset play/pause buttons to match new state
        icon = self.icons.pause if self.master_state["playing"] else self.icons.play
        self.btn_play_pause_data.configure(image=icon)
        if hasattr(self, "btn_play_pause_lompe"):
            self.btn_play_pause_lompe.configure(image=icon)

        # Register/prepare frames for animated GIF
        # self.master_state["tracks"].clear()
        self.anim_mgr.register_track(self.data_frames_tk,  self.label_data_gif, self.master_state)
        self.anim_mgr.update_tracks(self.master_state)

        # Place frame controls
        self.data_frame_controls.place(relx=0.5, rely=0.97, anchor="center")
        self.interactive_wdw_data.place(relx=0.98, rely=0.97, anchor="e")

    #################
    # Lompe output

    def lompe_output_UI(self):

        self.error_frame = self.make_error_frame(self.label_lompe_gif.winfo_width(), self.label_lompe_gif.winfo_height())

        try:
            # Run Lompe analysis, get PIL images
            self.lompe_models = run_lompe(self.analysis_times, self.grids, self.data_objects_per_grid, self.SHs, self.SPs, self.l1, self.l2)
            self.lompe_frames_pil = plot_lompe_output(self.lompe_models, self.sat_id, self.figh, self.speed)

            # Convert PIL → Tkinter images
            self.label_lompe_gif.update_idletasks()
            w = max(self.label_lompe_gif.winfo_width() - 40, 1)  # 10px margin each side
            h = max(self.label_lompe_gif.winfo_height(), 1)
            self.lompe_frames_tk = [customtkinter.CTkImage(light_image=self.resize_keep_aspect(f, w, h), size=self.resize_keep_aspect(f, w, h).size) for f in self.lompe_frames_pil]
            
        except Exception as e:
            print("Error running lompe_output_UI:", e)
            # replace frames with a single “error” image
            w = max(self.label_lompe_gif.winfo_width() - 40, 1)
            h = max(self.label_lompe_gif.winfo_height(), 1)
            error_img = customtkinter.CTkImage(light_image=self.error_frame.resize((w,h), Image.LANCZOS), size=(w,h))
            self.lompe_frames_tk = [error_img]

            # Display error frame
            self.anim_mgr.register_track(self.lompe_frames_tk, self.label_lompe_gif, self.master_state)
            self.anim_mgr.update_tracks(self.master_state)

            raise RuntimeError from e
        
        # Register/prepare frames for animated GIF
        self.anim_mgr.register_track(self.lompe_frames_tk, self.label_lompe_gif, self.master_state)
        self.anim_mgr.update_tracks(self.master_state)

        # Place frame controls
        self.lompe_frame_controls.place(relx=0.5, rely=0.97, anchor="center")
        self.interactive_wdw_lompe.place(relx=0.98, rely=0.97, anchor="e")

        if self.lompe_button:
            self.lompe_button.grid_forget()


    # Error placeholder
    def make_error_frame(self, width, height, text="An error occured... "):
        img = Image.new("RGBA", (width, height), (150, 0, 0, 80))
        draw = ImageDraw.Draw(img)

        font = ImageFont.load_default()
        w, h = draw.textbbox((0,0), text, font=font)[2:] 
        draw.text(((width-w)//2, (height-h)//2), text, fill=(255,255,255,255))
        return img
    
    def resize_keep_aspect(self, img, max_w, max_h):
        orig_w, orig_h = img.size
        scale = min(max_w / orig_w, max_h / orig_h)
        new_size = (int(orig_w * scale), int(orig_h * scale))
        return img.resize(new_size, Image.LANCZOS)

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

        # Run lompe with new parameters
        self.lompe_output_UI()

    #################
    # Validation (LompeOSSE)
    
    # TODO clean up this function
    def open_validation_window(self):
        self.validation_window = customtkinter.CTkToplevel(self)
        self.validation_window.title("LompeOSSE validation output")
        self.validation_window.geometry(f"{1200}x{500}") #1000x400   # large window
        
        # Container for both plots
        self.plots_container = customtkinter.CTkFrame(self.validation_window, 
                                                      width=self.col2_width + self.col2_width/1.5, 
                                                      height=self.output_height-100)
        self.plots_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.plots_container.grid_columnconfigure(0, weight=2)  # big
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
                                                           image=self.icons.previous,
                                                           text="",
                                                           width=20,
                                                           height=20,
                                                           fg_color="transparent",
                                                           command=self.prev_frame_validation)

        self.btn_play_pause_validation = customtkinter.CTkButton(self.validation_controls,
                                                                 image=self.icons.pause,
                                                                 text="",
                                                                 width=30,
                                                                 height=30,
                                                                 fg_color="transparent",
                                                                 command=self.toggle_play_pause_validation)

        self.btn_next_validation = customtkinter.CTkButton(self.validation_controls,
                                                           image=self.icons.next,
                                                           text="",
                                                           width=20,
                                                           height=20,
                                                           fg_color="transparent",
                                                           command=self.next_frame_validation)

        self.btn_prev_validation.pack(side="left", padx=10)
        self.btn_play_pause_validation.pack(side="left", padx=10)
        self.btn_next_validation.pack(side="left", padx=10)

        # Status label
        self.status_label = customtkinter.CTkLabel(self.validation_window,
                                                   text="Running LompeOSSE…",
                                                   font=customtkinter.CTkFont(size=14, weight="bold"))
        self.status_label.pack(pady=2)

    def lompeOSSE_UI(self):

        # Run LompeOSSE and create output (PIL images)
        t0 = tt.perf_counter()

        lompeOSSE_models, gamera_models = run_lompeOSSE(self.lompe_models, self.timeoff, self.snapshot)
        
        t1 = tt.perf_counter()
        print("run lompeosse:", t1 - t0)


        self.lompeOSSE_frames_pil, self.gamera_frames_pil = plot_lompeOSSE_output(lompeOSSE_models, gamera_models, self.figh, self.speed)
        t2 = tt.perf_counter()
        print("all lompeosse plots:", t2 - t1)

        # Convert PIL → Tkinter images
        # self.validation_window.update_idletasks()

        # w1 = self.lompe_plot_frame.winfo_width()
        # h1 = self.lompe_plot_frame.winfo_height()
        # self.lompeOSSE_frames_tk = [customtkinter.CTkImage(light_image=f.resize((w1, h1), Image.LANCZOS),
        #                    size=(w1, h1)) for f in self.lompeOSSE_frames_pil]
                
        # w2 = self.gamera_plot_frame.winfo_width()
        # h2 = self.gamera_plot_frame.winfo_height()
        # self.gamera_frames_tk = [customtkinter.CTkImage(light_image=f.resize((w2, h2), Image.LANCZOS),
        #             size=(w2, h2)) for f in self.gamera_frames_pil]


        self.validation_window.update_idletasks()
        w1 = max(self.lompe_plot_frame.winfo_width() - 40, 1)  # 10px margin each side
        h1 = max(self.lompe_plot_frame.winfo_height(), 1)
        self.lompeOSSE_frames_tk = [customtkinter.CTkImage(light_image=self.resize_keep_aspect(f, w1, h1), size=self.resize_keep_aspect(f, w1, h1).size) for f in self.lompeOSSE_frames_pil]
        w2 = max(self.gamera_plot_frame.winfo_width() - 40, 1)  # 10px margin each side
        h2 = max(self.gamera_plot_frame.winfo_height(), 1)    
        self.gamera_frames_tk = [customtkinter.CTkImage(light_image=self.resize_keep_aspect(f, w2, h2), size=self.resize_keep_aspect(f, w2, h2).size) for f in self.gamera_frames_pil]

        # Initialize animation
        self.validation_state = {"tracks": [],
                                "current_frame": 0,
                                "playing": True,
                                "job": None,
                                "delay": self.speed,
                                "scheduler": self.validation_window.after, 
                                "cancel": self.validation_window.after_cancel}

        # Register/prepare Tkinter images for animation
        self.anim_mgr.register_track(self.lompeOSSE_frames_tk, self.lompe_label,  self.validation_state)
        self.anim_mgr.register_track(self.gamera_frames_tk,    self.gamera_label, self.validation_state)

        # Update validation window label
        self.status_label.configure(text="")

        # Play animation
        # self.anim_mgr.update_tracks(self.validation_state)
        self.play_validation()

# -------------------------------------------------------
# -------------------------------------------------------
# -------------------------------------------------------

    #################
    # Run toolbox! TODO make keep this only in this script + the user selections and organize the rest differently (all the stuff to make a nice layout etc should be somewhere else because not relevant to user)
    def run_swarm_df(self):

        print("--- Running SwarmDF --- ")
        
        self.anim_mgr = AnimationManager()

        # check and validate values from all entries
        for entry, name, default, min_val, max_val in self.validators:
            self.validate_entry(entry, name, default, min_val, max_val)

        self.button_runSwarmDF.configure(state="disabled")

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

        try: 

            ###############
            # Get all input (GUI) info
            ###############

            # demo?
            demo = True if self.switch_demo.get() else False

            # satellite ID
            self.sat_id = self.optmenu_satellite.get()
            if self.sat_id == "Satellite ID":
                messagebox.showerror("Error", "⚠️ Please select a valid Satellite ID (Swarm A, B, or C) and press Run SwarmDF again.")
                return
        
            # time interval
            self.start_time, self.end_time = self.get_start_end_times()
            
            # time step (between frames)
            timestep = float(self.entry_timestep.get())
            unit = self.timestep_unit_var.get()

            if unit == "min":
                timestep *= 60
            elif unit == "h":
                timestep *= 3600

            self.timestep = timestep

            # datasets
            self.datasets2download = []
            # if self.checkbox_swarm_efield.get():
            #     self.datasets2download.append('swarm_efield')
            #TODO add ion flow
            if self.checkbox_swarm_bfield.get():
                self.datasets2download.append('swarm_mag')
            if self.checkbox_superdarn.get():
                self.datasets2download.append('superdarn')
            if self.checkbox_supermag.get():
                self.datasets2download.append('supermag')
            if self.checkbox_iridium_ampere.get():
                self.datasets2download.append('iridium_ampere')
            if self.checkbox_dmsp_ssies17.get():
                self.datasets2download.append('dmsp_ssies17')
            if self.checkbox_dmsp_ssies18.get():
                self.datasets2download.append('dmsp_ssies18')

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
            self.grid_params = self.get_grid_parameters()
            if self.grid_params is None:
                return

            # Figure size
            self.figw = float(self.entry_figw.get())
            self.figh = float(self.entry_figh.get())

            # Polar plot magnetic coordinates
            self.mag = bool(self.checkbox_magcoords.get())

            # Show global data (outside grid)
            self.show_data = bool(self.checkbox_showdata.get())

            # GIF speed
            self.speed = self.apply_gif_parameters(update_state=False) # ms/frame

            # regularization #TODO Ok kalle?
            slider_l1_value = self.slider_l1.get()
            self.l1 = 10 ** slider_l1_value
            slider_l2_value = self.slider_l2.get()
            self.l2 = 10 ** slider_l2_value
            self.regul_params = {'l1': self.l1, 'l2': self.l2}

            # validation (LompeOSSE)
            self.run_validation = self.checkbox_lompeosse.get()
            self.timeoff = int(self.entry_Gtimeoff.get())
            self.snapshot = int(self.entry_Gsnapshot.get())

            # Collect parameters from GUI for generating Python code
            self.config = build_config_dict(self.sat_id, 
                                            self.start_time, 
                                            self.end_time, 
                                            self.timestep,
                                            self.datasets2download, 
                                            self.conductance_method, 
                                            self.conductance_params, 
                                            self.grid_params, 
                                            self.regul_params, 
                                            self.speed,
                                            self.mag, 
                                            self.run_validation, 
                                            self.timeoff, 
                                            self.snapshot)

            ######################
            # Collect data
            ######################            

            datahandler = DataManager(self.start_time, self.end_time, self.datasets2download, demo = demo)
            self.datasets = datahandler.datasets
            
            ######################
            # Swarm orbit animation
            ######################
            
            input_ok = True

            try:
                self.lompe_input_UI()
            except RuntimeError:
                input_ok = False

            if not input_ok:
                print('Stopping pipeline: no valid input')    
                # print('SwarmDF failed')
                return  # stops SwarmDF

            ######################
            # Define conductances 
            ######################

            self.SHs, self.SPs = compute_conductances(self.conductance_method, self.analysis_times, self.grids, self.conductance_params)
                    
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

                    try:
                        self.lompe_output_UI()
                    except RuntimeError:
                        print('SwarmDF failed')

            ######################
            # Show output animations (gifs) 
            ######################

            self.play()
            #TODO see if there's a way to show swarm trajectory before lompe output is ready

            ######################
            # Lompe_OSSE validation 
            ######################

            # TODO it opens the validatio window once everything else is done, I would like things to show one after another 
            if self.checkbox_lompeosse.get():
                
                # Create pop-up window
                self.open_validation_window()
                
                # Run LompeOSSE analysis and display output in the validation window
                self.lompeOSSE_UI()

            ######################
            # Generate Python code
            ######################

            if self.switch_pythoncode.get():

                # filename
                if self.entry_codename.get():
                    fn= self.entry_codename.get()
                else:
                    fn= 'SwarmDF_script.py'
            
                generate_python_code(self.config, fn)


        except Exception as e:
            print(e)
            print("Coudln't run SwarmDF, the following exception occured:", e) #TODO fix this, maybe remove eventually?

        finally: # ALWAYS executed (success OR error)

            if hasattr(self, "progressbar1"):
                self.progressbar1.stop()
                self.progressbar1.destroy()

            if hasattr(self, "progressbar2"):
                self.progressbar2.stop()
                self.progressbar2.destroy()

            self.button_runSwarmDF.configure(state="enabled")





class DateTimeEntry(customtkinter.CTkFrame):
    def __init__(self, master, label, default=None):
        super().__init__(master)

        # Label
        lab = customtkinter.CTkLabel(self, text=label)
        lab.grid(row=0, column=0, columnspan=13, pady=(0, 5), sticky="w")
        CustomTooltip(lab, "User-defined time interval is used to define grid centers; \n actual data intervals are determined dynamically per grid.")

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
        cal = Calendar(top,
                       selectmode="day",
                       date_pattern="yyyy-mm-dd",
                       year=y,
                       month=m,
                       day=d, 
                       mindate=datetime(2013, 11, 25),
                       maxdate=date.today(),
                       showothermonthdays=False,
                       headersforeground='darkgrey',
                       selectforeground='green',
                       normalforeground='white', 
                       weekendforeground='white',
                       disableddayforeground='grey',
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

        def mirror(event, idx):
            val = start.entries[idx].get()
            ph = start.placeholders[idx]

            if val != ph:
                end.entries[idx].delete(0, "end")
                end.entries[idx].insert(0, val)
                end.entries[idx].configure(text_color="white")

        def select_all(event):
            event.widget.select_range(0, "end")
            event.widget.icursor("end")

        for i, entry in enumerate(start.entries):
            entry.bind("<KeyRelease>", lambda e, i=i: mirror(e, i))
            entry.bind("<FocusIn>", select_all)


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


class AnimationManager:

    def register_track(self, frames, widget, state):
        """ 
        Register a GIF animation as a passive object.
        It does not start animation; it only stores frames and target label.
        (Swarm orbit and lompe plots) only
        """
        track = {"frames": frames, "widget": widget}
        state['tracks'].append(track)
        
        return track

    def update_tracks(self, state):
        """
        Draw current frame for all registered animations.
        """
        i = state["current_frame"]

        for track in state['tracks']:
            frames = track["frames"]
            widget = track["widget"]

            frame = frames[i % len(frames)]
            widget.configure(image=frame, text="")
            widget.image = frame  # keep reference

    def play_generic(self, state):
        """
        Advance global frame counter and update all animations.
        This is the single timing loop for the whole GUI (both GIFs).
        Timing loop
        """
        if not state["playing"]:
            return

        state["current_frame"] = (state["current_frame"] + 1) #) % len(state["frames"])
        self.update_tracks(state)

        state["job"] = state["scheduler"](state["delay"], lambda: self.play_generic(state))
    
    def toggle_play_pause_generic(self, state, buttons):
        """
        Play/pause animation
        """
        state["playing"] = not state["playing"]

        # icon = self.icons.pause if state["playing"] else self.icons.play
        # for btn in buttons:
        #     btn.configure(image=icon)

        if state["playing"]:
            self.play_generic(state)
        else:
            if state["job"]:
                state["cancel"](state["job"])
                state["job"] = None
        
        return state["playing"]

    # def step_frame_generic(self, state, step):
    #     """
    #     Manual stepping
    #     """
    #     state["playing"] = False

    #     if state["job"]:
    #         state["cancel"](state["job"])
    #         state["job"] = None

    #     state["current_frame"] = state["current_frame"] + step

    #     self.update_tracks(state)

    def step_frame_generic(self, state, step, toggle_callback=None):
        """
        Manual stepping
        """
        # if currently playing → stop via existing logic (also updates icons)
        if state.get("playing", False) and toggle_callback is not None:
            toggle_callback()

        state["playing"] = False

        if state["job"]:
            state["cancel"](state["job"])
            state["job"] = None

        state["current_frame"] = state["current_frame"] + step

        self.update_tracks(state)

if __name__ == "__main__":
    app = SwarmDFGUI()
    app.mainloop()


