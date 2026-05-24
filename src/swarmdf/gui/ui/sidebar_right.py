import customtkinter
from ui.helpers.tooltip import CustomTooltip
import webbrowser

def build_right_sidebar(gui):

        gui.right_sidebar = customtkinter.CTkFrame(gui, width=200, corner_radius=10, fg_color="transparent")
        gui.right_sidebar.grid(row=0, column=3, rowspan=2, padx=(20, 10), pady=(20, 20), sticky="nsew")
        gui.right_sidebar.grid_propagate(False)
        gui.right_sidebar.grid_columnconfigure(0, weight=1)
        gui.right_sidebar.grid_rowconfigure((0, 1, 2), weight=1)

        ##############
        # Top panel

        gui.tabview = customtkinter.CTkTabview(gui.right_sidebar, corner_radius=8)
        gui.tabview.grid(row=0, column=0, pady=(0, 5), sticky="nsew")
        gui.tab_plot = gui.tabview.add("Plot options")
        gui.tab_gif = gui.tabview.add("GIF")
        gui.tab_plot.grid_columnconfigure((0, 1), weight=1)
        gui.tab_gif.grid_columnconfigure(0, weight=1)

        # TAB 1: Plotting settings

        gui.frame_figsize = customtkinter.CTkFrame(gui.tab_plot, fg_color="transparent")
        gui.frame_figsize.grid(row=1, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")
        gui.frame_figsize.grid_columnconfigure((0, 1), weight=1)

        # Adjust figure size
        # TODO add hspace and wspace? keep only figheight like in lompe? 
        gui.label_figh = customtkinter.CTkLabel(gui.frame_figsize, text="Fig height:")
        gui.label_figh.grid(row=0, column=0, pady=(0, 3))
        gui.entry_figh = customtkinter.CTkEntry(gui.frame_figsize, width=40)
        gui.entry_figh.grid(row=1, column=0, padx=5)
        gui.entry_figh.insert(0, 9)
        CustomTooltip(gui.entry_figh, "Figure height (inches). Adjust if the plot looks stretched or compressed (which can happen depending on grid shape/size).")

        gui.label_figw = customtkinter.CTkLabel(gui.frame_figsize, text="Fig width:")
        gui.label_figw.grid(row=0, column=1, pady=(0, 3))
        gui.entry_figw = customtkinter.CTkEntry(gui.frame_figsize, width=40)
        gui.entry_figw.grid(row=1, column=1, padx=5)
        gui.entry_figw.insert(0, 12.2)
        CustomTooltip(gui.entry_figw, "Figure width (inches). Adjust if the plot looks stretched or compressed (which can happen depending on grid shape/size).")

        # Polar plot coordinates (mag vs. geo)
        gui.checkbox_magcoords = customtkinter.CTkCheckBox(gui.tab_plot, text='Polar plot in magnetic coords') #, command=gui.replot_lompe_input
        gui.checkbox_magcoords.grid(row=2, column=0, columnspan=2, padx=15, pady=(30, 0), sticky="ew")
        CustomTooltip(gui.checkbox_magcoords, "Switch polar plot (top panel) from geographic to magnetic coordinates")

        # Show global data coverage
        gui.checkbox_showdata = customtkinter.CTkCheckBox(gui.tab_plot, text='Show global data coverage')
        gui.checkbox_showdata.grid(row=3, column=0, columnspan=2, padx=20, pady=(30, 0), sticky="ew")
        gui.checkbox_showdata.select()
        CustomTooltip(gui.checkbox_showdata, "Include data outside the analysis grid in the polar plot (top panel)")

        # Replot SwarmDF input
        gui.button_replotinput = customtkinter.CTkButton(gui.tab_plot, command=gui.update_lompe_input, text='Apply')
        gui.button_replotinput.grid(row=4, column=0, columnspan=2, pady=(35, 10))
        CustomTooltip(gui.button_replotinput, "Apply changes to input plot (top panel)")
        gui.button_replotinput.configure(state="disabled")

        # TAB 2: GIF speed

        gui.label_gifspeed = customtkinter.CTkLabel(gui.tab_gif, text="Animation speed (ms/frame):")
        gui.label_gifspeed.grid(row=1, column=0, pady=(15, 0), sticky="ew")
        gui.entry_gifspeed = customtkinter.CTkEntry(gui.tab_gif, width=50)
        gui.entry_gifspeed.grid(row=2, column=0, pady=(7, 0))
        gui.default_speed = 550  # ms
        gui.entry_gifspeed.insert(0, gui.default_speed)
        CustomTooltip(gui.label_gifspeed, text="Time in milliseconds between each frame.\nLower = faster animation (0 stops the GIF).")

        # Apply new speed
        gui.button_apply = customtkinter.CTkButton(gui.tab_gif, text="Apply", command=gui.apply_gif_parameters)
        gui.button_apply.grid(row=3, column=0, pady=(45, 10))
        CustomTooltip(gui.button_apply, text="Apply new speed to GIFs")
        gui.button_apply.configure(state="disabled")

        ##############
        # Regularization parameters

        gui.frame_regul = customtkinter.CTkFrame(gui.right_sidebar, corner_radius=8)
        gui.frame_regul.grid(row=1, column=0, pady=5, sticky="nsew")
        gui.frame_regul.grid_columnconfigure(0, weight=0)
        gui.frame_regul.grid_columnconfigure(1, weight=1)  
        gui.frame_regul.grid_columnconfigure(2, weight=0)

        gui.header_frame_regul = customtkinter.CTkLabel(gui.frame_regul, text="Regularization \n parameters", font=customtkinter.CTkFont(size=14, weight="bold"))
        gui.header_frame_regul.grid(row=0, column=0, columnspan=3, pady=(5, 5), sticky="ew")

        # L1 parameter
        gui.label_l1 = customtkinter.CTkLabel(gui.frame_regul, text="l1:")
        gui.label_l1.grid(row=1, column=0, padx=(5, 0), pady=(35,0), sticky="e")

        gui.slider_l1 = customtkinter.CTkSlider(gui.frame_regul, orientation="horizontal", command=gui.update_l1_label,
                                                from_=-2, to=5,
                                                number_of_steps=70)
        gui.slider_l1.grid(row=1, column=1, columnspan=1, padx=5, pady=(40,0), sticky="ew")

        gui.value_l1 = customtkinter.CTkLabel(gui.frame_regul, text=f"{gui.slider_l1.get():.1f}")
        gui.value_l1.grid(row=1, column=2, padx=(5,10), pady=(35,0), sticky="w")

        # L2 parameter
        gui.label_l2 = customtkinter.CTkLabel(gui.frame_regul, text="l2:")
        gui.label_l2.grid(row=2, column=0, padx=(5, 0), pady=(15,0), sticky="e")
        gui.slider_l2 = customtkinter.CTkSlider(gui.frame_regul, orientation="horizontal", command=gui.update_l2_label,
                                                from_=-2, to=5,
                                                number_of_steps=70)
        gui.slider_l2.grid(row=2, column=1, columnspan=1, padx=5, pady=(20,0), sticky="ew")

        gui.value_l2 = customtkinter.CTkLabel(gui.frame_regul, text=f"{gui.slider_l2.get():.1f}")
        gui.value_l2.grid(row=2, column=2, padx=(5,10), pady=(15,0), sticky="w")

        gui.slider_l1.set(0)
        gui.slider_l2.set(0)

        # Rerun Lompe
        gui.button_runlompe = customtkinter.CTkButton(master=gui.frame_regul, text="Run Lompe", command=gui.apply_new_regularization)
        gui.button_runlompe.grid(row=3, column=0, columnspan=3, padx=(10,10), pady=(50,10))
        CustomTooltip(gui.button_runlompe, "Run Lompe \n with the new regularizaton parameters")
        gui.button_runlompe.configure(state="disabled")

        ##############
        # Validation

        gui.frame_validation = customtkinter.CTkFrame(gui.right_sidebar, corner_radius=8)
        gui.frame_validation.grid(row=2, column=0, pady=(5, 0), sticky="nsew")
        gui.frame_validation.grid_columnconfigure(0, weight=1)

        gui.header_frame_validation = customtkinter.CTkLabel(gui.frame_validation, text="Output \n validation", font=customtkinter.CTkFont(size=14, weight="bold"))
        gui.header_frame_validation.grid(row=0, column=0, pady=(5, 5))

        # Gamera snapshot
        gui.label_Gsnapshot = customtkinter.CTkLabel(gui.frame_validation, text="Gamera snapshot number:")
        gui.label_Gsnapshot.grid(row=1, column=0, padx=(27,0), pady=(35, 0), sticky="w")
        gui.entry_Gsnapshot = customtkinter.CTkEntry(gui.frame_validation, width=30)
        gui.entry_Gsnapshot.grid(row=1, column=0, padx=(0,25), pady=(38, 0), sticky='e')        
        CustomTooltip(gui.label_Gsnapshot, "Gamera simulation snapshot index. \n Each index represents a different physical state. \n See the LompeOSSE documentation for details. ")
        gui.entry_Gsnapshot.insert(0, 0)        

        # Gamera time offset
        gui.label_Gtimeoff = customtkinter.CTkLabel(gui.frame_validation, text="Time offset (hours):")
        gui.label_Gtimeoff.grid(row=3, column=0, padx=(40,0), pady=(35, 0), sticky="w")
        gui.entry_Gtimeoff = customtkinter.CTkEntry(gui.frame_validation, width=30)
        gui.entry_Gtimeoff.grid(row=3, column=0, padx=(0,25), pady=(38, 0), sticky='e')        
        CustomTooltip(gui.label_Gtimeoff, "Rotates the Gamera snapshot in magnetic local time. \n See the LompeOSSE documentation for details.")
        gui.entry_Gtimeoff.insert(0, 0) # in hours  

        # Run validation
        gui.button_validate = customtkinter.CTkButton(gui.frame_validation, text="Validation", command=gui.trigger_lompeosse_analysis)
        gui.button_validate.grid(row=4, column=0, pady=(50, 10))       
        CustomTooltip(gui.button_validate, "This will run LompeOSSE \n (validation routine for experiment setup)")
        gui.button_validate.configure(state="disabled")

        # Link to LompeOSSE documentation TODO fix link!
        gui.link_lompeosse_docu = customtkinter.CTkLabel(gui.frame_validation, text="LompeOSSE documentation", text_color="green", cursor="hand2")
        gui.link_lompeosse_docu.grid(row=5, column=0, columnspan=2, padx=35, pady=(25, 0), sticky='nsew')
        gui.link_lompeosse_docu.bind("<Button-1>", lambda e: webbrowser.open(""))

