import customtkinter
from ui.helpers.tooltip import CustomTooltip
from ui.input_panels import load_example_date


def build_left_sidebar(gui):

    gui.frame_sidebar = customtkinter.CTkFrame(gui, width=140, corner_radius=0)
    gui.frame_sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")

    gui.title_sidebar = customtkinter.CTkLabel(gui.frame_sidebar, text="SwarmDF \n User interface", font=customtkinter.CTkFont(size=20, weight="bold"))
    gui.title_sidebar.grid(row=0, column=0, padx=20, pady=(20, 50))

    # "Run Lompe analysis" checkbox
    gui.checkbox_runlompe = customtkinter.CTkCheckBox(master=gui.frame_sidebar, text=f"Run Lompe analysis")
    gui.checkbox_runlompe.grid(row=3, column=0, padx=20, pady=(20,20))
    gui.checkbox_runlompe.select()
    # CustomTooltip(gui.checkbox_runlompe, text="When not selected, SwarmDF collects the requested data and shows the data coverage around Swarm.")      

    # "Run LompeOSSE validation" checkbox
    gui.checkbox_lompeosse = customtkinter.CTkCheckBox(gui.frame_sidebar, text='Run LompeOSSE validation')
    gui.checkbox_lompeosse.grid(row=4, column=0, padx=20, pady=(20,20))
    # gui.checkbox_lompeosse.select()

    # "Generate Python code" switch
    gui.switch_pythoncode = customtkinter.CTkSwitch(master=gui.frame_sidebar, text=f"Generate Python code") 
    gui.switch_pythoncode.grid(row=5, column=0, padx=20, pady=(20,5))
    CustomTooltip(gui.switch_pythoncode, text="Generate a standalone Python script reproducing the SwarmDF pipeline based on the user-selected configuration. \n This allows the workflow to be rerun outside the GUI.")      

    # User filename for generated Python code
    gui.entry_codename = customtkinter.CTkEntry(master=gui.frame_sidebar, placeholder_text="MyFile.py")
    gui.entry_codename.grid(row=6, column=0, padx=20, pady=5)
    CustomTooltip(gui.entry_codename, "Filename for generated script (default: SwarmDF_script.py")

    # "Run SwarmDF" button
    gui.button_runSwarmDF = customtkinter.CTkButton(gui.frame_sidebar, 
                                                        command=gui.run_swarmdf, 
                                                        text='Run SwarmDF',
                                                        width=160, height=80, font=("Arial", 18))
    gui.button_runSwarmDF.grid(row=7, column=0, padx=20, pady=(100,10))

    # Demo mode switch
    gui.switch_demo = customtkinter.CTkSwitch(master=gui.frame_sidebar, text=f"Demo mode", command=lambda: load_example_date(gui)) 
    gui.switch_demo.grid(row=8, column=0, padx=20, pady=(10,100))
    CustomTooltip(gui.switch_demo, "Use sample datasets for example event and skip data collection")

    # Apparence mode
    gui.frame_sidebar.grid_rowconfigure(9, weight=1)
    gui.label_appearance_mode = customtkinter.CTkLabel(gui.frame_sidebar, text="Appearance Mode:", anchor="w")
    gui.label_appearance_mode.grid(row=10, column=0, padx=20, pady=(10, 0))
    gui.optmenu_appearance_mode = customtkinter.CTkOptionMenu(gui.frame_sidebar, 
                                                                values=["Light", "Dark", "System"],
                                                                command=change_appearance_mode)
    gui.optmenu_appearance_mode.grid(row=11, column=0, padx=20, pady=(10, 10))
    gui.optmenu_appearance_mode.set("Dark")

    # Scaling option
    gui.label_scaling = customtkinter.CTkLabel(gui.frame_sidebar, text="UI Scaling:", anchor="w")
    gui.label_scaling.grid(row=12, column=0, padx=20, pady=(10, 0))
    gui.optmenu_scaling = customtkinter.CTkOptionMenu(gui.frame_sidebar, 
                                                        values=["80%", "90%", "100%", "110%", "120%"],
                                                        command=change_scaling)
    gui.optmenu_scaling.grid(row=13, column=0, padx=20, pady=(10, 20))
    gui.optmenu_scaling.set("100%")

    # return gui.sidebar


#################
# Sidebar options

def change_appearance_mode(new_appearance_mode: str):
    customtkinter.set_appearance_mode(new_appearance_mode)

def change_scaling(new_scaling: str):
    new_scaling_float = int(new_scaling.replace("%", "")) / 100
    customtkinter.set_widget_scaling(new_scaling_float)
