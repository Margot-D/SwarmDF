import customtkinter
from ui.helpers.icons import Icons

def build_plot_panels(gui):

    gui.plot_container = customtkinter.CTkFrame(gui, fg_color="transparent")
    gui.plot_container.grid(row=0, column=2, rowspan=2, padx=(20,0), pady=(20,20), sticky="nsew")
    gui.plot_container.grid_rowconfigure(0, weight=1)
    gui.plot_container.grid_rowconfigure(1, weight=1)
    gui.plot_container.grid_columnconfigure(0, weight=1)
    gui.plot_container.bind("<Configure>", gui.keep_ratio)

    gui.grid_columnconfigure(4, weight=0)

    ##############
    # Input panel

    gui.frame_input = customtkinter.CTkFrame(gui.plot_container)
    gui.frame_input.grid(row=0, column=0, sticky="ns", pady=(0,10))
    gui.frame_input.grid_propagate(False)
    gui.frame_input.grid_columnconfigure((0), weight=1)
    gui.frame_input.grid_rowconfigure((0), weight=0)
    gui.frame_input.grid_rowconfigure((1), weight=1)

    gui.header_input = customtkinter.CTkLabel(gui.frame_input, text="Input to Lompe: analysis region along satellite track and data distribution", font=customtkinter.CTkFont(size=14, weight="bold", underline=0))
    gui.header_input.grid(row=0, column=0,  pady=(2, 10), sticky="n")

    gui.label_input = customtkinter.CTkLabel(gui.frame_input, text="Waiting for trajectory animation...")
    gui.label_input.grid(row=1, column=0, pady=(0, 30), sticky='nsew')

    # GIF controls and interactive window
    gui.input_ui = create_plot_controls(gui, gui.frame_input, "input")

    # Progress bar #TODO fix 
    gui.progress_input = customtkinter.CTkProgressBar(gui.frame_input, mode="indeterminate")
    gui.progress_input.grid(row=1, column=0, pady=(30, 10))
    
    ##############
    # Output panel

    gui.frame_output = customtkinter.CTkFrame(gui.plot_container)
    gui.frame_output.grid(row=1, column=0, sticky="ns")
    gui.frame_output.grid_propagate(False)
    gui.frame_output.grid_columnconfigure((0), weight=1)
    gui.frame_output.grid_rowconfigure(0, weight=0) # title
    gui.frame_output.grid_rowconfigure(1, weight=1) # GIF
    gui.frame_output.grid_rowconfigure(2, weight=0) # controls

    gui.header_output = customtkinter.CTkLabel(gui.frame_output, text="Lompe output: reconstructed electrodynamics", font=customtkinter.CTkFont(size=14, weight="bold", underline=0))
    gui.header_output.grid(row=0, column=0, pady=(2, 10), sticky="n")

    gui.label_output = customtkinter.CTkLabel(gui.frame_output, text="Waiting for Lompe plot...")
    gui.label_output.grid(row=1, column=0, pady=(0, 30), sticky='nsew')

    # GIF controls and interactive window
    gui.output_ui = create_plot_controls(gui, gui.frame_output, "output")

    # Run Lompe (temporary button)
    gui.button_runlompe_temp = customtkinter.CTkButton(master=gui.frame_output, text="Run Lompe analysis", command=gui.trigger_lompe_analysis, width=170, height=40)
    gui.button_runlompe_temp.grid(row=1, column=0, pady=(0, 20))
    gui.button_runlompe_temp.grid_forget()


def create_plot_controls(gui, parent, kind):

    # --- Animation controls ---

    gui.icons = Icons()

    frame_controls = customtkinter.CTkFrame(parent, fg_color="transparent")
    frame_controls.place(relx=0.5, rely=0.97, anchor="center")

    button_playpause = customtkinter.CTkButton(frame_controls, 
                                               image=gui.icons.pause,
                                               text="",
                                               width=30, height=30,
                                               fg_color="transparent",
                                               border_width=0, corner_radius=0,
                                               command=gui.toggle_play_pause)

    button_prev = customtkinter.CTkButton(frame_controls,
                                          image=gui.icons.previous,
                                          text="",
                                          width=20, height=20,
                                          fg_color="transparent",
                                          border_width=0, corner_radius=0,
                                          command=gui.prev_frame)
    
    button_next = customtkinter.CTkButton(frame_controls,
                                          image=gui.icons.next,
                                          text="",
                                          width=20, height=20,
                                          fg_color="transparent",
                                          border_width=0, corner_radius=0,
                                          command=gui.next_frame)

    button_prev.pack(side="left", padx=5)
    button_playpause.pack(side="left", padx=8)
    button_next.pack(side="left", padx=5)
    frame_controls.place_forget() # hide initially

    # --- Interactive plots button ---

    frame_interactive_window = customtkinter.CTkFrame(parent, fg_color="transparent")
    frame_interactive_window.place(relx=0.98, rely=0.97, anchor="e")

    button_intwdw = customtkinter.CTkButton(frame_interactive_window,
                                            text="Interactive plots",
                                            width=30, height=30,
                                            fg_color="transparent",
                                            border_width=0, corner_radius=0,
                                            command=getattr(gui, f"interactive_window_{kind}")) 

    button_intwdw.pack(side="right", padx=5)
    frame_interactive_window.place_forget()

    return {"frame_controls": frame_controls,
           "playpause": button_playpause,
           "prev": button_prev,
           "next": button_next,
           "frame_interactive": frame_interactive_window,
           "button_interactive": button_intwdw}