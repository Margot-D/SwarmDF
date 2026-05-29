import customtkinter

def open_validation_window(gui):

    gui.validation_window = customtkinter.CTkToplevel(gui)
    gui.validation_window.title("LompeOSSE validation output")
    gui.validation_window.geometry(f"{1200}x{500}")
    
    gui.plot_container = customtkinter.CTkFrame(gui.validation_window, width=450 + 450/1.5, height=300)
    gui.plot_container.pack(fill="both", expand=True, padx=10, pady=10)
    gui.plot_container.grid_columnconfigure(0, weight=2)
    gui.plot_container.grid_columnconfigure(1, weight=2)
    gui.plot_container.grid_rowconfigure(0, weight=1)

    # LompeOSSE results
    gui.frame_lompeosse = customtkinter.CTkFrame(gui.plot_container)
    gui.frame_lompeosse.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
    gui.label_lompeosse = customtkinter.CTkLabel(gui.frame_lompeosse, text="")
    gui.label_lompeosse.pack(fill="both", expand=True)

    # Gamera quantities
    gui.frame_gamera = customtkinter.CTkFrame(gui.plot_container)
    gui.frame_gamera.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
    gui.label_gamera = customtkinter.CTkLabel(gui.frame_gamera, text="")
    gui.label_gamera.pack(fill="both", expand=True)

    # Progress bar
    gui.progress_validation = customtkinter.CTkProgressBar(gui.validation_window, mode="indeterminate")
    gui.progress_validation.pack(side="bottom", pady=15)
    gui.progress_validation.start()

    # Status label
    gui.status_label = customtkinter.CTkLabel(gui.validation_window, text="Running LompeOSSE…", font=customtkinter.CTkFont(size=14, weight="bold"))
    gui.status_label.pack(side='bottom', pady=2)

    # GIF controls 

    gui.validation_controls = customtkinter.CTkFrame(gui.validation_window, fg_color="transparent")
    gui.validation_controls.pack(side="bottom", pady=5)

    gui.button_prev_val = customtkinter.CTkButton(gui.validation_controls,
                                                  image=gui.icons.previous,
                                                  text="",
                                                  width=20, height=20,
                                                  fg_color="transparent",
                                                  command=gui.prev_frame_validation)

    gui.button_playpause_val = customtkinter.CTkButton(gui.validation_controls,
                                                       image=gui.icons.pause,
                                                       text="",
                                                       width=30, height=30,
                                                       fg_color="transparent",
                                                       command=gui.toggle_play_pause_validation)

    gui.button_next_val = customtkinter.CTkButton(gui.validation_controls,
                                                  image=gui.icons.next,
                                                  text="",
                                                  width=20, height=20,
                                                  fg_color="transparent",
                                                  command=gui.next_frame_validation)

    gui.button_prev_val.pack(side="left", padx=10)
    gui.button_playpause_val.pack(side="left", padx=10)
    gui.button_next_val.pack(side="left", padx=10)
    gui.validation_controls.pack_forget() # hide initially

    # Interactive plots

    gui.frame_interactive_window_val = customtkinter.CTkFrame(gui.validation_window, fg_color="transparent") #"#FFFFFF"
    gui.frame_interactive_window_val.place(relx=0.98, rely=0.97, anchor="e")
    gui.button_intwdw_val = customtkinter.CTkButton(gui.frame_interactive_window_val,
                                                    text="Interactive plots",
                                                    width=30, height=30,
                                                    fg_color="transparent",
                                                    border_width=0, corner_radius=0,
                                                    command=gui.interactive_window_validation)
    gui.button_intwdw_val.pack(side="right", padx=5)
    gui.frame_interactive_window_val.place_forget()

