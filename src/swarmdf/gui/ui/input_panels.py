import customtkinter
from tkinter import messagebox
from tkcalendar import Calendar
from ui.helpers.tooltip import CustomTooltip
import webbrowser
from datetime import datetime, date

def build_input_panels(gui):
        
    #############
    # Top row
    #############

    col1_width = 150 #65

    gui.tabview = customtkinter.CTkTabview(gui, corner_radius=10) #, width=col1_width
    gui.tabview.grid(row=0, column=1, padx=(20, 0), pady=(3, 0), sticky="nsew")
    tab1 = "Main input"
    tab2 = "Datasets"
    tab3 = "Conductances"
    gui.tabview.add(tab1)
    gui.tabview.add(tab2)
    gui.tabview.add(tab3)
    gui.tabview.tab(tab1).grid_columnconfigure(0, weight=1)
    gui.tabview.tab(tab2).grid_columnconfigure((0,1), weight=2)
    gui.tabview.tab(tab3).grid_columnconfigure(0, weight=2)
    gui.tabview.configure(height=500)
    # gui.tabview.grid_propagate(False)

    #######
    # TAB 1 - Main input
    
    # Satellite ID
    gui.optmenu_satellite = customtkinter.CTkOptionMenu(gui.tabview.tab(tab1), dynamic_resizing=False,
                                                            values=["Swarm A", "Swarm B", "Swarm C"])
    gui.optmenu_satellite.grid(row=0, column=0, padx=(10,10), pady=(30, 10))
    gui.optmenu_satellite.set("Satellite ID")

    # Start time entry
    gui.entry_start_time = DateTimeEntry(gui.tabview.tab(tab1), label="Start time:      ⓘ")
    gui.entry_start_time.grid(row=1, column=0, padx=20, pady=20, sticky="w")

    # End time
    gui.entry_end_time = DateTimeEntry(gui.tabview.tab(tab1), label="End time:        ⓘ")
    gui.entry_end_time.grid(row=2, column=0, padx=20, pady=10, sticky="w")
    gui.entry_end_time.link_datetime_entries(gui.entry_start_time, gui.entry_end_time)

    # Time step
    gui.label_timestep = customtkinter.CTkLabel(gui.tabview.tab(tab1), text="Time steps:   ⓘ")
    gui.label_timestep.grid(row=3, column=0, padx=20, pady=40, sticky="w")
    gui.entry_timestep = customtkinter.CTkEntry(gui.tabview.tab(tab1), width=50)
    gui.entry_timestep.grid(row=3, column=0, pady=20)        
    gui.entry_timestep.insert(0, 30) # default: 30 s
    CustomTooltip(gui.label_timestep, "Time between frames. \n Use the dropdown to select seconds, minutes, or hours. \n Min value: 10 sec")

    gui.timestep_unit_var = customtkinter.StringVar(value="s")
    gui.timestep_unit_menu = customtkinter.CTkOptionMenu(gui.tabview.tab(tab1), values=["s", "min", "h"], variable=gui.timestep_unit_var, width=60, button_color="#A0A0A0", fg_color="#A0A0A0")
    gui.timestep_unit_menu.grid(row=3, column=0, padx=(180,30), pady=20)

    # "Set example date" button         
    customtkinter.CTkButton(gui.tabview.tab(tab1),
                            text="Use example event",
                            command=lambda: load_example_date(gui),
                            width=40,
                            height=8,
                            fg_color="#888888",      # medium grey background
                            hover_color="#AAAAAA",   # slightly lighter on hover
                            font=customtkinter.CTkFont(size=13)).grid(row=5, column=0, pady=(25, 10))

    # "Reset date to placeholders" button
    customtkinter.CTkButton(gui.tabview.tab(tab1),
                            text="Reset to placeholders",
                            command=lambda: reset_dates(gui), 
                            width=40,
                            height=8,
                            fg_color="#888888",      # medium grey background
                            hover_color="#AAAAAA",   # slightly lighter on hover
                            font=customtkinter.CTkFont(size=13)).grid(row=6, column=0, pady=(0, 15))

    # Link to Swarm aurora website
    gui.link_find_conjunction = customtkinter.CTkLabel(gui.tabview.tab(tab1), text="Find conjunction with Swarm-Aurora", text_color="green", cursor="hand2")
    gui.link_find_conjunction.grid(row=7, column=0, padx=35, pady=(5, 0), sticky='n') #pady=(25, 5)
    gui.link_find_conjunction.bind("<Button-1>", lambda e: webbrowser.open("https://swarm-aurora.com/"))

    #######
    # TAB 2 - Datasets 

    # TODO get the correct electric field data (ask Spencer), this is along-track track, meaning i need a los component (which should simply be the direction of the satellite). kalle said this should be available on viresclient. 

    gui.checkbox_swarm_bfield = customtkinter.CTkCheckBox(master=gui.tabview.tab(tab2), text='Swarm mag')
    gui.checkbox_swarm_bfield.grid(row=3, column=0, pady=(60, 20), padx=10, sticky="n")
    CustomTooltip(gui.checkbox_swarm_bfield, "Space magnetic field")

    gui.checkbox_swarm_conv = customtkinter.CTkCheckBox(master=gui.tabview.tab(tab2), text='Swarm ion flow')
    gui.checkbox_swarm_conv.grid(row=3, column=1, pady=(60, 20), padx=10, sticky="n")
    CustomTooltip(gui.checkbox_swarm_conv, "Cross-track ion drift")

    # gui.checkbox_swarm_efield = customtkinter.CTkCheckBox(master=gui.tabview.tab(tab2), text='Swarm elec')
    # gui.checkbox_swarm_efield.grid(row=4, column=0, pady=(20, 20), padx=10, sticky="n")
    # CustomTooltip(gui.checkbox_swarm_efield, "...")

    gui.checkbox_supermag = customtkinter.CTkCheckBox(master=gui.tabview.tab(tab2), text='SuperMAG')
    gui.checkbox_supermag.grid(row=4, column=1, pady=(20, 20), padx=10, sticky="n")
    CustomTooltip(gui.checkbox_supermag, "Ground magnetometer")

    gui.checkbox_superdarn = customtkinter.CTkCheckBox(master=gui.tabview.tab(tab2), text='SuperDARN')
    gui.checkbox_superdarn.grid(row=4, column=0, pady=(20, 20), padx=10, sticky="n")
    CustomTooltip(gui.checkbox_superdarn, "Convection velocities")

    gui.checkbox_iridium_ampere = customtkinter.CTkCheckBox(master=gui.tabview.tab(tab2), text='Iridium/AMPERE')
    gui.checkbox_iridium_ampere.grid(row=6, column=0, pady=(20, 20), padx=10, sticky="n")
    CustomTooltip(gui.checkbox_iridium_ampere, "Space magnetic perturbations")

    gui.checkbox_dmsp_ssies17 = customtkinter.CTkCheckBox(master=gui.tabview.tab(tab2), text='DMSP/SSIES 17')
    gui.checkbox_dmsp_ssies17.grid(row=5, column=0, pady=(20, 20), padx=10, sticky="n")
    CustomTooltip(gui.checkbox_dmsp_ssies17, "Ion drift")

    gui.checkbox_dmsp_ssies18 = customtkinter.CTkCheckBox(master=gui.tabview.tab(tab2), text='DMSP/SSIES 18')
    gui.checkbox_dmsp_ssies18.grid(row=5, column=1, pady=(20, 20), padx=10, sticky="n")
    CustomTooltip(gui.checkbox_dmsp_ssies18, "Ion drift")

    # gui.entry_data = customtkinter.CTkEntry(gui.tabview.tab(tab2), placeholder_text="myfile.cdf") # TODO remove if not fixed
    # gui.entry_data.grid(row=5, column=1, columnspan=1, pady=(20, 20), padx=10, sticky="n")

    # Default: select all datasets
    # gui.checkbox_swarm_efield.select()
    gui.checkbox_swarm_bfield.select()
    # gui.checkbox_swarm_conv.select()
    gui.checkbox_supermag.select()
    gui.checkbox_superdarn.select()
    gui.checkbox_iridium_ampere.select()
    gui.checkbox_dmsp_ssies17.select()
    gui.checkbox_dmsp_ssies18.select()
    
    # Link to data documentation TODO fix link!
    gui.link_data_docu = customtkinter.CTkLabel(gui.tabview.tab(tab2), text="Data documentation", text_color="green", cursor="hand2")
    gui.link_data_docu.grid(row=9, column=0, columnspan=2, padx=35, pady=(25, 0), sticky='nsew') #pady=(25, 5)
    gui.link_data_docu.bind("<Button-1>", lambda e: webbrowser.open(""))

    #######
    # TAB 3 - Conductance method

    gui.label_conductance_optmenu = customtkinter.CTkLabel(gui.tabview.tab(tab3), text="Conductance estimates:", wraplength=150)
    gui.label_conductance_optmenu.grid(row=1, column=0, columnspan=3, padx=10, pady=(30, 5), sticky="n")
    CustomTooltip(gui.label_conductance_optmenu, "Estimates of ionospheric conductances are a key input to the Lompe inversion. \n Select the model representing the auroral precipitation contribution.")
    
    gui.optmenu_conductance = customtkinter.CTkOptionMenu(gui.tabview.tab(tab3), dynamic_resizing=True,
                                                    values=["Hardy model", "Zhang & Paxton model"])
    gui.optmenu_conductance.grid(row=2, column=0, columnspan=3, padx=10, pady=(5, 20))
    gui.optmenu_conductance.set("Zhang & Paxton model")

    for i in range(3):
        gui.tabview.tab(tab3).grid_columnconfigure(i, weight=1) # Make columns expand nicely

    # Kp index (useful for Hardy model)
    gui.label_kp = customtkinter.CTkLabel(gui.tabview.tab(tab3), text="Kp:")
    gui.label_kp.grid(row=6, column=0, padx=(25, 5), pady=(20, 5), sticky="n")
    gui.entry_kp = customtkinter.CTkEntry(gui.tabview.tab(tab3), width=60)
    gui.entry_kp.grid(row=7, column=0, padx=(25, 5), pady=(0, 20), sticky="n")
    gui.entry_kp.insert(0, 4)
    CustomTooltip(gui.entry_kp, "Indicator of disturbances in the Earth's magnetic field")

    # F10.7 solar flux (useful for EUV conductance)
    gui.label_f107 = customtkinter.CTkLabel(gui.tabview.tab(tab3), text="F10.7 (s.f.u):")
    gui.label_f107.grid(row=6, column=1, padx=(25, 5), pady=(20, 5), sticky="n")
    gui.entry_f107 = customtkinter.CTkEntry(gui.tabview.tab(tab3), width=60)
    gui.entry_f107.grid(row=7, column=1, padx=(25, 5), pady=(0, 20), sticky="n")
    gui.entry_f107.insert(0, 100)
    CustomTooltip(gui.entry_f107, "Solar radio flux at 10.7 cm (solar activity indicator)")

    # Background/starlight (useful for EUV conductance)
    gui.label_background = customtkinter.CTkLabel(gui.tabview.tab(tab3), text="Background:") # add info/explnanation for all these parameters
    gui.label_background.grid(row=6, column=2, padx=(25, 5), pady=(20, 5), sticky="n")
    gui.entry_background = customtkinter.CTkEntry(gui.tabview.tab(tab3), width=60)
    gui.entry_background.grid(row=7, column=2, padx=(25, 5), pady=(0, 20), sticky="n")
    gui.entry_background.insert(0, 2)
    CustomTooltip(gui.entry_background, "Background conductance - somthg about starlight? fix")

    #############
    # Bottom row (grid parameters)
    #############

    gui.frame_gridparam = customtkinter.CTkFrame(gui, corner_radius=10) #, width=col1_width
    gui.frame_gridparam.grid(row=1, column=1, padx=(20, 0), pady=(10, 20), sticky="nsew")
    gui.frame_gridparam.grid_columnconfigure((0,1), weight=1)
    # gui.frame_gridparam.grid_propagate(False)

    gui.label_grid_param = customtkinter.CTkLabel(gui.frame_gridparam, text="Grid parameters", font=customtkinter.CTkFont(size=14, weight="bold"))
    gui.label_grid_param.grid(row=0, column=0, columnspan=2, pady=(0, 10))

    gui.label_L = customtkinter.CTkLabel(gui.frame_gridparam, text="Along-track \n dimension (km):", anchor='center') # but in reality cross-track dimension of analysis grid
    gui.label_W = customtkinter.CTkLabel(gui.frame_gridparam, text="Cross-track \n dimension (km):", anchor='center') # along-track dimension of analysis grid
    gui.label_L.grid(row=2, column=0, padx=10, pady=10, sticky="n")
    gui.label_W.grid(row=2, column=1, padx=10, pady=10, sticky="n")

    gui.entry_L = customtkinter.CTkEntry(gui.frame_gridparam, width=70)
    gui.entry_W = customtkinter.CTkEntry(gui.frame_gridparam, width=70)
    gui.entry_L.grid(row=3, column=0, padx=10, pady=3)
    gui.entry_W.grid(row=3, column=1, padx=10, pady=3)

    gui.label_Lres = customtkinter.CTkLabel(gui.frame_gridparam, text="Along-track \n resolution (km):", anchor='center')
    gui.label_Wres = customtkinter.CTkLabel(gui.frame_gridparam, text="Cross-track \n resolution (km):", anchor='center')
    gui.label_Lres.grid(row=4, column=0, padx=10, pady=(30,10), sticky="n")
    gui.label_Wres.grid(row=4, column=1, padx=10, pady=(30,10), sticky="n")

    gui.entry_Lres = customtkinter.CTkEntry(gui.frame_gridparam, width=70)
    gui.entry_Wres = customtkinter.CTkEntry(gui.frame_gridparam, width=70)
    gui.entry_Lres.grid(row=5, column=0, padx=10, pady=3)
    gui.entry_Wres.grid(row=5, column=1, padx= 10, pady=3)

    gui.entry_L.insert(0, "2000")
    gui.entry_W.insert(0, "1500")
    gui.entry_Lres.insert(0, "200")
    gui.entry_Wres.insert(0, "200")

    # # mirror entries
    # gui.link_grid_entries(gui.entry_L, gui.entry_W)
    # gui.link_grid_entries(gui.entry_Lres, gui.entry_Wres)

    # shift the grid center wres km in cross-track direction
    gui.label_wshift = customtkinter.CTkLabel(gui.frame_gridparam, text="Shift center (km):", anchor='center')
    gui.label_wshift.grid(row=6, column=0, padx=(10,0), pady=30, sticky='e')
    gui.entry_wshift = customtkinter.CTkEntry(gui.frame_gridparam, width=55)
    gui.entry_wshift.grid(row=6, column=1, padx=(7,0), pady=15, sticky='w')
    gui.entry_wshift.insert(0, 0)
    CustomTooltip(gui.entry_wshift, "Shift the grid center horizontally (cross-track) to align the Swarm track \n (positive = left, negative = right)")


def load_example_date(gui):
    # example_start = datetime(2014, 12, 15, 1, 12, 0)
    # example_end   = datetime(2014, 12, 15, 1, 27, 0)
    example_start = datetime(2014, 12, 15, 1, 15, 0)
    example_end   = datetime(2014, 12, 15, 1, 16, 0) #TODO final version, change to 5 min? 
    gui.entry_start_time.set_datetime(example_start)
    gui.entry_end_time.set_datetime(example_end)

def reset_dates(gui):
    gui.entry_start_time.reset_to_placeholders()
    gui.entry_end_time.reset_to_placeholders()        

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
