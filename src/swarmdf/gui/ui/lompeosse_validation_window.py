import customtkinter
from tkinter import messagebox

FONT_BIGGERB = ("DejaVu Sans", 16, "bold")
FONT_NORMAL = ("DejaVu Sans", 14)

def open_lompeosse_window(gui):

    gui.lompeosse_window = customtkinter.CTkToplevel(gui)
    gui.lompeosse_window.title("LompeOSSE output")
    gui.lompeosse_window.geometry(f"{1200}x{630}")
    
    gui.plot_container = customtkinter.CTkFrame(gui.lompeosse_window, width=450 + 450/1.5, height=300)
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
    gui.progress_lompeosse = customtkinter.CTkProgressBar(gui.lompeosse_window, mode="indeterminate")
    gui.progress_lompeosse.pack(side="bottom", pady=15)
    gui.progress_lompeosse.start()

    # Status label
    gui.status_label = customtkinter.CTkLabel(gui.lompeosse_window, text="Running LompeOSSE…", font=FONT_NORMAL)
    gui.status_label.pack(side='bottom', pady=2)

    # Bottom panel with GIF controls, interactive plots button and validation metrics button
    gui.bottom_panel_lompeosse = customtkinter.CTkFrame(gui.lompeosse_window, fg_color="transparent")
    gui.controls_row = customtkinter.CTkFrame(gui.bottom_panel_lompeosse, fg_color="transparent")
    gui.controls_row.pack(fill="x")

    # GIF controls 
    gui.lompeosse_controls = customtkinter.CTkFrame(gui.controls_row, fg_color="transparent")

    gui.button_prev_lompeosse = customtkinter.CTkButton(gui.lompeosse_controls,
                                                        image=gui.icons.previous,
                                                        text="",
                                                        width=20, height=20,
                                                        fg_color="transparent",
                                                        command=gui.prev_frame_validation)

    gui.button_playpause_lompeosse = customtkinter.CTkButton(gui.lompeosse_controls,
                                                             image=gui.icons.pause,
                                                             text="",
                                                             width=30, height=30,
                                                             fg_color="transparent",
                                                             command=gui.toggle_play_pause_validation)

    gui.button_next_lompeosse = customtkinter.CTkButton(gui.lompeosse_controls,
                                                        image=gui.icons.next,
                                                        text="",
                                                        width=20, height=20,
                                                        fg_color="transparent",
                                                        command=gui.next_frame_validation)

    gui.button_prev_lompeosse.pack(side="left", padx=10) # pack in lompeosse_controls frame
    gui.button_playpause_lompeosse.pack(side="left", padx=10)
    gui.button_next_lompeosse.pack(side="left", padx=10)

    gui.lompeosse_controls.pack(anchor="center") # pack subframe into controls_row frame

    # Interactive plots
    gui.frame_bttn_int_wdw_lompeosse = customtkinter.CTkFrame(gui.controls_row, fg_color="transparent") #"#FFFFFF"
    gui.frame_bttn_int_wdw_lompeosse.place(relx=0.98, rely=0.55, anchor="e") # place subframe into controls_row frame

    gui.button_int_wdw_lompeosse = customtkinter.CTkButton(gui.frame_bttn_int_wdw_lompeosse,
                                                           text="Interactive plots",
                                                           width=30, height=30,
                                                           fg_color="transparent",
                                                           border_width=0, corner_radius=0,
                                                           font=FONT_NORMAL,
                                                           command=gui.interactive_window_lompeosse)
    gui.button_int_wdw_lompeosse.pack(side="right", padx=5) # pack in frame_bttn_int_lompeosse frame

    # Validation metrics window button
    gui.button_validation_metrics = customtkinter.CTkButton(gui.bottom_panel_lompeosse, 
                                                            text="Validation metrics",
                                                            width=30, height=30,
                                                            font=FONT_NORMAL,
                                                            command=lambda: open_validation_window(gui))

    gui.button_validation_metrics.pack(pady=2) # pack in bottom_panel_lompeosse panel

    gui.lompeosse_window.protocol("WM_DELETE_WINDOW", lambda: close_lompeosse_window(gui))

def open_validation_window(gui):

    if hasattr(gui, "validation_window") and gui.validation_window is not None and gui.validation_window.winfo_exists():
        gui.validation_window.lift()
        gui.validation_window.focus_force()
        return
    
    gui.validation_window = customtkinter.CTkToplevel(gui.lompeosse_window)
    gui.validation_window.title("LompeOSSE validation metrics")
    gui.validation_window.geometry(f"{800}x{600}")

    # Validation metrics frame and label
    gui.frame_validation = customtkinter.CTkFrame(gui.validation_window)
    gui.frame_validation.pack(fill="both", expand=True, padx=10, pady=10)
    gui.label_validation = customtkinter.CTkLabel(gui.frame_validation, text="")
    gui.label_validation.pack(fill="both", expand=True)

    # Bottom panel:
    gui.bottom_panel_val = customtkinter.CTkFrame(gui.validation_window, fg_color="transparent")
    gui.bottom_panel_val.pack(side="bottom", fill="x", pady=2)

    # GIF controls 
    gui.validation_controls = customtkinter.CTkFrame(gui.bottom_panel_val, fg_color="transparent")

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

    # Interactive plots
    gui.button_intwdw_val = customtkinter.CTkButton(gui.bottom_panel_val,
                                                    text="Interactive plots",
                                                    width=30, height=30,
                                                    fg_color="transparent",
                                                    border_width=0, corner_radius=0,
                                                    font=FONT_NORMAL,
                                                    command=gui.interactive_window_validation)

    gui.validation_controls.place(relx=0.5, rely=0.5, anchor="center")
    gui.button_intwdw_val.pack(side="right", padx=10)

    gui.display_validation()

    gui.validation_window.protocol("WM_DELETE_WINDOW", lambda: close_validation_window(gui))

def close_lompeosse_window(gui):
    """Ask for confirmation before closing a running LompeOSSE analysis"""

    if gui.lompeosse_running:
        answer = messagebox.askyesno("Cancel LompeOSSE",
                                     "LompeOSSE is still running.\n\n"
                                     "Do you want to cancel the analysis and close the window?",
                                     parent=gui.lompeosse_window)

        if not answer:
            return

        # Request cancellation here
        gui.lompeosse_cancel_event.set()

        gui.status_label.configure(text="Cancelling LompeOSSE... This may take some time")

        # Keep the window open until the worker has stopped
        return
    
    gui.lompeosse_window.destroy()

def close_validation_window(gui):

    if hasattr(gui, "validation_track"):
        if gui.validation_track in gui.validation_state["tracks"]:
            gui.validation_state["tracks"].remove(gui.validation_track)
        gui.validation_track = None

    gui.validation_window.destroy()
    gui.validation_window = None