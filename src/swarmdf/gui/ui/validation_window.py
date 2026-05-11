import customtkinter

#TODO clean code

def open_validation_window(gui):
    gui.validation_window = customtkinter.CTkToplevel(gui)
    gui.validation_window.title("LompeOSSE validation output")
    gui.validation_window.geometry(f"{1200}x{500}") #1000x400   # large window
    
    # Progress bar
    gui.progress_validation = customtkinter.CTkProgressBar(gui.validation_window, mode="indeterminate")
    gui.progress_validation.pack(side="bottom", pady=15)
    gui.progress_validation.start()

    # Status label
    gui.status_label = customtkinter.CTkLabel(gui.validation_window, text="Running LompeOSSE…", font=customtkinter.CTkFont(size=14, weight="bold"))
    gui.status_label.pack(side='bottom', pady=2)

    # Container for both plots
    gui.plots_container = customtkinter.CTkFrame(gui.validation_window, 
                                                    width=gui.col2_width + gui.col2_width/1.5, 
                                                    height=gui.output_height-100)
    gui.plots_container.pack(fill="both", expand=True, padx=10, pady=10)

    gui.plots_container.grid_columnconfigure(0, weight=2)  # big
    gui.plots_container.grid_columnconfigure(1, weight=2)  # small
    gui.plots_container.grid_rowconfigure(0, weight=1)

    # LompeOSSE 
    gui.lompe_plot_frame = customtkinter.CTkFrame(gui.plots_container)
    gui.lompe_plot_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
    gui.lompe_label = customtkinter.CTkLabel(gui.lompe_plot_frame, text="")
    gui.lompe_label.pack(fill="both", expand=True)

    # Gamera quantities
    gui.gamera_plot_frame = customtkinter.CTkFrame(gui.plots_container)
    gui.gamera_plot_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
    gui.gamera_label = customtkinter.CTkLabel(gui.gamera_plot_frame, text="")
    gui.gamera_label.pack(fill="both", expand=True)

    #############
    # Validation window layout
    #############

    gui.validation_controls = customtkinter.CTkFrame(gui.validation_window, fg_color="transparent")
    gui.validation_controls.pack(side="bottom", pady=5)

    gui.btn_prev_validation = customtkinter.CTkButton(gui.validation_controls,
                                                        image=gui.icons.previous,
                                                        text="",
                                                        width=20,
                                                        height=20,
                                                        fg_color="transparent",
                                                        command=gui.prev_frame_validation)

    gui.btn_play_pause_validation = customtkinter.CTkButton(gui.validation_controls,
                                                                image=gui.icons.pause,
                                                                text="",
                                                                width=30,
                                                                height=30,
                                                                fg_color="transparent",
                                                                command=gui.toggle_play_pause_validation)

    gui.btn_next_validation = customtkinter.CTkButton(gui.validation_controls,
                                                        image=gui.icons.next,
                                                        text="",
                                                        width=20,
                                                        height=20,
                                                        fg_color="transparent",
                                                        command=gui.next_frame_validation)

    gui.btn_prev_validation.pack(side="left", padx=10)
    gui.btn_play_pause_validation.pack(side="left", padx=10)
    gui.btn_next_validation.pack(side="left", padx=10)

