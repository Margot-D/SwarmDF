import customtkinter
from ui.helpers.tooltip import CustomTooltip
from ui.helpers.icons import Icons

def build_output_panels(gui):

    gui.col2_width = 450
    gui.output_height = 400

    gui.output_container = customtkinter.CTkFrame(gui,  fg_color="transparent")
    gui.output_container.grid(row=0, column=2, rowspan=2, padx=(20,0), pady=(20,20), sticky="nsew")

    gui.output_container.grid_rowconfigure(0, weight=1)
    gui.output_container.grid_rowconfigure(1, weight=1)
    gui.output_container.grid_columnconfigure(0, weight=1)

    gui.output_container.bind("<Configure>", gui.keep_ratio)

    ######
    # Satellite track + grid + data distribution

    gui.frame_data = customtkinter.CTkFrame(gui.output_container)
    gui.frame_data.grid(row=0, column=0, sticky="ns", pady=(0,10))

    gui.frame_data.grid_propagate(False)
    gui.frame_data.grid_columnconfigure((0), weight=1)
    gui.frame_data.grid_rowconfigure((0), weight=0)
    gui.frame_data.grid_rowconfigure((1), weight=1)

    gui.header_frame = customtkinter.CTkFrame(gui.frame_data, fg_color="transparent")
    gui.header_frame.grid(row=0, column=0, pady=(2, 10), sticky="n")
    gui.header_frame.grid_columnconfigure(0, weight=0)
    gui.header_frame.grid_columnconfigure(1, weight=0)

    gui.label_data_frame = customtkinter.CTkLabel(gui.header_frame, text="Input to Lompe: analysis region along satellite track and data distribution", font=customtkinter.CTkFont(size=14, weight="bold"))
    gui.label_data_frame.grid(row=0, column=0, sticky="w")

    gui.info_icon_gif1 = customtkinter.CTkLabel(gui.header_frame, text="ⓘ", width=40, height=40, padx=4, pady=2)
    gui.info_icon_gif1.grid(row=0, column=1, padx=(6, 0), sticky="w")
    CustomTooltip(gui.info_icon_gif1, "\n Swarm magnetic perturbations (purple) \n Swarm electric field (black)  \n SuperDARN and DMSP/SSIES LOS velocities (green) \n SuperMAG ground magnetic perturbations (orange) \n Iridium/AMPERE magnetic perturbations (blue) \n")

    gui.label_data_gif = customtkinter.CTkLabel(gui.frame_data, text="Waiting for trajectory animation...")
    gui.label_data_gif.grid(row=1, column=0, pady=(0, 30), sticky='nsew')

    # Add output gif controls
    gui.icons = Icons()

    gui.data_frame_controls = customtkinter.CTkFrame(gui.frame_data, fg_color="transparent") #"#FFFFFF"
    gui.data_frame_controls.place(relx=0.5, rely=0.97, anchor="center")

    # Play/pause button
    gui.btn_play_pause_data = customtkinter.CTkButton(gui.data_frame_controls,
                                                        image=gui.icons.pause,
                                                        text="",
                                                        width=30,
                                                        height=30,
                                                        fg_color="transparent",
                                                        border_width=0,
                                                        corner_radius=0,
                                                        command=gui.toggle_play_pause)

    # Previous/next buttons
    gui.btn_next_data = customtkinter.CTkButton(gui.data_frame_controls,
                                                    image=gui.icons.next,
                                                    text="",
                                                    width=20,
                                                    height=20,
                                                    fg_color="transparent",
                                                    border_width=0,
                                                    corner_radius=0,
                                                    command=gui.next_frame)

    gui.btn_prev_data = customtkinter.CTkButton(gui.data_frame_controls,
                                                    image=gui.icons.previous,
                                                    text="",
                                                    width=20,
                                                    height=20,
                                                    fg_color="transparent",
                                                    border_width=0,
                                                    corner_radius=0,
                                                command=gui.prev_frame)
    

    gui.btn_prev_data.pack(side="left", padx=5)
    gui.btn_play_pause_data.pack(side="left", padx=8)
    gui.btn_next_data.pack(side="left", padx=5)

    gui.data_frame_controls.place_forget() # hide initially
    
    # Option to open interactive plots
    gui.interactive_wdw_data = customtkinter.CTkFrame(gui.frame_data, fg_color="transparent") #"#FFFFFF"
    gui.interactive_wdw_data.place(relx=0.98, rely=0.97, anchor="e")
    gui.button_interactive_wdw_input = customtkinter.CTkButton(gui.interactive_wdw_data,
                                            text="Interactive plots",
                                            width=30,
                                            height=30,
                                            fg_color="transparent",
                                            border_width=0,
                                            corner_radius=0,
                                            command=gui.interactive_window_input)
    gui.button_interactive_wdw_input.pack(side="right", padx=5)
    gui.interactive_wdw_data.place_forget()

    ######
    # Lompe output

    gui.lompe_frame = customtkinter.CTkFrame(gui.output_container)
    gui.lompe_frame.grid(row=1, column=0, sticky="ns")

    gui.lompe_frame.grid_propagate(False)
    gui.lompe_frame.grid_columnconfigure((0), weight=1)
    gui.lompe_frame.grid_rowconfigure(0, weight=0) # title
    gui.lompe_frame.grid_rowconfigure(1, weight=1) # GIF
    gui.lompe_frame.grid_rowconfigure(2, weight=0) # controls

    gui.label_lompe_frame = customtkinter.CTkLabel(gui.lompe_frame,
                                                    text="Lompe output: reconstructed electrodynamics", 
                                                    font=customtkinter.CTkFont(size=14, weight="bold", underline=0))
    gui.label_lompe_frame.grid(row=0, column=0, pady=(2, 10), sticky="n")


    gui.label_lompe_gif = customtkinter.CTkLabel(gui.lompe_frame, text="Waiting for Lompe plot...")
    gui.label_lompe_gif.grid(row=1, column=0, pady=(0, 30), sticky='nsew')

    gui.lompe_frame_controls = customtkinter.CTkFrame(gui.lompe_frame, fg_color="transparent") #"#FFFFFF"
    gui.lompe_frame_controls.place(relx=0.5, rely=0.97, anchor="center")

    # Play/pause button
    gui.btn_play_pause_lompe = customtkinter.CTkButton(gui.lompe_frame_controls,                                               
                                                        image=gui.icons.pause, 
                                                        text="",
                                                        width=30,                  # button width
                                                        height=30,                 # button height
                                                        fg_color="transparent",    # foreground (button face) - CTk supports 'transparent'
                                                        #   hover_color="#67d76e92",   # very light overlay when hovering (optional)
                                                        border_width=0,
                                                        corner_radius=0, 
                                                        command=gui.toggle_play_pause)
    
    # Previous/next buttons
    gui.btn_next_lompe = customtkinter.CTkButton(gui.lompe_frame_controls,
                                            image=gui.icons.next,
                                            text="",
                                            width=20,
                                            height=20,
                                            fg_color="transparent",
                                            border_width=0,
                                            corner_radius=0,
                                            command=gui.next_frame)

    gui.btn_prev_lompe = customtkinter.CTkButton(gui.lompe_frame_controls,
                                            image=gui.icons.previous,
                                            text="",
                                            width=20,
                                            height=20,
                                            fg_color="transparent",
                                            border_width=0,
                                            corner_radius=0,
                                            command=gui.prev_frame)
    
    gui.btn_prev_lompe.pack(side="left", padx=5)
    gui.btn_play_pause_lompe.pack(side="left", padx=8)
    gui.btn_next_lompe.pack(side="left", padx=5)

    gui.lompe_frame_controls.place_forget() # hide initially

    # Option to open interactive plots
    gui.interactive_wdw_lompe = customtkinter.CTkFrame(gui.lompe_frame, fg_color="transparent") #"#FFFFFF"
    gui.interactive_wdw_lompe.place(relx=0.98, rely=0.97, anchor="e")
    gui.button_interactive_wdw_output = customtkinter.CTkButton(gui.interactive_wdw_lompe,
                                            text="Interactive plots",
                                            width=30,
                                            height=30,
                                            fg_color="transparent",
                                            border_width=0,
                                            corner_radius=0,
                                            command=gui.interactive_window_output)
    gui.button_interactive_wdw_output.pack(side="right", padx=5)
    gui.interactive_wdw_lompe.place_forget()


    # Make sure main window limits column 3's stretch
    gui.grid_columnconfigure(4, weight=0)