import customtkinter
from ui.helpers.tooltip import CustomTooltip
from ui.validation_window import open_validation_window
from swarmdf.pipeline import compute_swarmdf_validation
import webbrowser

def build_right_sidebar(gui):

        col3_width = 200

        gui.col3_frame = customtkinter.CTkFrame(gui, width=col3_width, corner_radius=10, fg_color="transparent")
        gui.col3_frame.grid(row=0, column=3, rowspan=2, padx=(20, 10), pady=(20, 20), sticky="nsew")
        gui.col3_frame.grid_propagate(False)

        gui.col3_frame.grid_columnconfigure(0, weight=1)
        gui.col3_frame.grid_rowconfigure((0, 1, 2), weight=1)

        ######
        # Plotting/GIF settings

        gui.tabview_fig = customtkinter.CTkTabview(gui.col3_frame, corner_radius=8)
        gui.tabview_fig.grid(row=0, column=0, pady=(0, 5), sticky="nsew")
        gui.tab_plot = gui.tabview_fig.add("Plot options")
        gui.tab_gif = gui.tabview_fig.add("GIF")
        gui.tab_plot.grid_columnconfigure((0, 1), weight=1)
        gui.tab_gif.grid_columnconfigure(0, weight=1)

        # TAB1
        gui.figsize_frame = customtkinter.CTkFrame(gui.tab_plot, fg_color="transparent")
        gui.figsize_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")
        gui.figsize_frame.grid_columnconfigure((0, 1), weight=1)

        # Option to adjust figure size
        # TODO add hspace and wspace? keep only figheight like in lompe? 
        gui.label_figh = customtkinter.CTkLabel(gui.figsize_frame, text="Fig height:")
        gui.label_figh.grid(row=0, column=0, pady=(0, 3))
        gui.entry_figh = customtkinter.CTkEntry(gui.figsize_frame, width=40)
        gui.entry_figh.grid(row=1, column=0, padx=5)
        gui.entry_figh.insert(0, 9)
        CustomTooltip(gui.entry_figh, "Figure height (inches). Adjust if the plot looks stretched or compressed (which can happen depending on grid shape/size).")

        gui.label_figw = customtkinter.CTkLabel(gui.figsize_frame, text="Fig width:")
        gui.label_figw.grid(row=0, column=1, pady=(0, 3))
        gui.entry_figw = customtkinter.CTkEntry(gui.figsize_frame, width=40)
        gui.entry_figw.grid(row=1, column=1, padx=5)
        gui.entry_figw.insert(0, 12.2)
        CustomTooltip(gui.entry_figw, "Figure width (inches). Adjust if the plot looks stretched or compressed (which can happen depending on grid shape/size).")

        # Option to switch between geographic and magnetic coords (polar plot)
        gui.checkbox_magcoords = customtkinter.CTkCheckBox(gui.tab_plot, text='Polar plot in magnetic coords', command=gui.replot_lompe_input)
        gui.checkbox_magcoords.grid(row=2, column=0, columnspan=2, padx=15, pady=(30, 0), sticky="ew")
        CustomTooltip(gui.checkbox_magcoords, "The polar plot (top panel) will be shown in magnetic coordinates. Default is geographic") #TODO change that to opposite

        # "Show global data coverage" checkbox
        gui.checkbox_showdata = customtkinter.CTkCheckBox(gui.tab_plot, text='Show global data coverage')
        gui.checkbox_showdata.grid(row=3, column=0, columnspan=2, padx=20, pady=(30, 0), sticky="ew")
        gui.checkbox_showdata.select()

        # Re-run SwarmDF button
        gui.button_runSwarmDF2 = customtkinter.CTkButton(gui.tab_plot, command=gui.run_swarm_df, text='Run SwarmDF')
        gui.button_runSwarmDF2.grid(row=4, column=0, columnspan=2, pady=(35, 10))

        # TAB2
        # GIF speed parameter 
        gui.label_gifspeed = customtkinter.CTkLabel(gui.tab_gif, text="Animation speed (ms/frame):")
        gui.label_gifspeed.grid(row=1, column=0, pady=(15, 0), sticky="ew")
        gui.entry_gifspeed = customtkinter.CTkEntry(gui.tab_gif, width=50)
        gui.entry_gifspeed.grid(row=2, column=0, pady=(7, 0))
        gui.default_speed = 550  # ms
        gui.entry_gifspeed.insert(0, gui.default_speed)
        CustomTooltip(gui.label_gifspeed, text="Time in milliseconds between each frame.\nLower = faster animation (0 stops the GIF).")

        # Apply button
        gui.button_apply = customtkinter.CTkButton(gui.tab_gif, text="Apply", command=gui.apply_gif_parameters)
        gui.button_apply.grid(row=3, column=0, pady=(45, 10))

        ######
        # Regularization parameters
        gui.regul_section = customtkinter.CTkFrame(gui.col3_frame, corner_radius=8)
        gui.regul_section.grid(row=1, column=0, pady=5, sticky="nsew")

        gui.regul_section.grid_columnconfigure(0, weight=0)  # labels (fixed)
        gui.regul_section.grid_columnconfigure(1, weight=1)  # sliders (expand)
        gui.regul_section.grid_columnconfigure(2, weight=0)  # values (fixed)

        gui.regul_section_title = customtkinter.CTkLabel(gui.regul_section, text="Regularization \n parameters", font=customtkinter.CTkFont(size=14, weight="bold"))
        gui.regul_section_title.grid(row=0, column=0, columnspan=3, pady=(5, 5), sticky="ew")

        # L1 parameter
        gui.label_l1 = customtkinter.CTkLabel(gui.regul_section, text="l1:")
        gui.label_l1.grid(row=1, column=0, padx=(5, 0), pady=(35,0), sticky="e")

        gui.slider_l1 = customtkinter.CTkSlider(gui.regul_section,
                                                        from_=-2, to=5,
                                                        number_of_steps=70,
                                                        orientation="horizontal",
                                                        command=gui.update_l1_label  # callback when slider moves
                                                        )

        gui.slider_l1.grid(row=1, column=1, columnspan=1, padx=5, pady=(40,0), sticky="ew")

        # L2 parameter
        gui.label_l2 = customtkinter.CTkLabel(gui.regul_section, text="l2:")
        gui.label_l2.grid(row=2, column=0, padx=(5, 0), pady=(15,0), sticky="e")

        gui.slider_l2 = customtkinter.CTkSlider(gui.regul_section,
                                                        from_=-2, to=5,
                                                        number_of_steps=70,
                                                        orientation="horizontal",
                                                        command=gui.update_l2_label  # callback when slider moves
                                                        )

        gui.slider_l2.grid(row=2, column=1, columnspan=1, padx=5, pady=(20,0), sticky="ew")

        gui.slider_l1.set(0)
        gui.slider_l2.set(0)

        # Label to show value
        gui.label_value_l1 = customtkinter.CTkLabel(gui.regul_section, text=f"{gui.slider_l1.get():.1f}")
        gui.label_value_l1.grid(row=1, column=2, padx=(5,10), pady=(35,0), sticky="w")

        gui.label_value_l2 = customtkinter.CTkLabel(gui.regul_section, text=f"{gui.slider_l2.get():.1f}")
        gui.label_value_l2.grid(row=2, column=2, padx=(5,10), pady=(15,0), sticky="w")

        # Apply button (re-run SwarmDF)
        gui.lompe_button2 = customtkinter.CTkButton(master=gui.regul_section, text="Apply", command=gui.apply_new_regularization)
        gui.lompe_button2.grid(row=3, column=0, columnspan=3, padx=(10,10), pady=(50,10))
        CustomTooltip(gui.lompe_button2, "This will re-run Lompe \n with the new regularizaton parameters")

        ######
        # Validation
        gui.validation_section = customtkinter.CTkFrame(gui.col3_frame, corner_radius=8)
        gui.validation_section.grid(row=2, column=0, pady=(5, 0), sticky="nsew")
        gui.validation_section.grid_columnconfigure(0, weight=1)

        gui.validation_section_title = customtkinter.CTkLabel(gui.validation_section, text="Output \n validation", font=customtkinter.CTkFont(size=14, weight="bold"))
        gui.validation_section_title.grid(row=0, column=0, pady=(5, 5))

        # Gamera snapshot
        gui.label_Gsnapshot = customtkinter.CTkLabel(gui.validation_section, text="Gamera snapshot number:")
        gui.label_Gsnapshot.grid(row=1, column=0, padx=(27,0), pady=(35, 0), sticky="w")
        CustomTooltip(gui.label_Gsnapshot, "Gamera simulation snapshot index. \n Each index represents a different physical state. \n See the LompeOSSE documentation for details. ")
        gui.entry_Gsnapshot = customtkinter.CTkEntry(gui.validation_section, width=30)
        gui.entry_Gsnapshot.grid(row=1, column=0, padx=(0,25), pady=(38, 0), sticky='e')        
        gui.entry_Gsnapshot.insert(0, 0)        

        # Gamera time offset
        gui.label_Gtimeoff = customtkinter.CTkLabel(gui.validation_section, text="Time offset (hours):")
        gui.label_Gtimeoff.grid(row=3, column=0, padx=(40,0), pady=(35, 0), sticky="w")
        CustomTooltip(gui.label_Gtimeoff, "Rotates the Gamera snapshot in magnetic local time. \n See the LompeOSSE documentation for details.")
        gui.entry_Gtimeoff = customtkinter.CTkEntry(gui.validation_section, width=30)
        gui.entry_Gtimeoff.grid(row=3, column=0, padx=(0,25), pady=(38, 0), sticky='e')        
        gui.entry_Gtimeoff.insert(0, 0) # in hours  

        # TODO should this command call "trigger_lompeosse" which would open the validation window itself?
        # Run validation button
        gui.button_validate = customtkinter.CTkButton(gui.validation_section, text="Validation", command=gui.trigger_lompeosse_analysis)
        gui.button_validate.grid(row=4, column=0, pady=(50, 10))       
        CustomTooltip(gui.button_validate, "This will run LompeOSSE \n (validation routine for experiment setup)")

        # Link to LompeOSSE documentation TODO fix link!
        gui.link_lompeosse_docu = customtkinter.CTkLabel(gui.validation_section, text="LompeOSSE documentation", text_color="green", cursor="hand2")
        gui.link_lompeosse_docu.grid(row=5, column=0, columnspan=2, padx=35, pady=(25, 0), sticky='nsew')
        gui.link_lompeosse_docu.bind("<Button-1>", lambda e: webbrowser.open(""))

