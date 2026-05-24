import customtkinter
from ui.helpers.tooltip import CustomTooltip
from ui.input_panels import load_example_date


def build_left_sidebar(gui):

    gui.left_sidebar = customtkinter.CTkFrame(gui, width=140, corner_radius=0)
    gui.left_sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
    gui.left_sidebar.grid_rowconfigure(9, weight=1)

    gui.header_lsidebar = customtkinter.CTkLabel(gui.left_sidebar, text="SwarmDF \n User interface", font=customtkinter.CTkFont(size=20, weight="bold"))
    gui.header_lsidebar.grid(row=0, column=0, padx=20, pady=(20, 50))

    # Run Lompe analysis
    gui.checkbox_runlompe = customtkinter.CTkCheckBox(master=gui.left_sidebar, text=f"Run Lompe analysis")
    gui.checkbox_runlompe.grid(row=3, column=0, padx=20, pady=(20,20))
    gui.checkbox_runlompe.select()

    # Run LompeOSSE validation
    gui.checkbox_lompeosse = customtkinter.CTkCheckBox(gui.left_sidebar, text='Run LompeOSSE validation')
    gui.checkbox_lompeosse.grid(row=4, column=0, padx=20, pady=(20,20))

    # Generate Python script
    gui.switch_pythonscript = customtkinter.CTkSwitch(master=gui.left_sidebar, text=f"Generate Python code") 
    gui.switch_pythonscript.grid(row=5, column=0, padx=20, pady=(20,5))
    CustomTooltip(gui.switch_pythonscript, text="Generate a standalone Python script reproducing the SwarmDF pipeline based on the user-selected configuration. \n This allows the workflow to be rerun outside the GUI.")      

    # User filename for generated Python script
    gui.entry_filename = customtkinter.CTkEntry(master=gui.left_sidebar, placeholder_text="MyFile.py")
    gui.entry_filename.grid(row=6, column=0, padx=20, pady=5)
    CustomTooltip(gui.entry_filename, "Filename for generated script (default: SwarmDF_script.py")

    # Run SwarmDF
    gui.button_runSwarmDF = customtkinter.CTkButton(gui.left_sidebar, command=gui.run_swarmdf, text='Run SwarmDF', width=160, height=80, font=("Arial", 18))
    gui.button_runSwarmDF.grid(row=7, column=0, padx=20, pady=(100,10))

    # Demo mode
    gui.switch_demo = customtkinter.CTkSwitch(master=gui.left_sidebar, text=f"Demo mode", command=lambda: load_example_date(gui)) 
    gui.switch_demo.grid(row=8, column=0, padx=20, pady=(10,100))
    CustomTooltip(gui.switch_demo, "Use sample datasets for example event and skip data downloading")

    # Apparence mode
    gui.label_appearance = customtkinter.CTkLabel(gui.left_sidebar, text="Appearance Mode:", anchor="w")
    gui.label_appearance.grid(row=10, column=0, padx=20, pady=(10, 0))
    gui.optmenu_appearance = customtkinter.CTkOptionMenu(gui.left_sidebar, values=["Light", "Dark", "System"], command=change_appearance_mode)
    gui.optmenu_appearance.grid(row=11, column=0, padx=20, pady=(10, 10))
    gui.optmenu_appearance.set("Dark")

    # Scaling option
    gui.label_scaling = customtkinter.CTkLabel(gui.left_sidebar, text="UI Scaling:", anchor="w")
    gui.label_scaling.grid(row=12, column=0, padx=20, pady=(10, 0))
    gui.optmenu_scaling = customtkinter.CTkOptionMenu(gui.left_sidebar,  values=["80%", "90%", "100%", "110%", "120%"], command=change_scaling)
    gui.optmenu_scaling.grid(row=13, column=0, padx=20, pady=(10, 20))
    gui.optmenu_scaling.set("100%")


def change_appearance_mode(new_appearance_mode: str):
    customtkinter.set_appearance_mode(new_appearance_mode)

def change_scaling(new_scaling: str):
    new_scaling_float = int(new_scaling.replace("%", "")) / 100
    customtkinter.set_widget_scaling(new_scaling_float)
