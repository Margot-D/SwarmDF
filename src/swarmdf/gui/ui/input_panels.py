import customtkinter
from tkinter import messagebox
from tkcalendar import Calendar
from swarmdf.gui.ui.helpers.tooltip import CustomTooltip
import webbrowser
from datetime import datetime, date

def build_input_panels(gui):
        
    #############
    # Top tabview

    gui.tabview = customtkinter.CTkTabview(gui, corner_radius=10)
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

    for i in range(3):
        gui.tabview.tab(tab3).grid_columnconfigure(i, weight=1) # Make columns expand nicely

    # TAB 1: Main input
    
    # Satellite ID
    gui.optmenu_satellite = customtkinter.CTkOptionMenu(gui.tabview.tab(tab1), dynamic_resizing=False, values=["Swarm A", "Swarm B", "Swarm C"])
    gui.optmenu_satellite.grid(row=0, column=0, padx=(10,10), pady=(30, 10))
    gui.optmenu_satellite.set("Satellite ID")

    # Start time
    gui.entry_start_time = DateTimeEntry(gui.tabview.tab(tab1), label="Start time:      ⓘ")
    gui.entry_start_time.grid(row=1, column=0, padx=20, pady=20, sticky="w")

    # End time
    gui.entry_end_time = DateTimeEntry(gui.tabview.tab(tab1), label="End time:        ⓘ")
    gui.entry_end_time.grid(row=2, column=0, padx=20, pady=10, sticky="w")

    # Link entries
    gui.entry_start_time.link_datetime_entries(gui.entry_end_time)

    # Time step
    gui.label_timestep = customtkinter.CTkLabel(gui.tabview.tab(tab1), text="Time steps:   ⓘ")
    gui.label_timestep.grid(row=3, column=0, padx=20, pady=40, sticky="w")
    gui.entry_timestep = customtkinter.CTkEntry(gui.tabview.tab(tab1), width=50)
    gui.entry_timestep.grid(row=3, column=0, pady=20)        
    gui.entry_timestep.insert(0, 30)
    CustomTooltip(gui.label_timestep, "Time between frames. \n Use the dropdown to select seconds, minutes, or hours. \n Min value: 10 sec")

    # Time step unit
    gui.var_timestep_unit = customtkinter.StringVar(value="s")
    gui.optmenu_timestep_unit = customtkinter.CTkOptionMenu(gui.tabview.tab(tab1), values=["s", "min", "h"], variable=gui.var_timestep_unit, width=60, button_color="#A0A0A0", fg_color="#A0A0A0")
    gui.optmenu_timestep_unit.grid(row=3, column=0, padx=(180,30), pady=20)

    # Set example date         
    customtkinter.CTkButton(gui.tabview.tab(tab1),
                            text="Use example event",
                            command=lambda: apply_example_date(gui),
                            width=40, height=8,
                            fg_color="#888888", hover_color="#AAAAAA",
                            font=customtkinter.CTkFont(size=13)).grid(row=5, column=0, pady=(25, 10))

    # Reset date to placeholders
    customtkinter.CTkButton(gui.tabview.tab(tab1),
                            text="Reset to placeholders",
                            command=lambda: reset_dates(gui), 
                            width=40, height=8,
                            fg_color="#888888", hover_color="#AAAAAA", 
                            font=customtkinter.CTkFont(size=13)).grid(row=6, column=0, pady=(0, 15))

    # Link to Swarm aurora website
    gui.link_find_conjunction = customtkinter.CTkLabel(gui.tabview.tab(tab1), text="Find conjunction with Swarm-Aurora", text_color="green", cursor="hand2")
    gui.link_find_conjunction.grid(row=7, column=0, padx=35, pady=(5, 0), sticky='n')
    gui.link_find_conjunction.bind("<Button-1>", lambda e: webbrowser.open("https://swarm-aurora.com/"))

    # TAB 2: Datasets 

    gui.checkbox_swarm_mag = customtkinter.CTkCheckBox(master=gui.tabview.tab(tab2), text='Swarm mag')
    gui.checkbox_swarm_mag.grid(row=3, column=0, pady=(60, 20), padx=10, sticky="n")
    CustomTooltip(gui.checkbox_swarm_mag, "Space magnetic field")

    gui.checkbox_swarm_efi = customtkinter.CTkCheckBox(master=gui.tabview.tab(tab2), text='Swarm ion flow')
    gui.checkbox_swarm_efi.grid(row=3, column=1, pady=(60, 20), padx=10, sticky="n")
    CustomTooltip(gui.checkbox_swarm_efi, "Cross-track ion drift")

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

    # gui.checkbox_swarm_efield.select()
    gui.checkbox_swarm_mag.select()
    gui.checkbox_swarm_efi.select()
    gui.checkbox_supermag.select()
    gui.checkbox_superdarn.select()
    gui.checkbox_iridium_ampere.select()
    gui.checkbox_dmsp_ssies17.select()
    gui.checkbox_dmsp_ssies18.select()
    
    # Link to data documentation TODO fix link!
    gui.link_data_docu = customtkinter.CTkLabel(gui.tabview.tab(tab2), text="Data documentation", text_color="green", cursor="hand2")
    gui.link_data_docu.grid(row=9, column=0, columnspan=2, padx=35, pady=(25, 0), sticky='nsew') #pady=(25, 5)
    gui.link_data_docu.bind("<Button-1>", lambda e: webbrowser.open(""))

    # TAB 3: Conductance method

    gui.label_conductance = customtkinter.CTkLabel(gui.tabview.tab(tab3), text="Conductance estimates:", wraplength=150)
    gui.label_conductance.grid(row=1, column=0, columnspan=3, padx=10, pady=(30, 5), sticky="n")    
    gui.optmenu_conductance = customtkinter.CTkOptionMenu(gui.tabview.tab(tab3), dynamic_resizing=True, values=["Hardy model", "Zhang & Paxton model"])
    gui.optmenu_conductance.grid(row=2, column=0, columnspan=3, padx=10, pady=(5, 20))
    gui.optmenu_conductance.set("Zhang & Paxton model")
    CustomTooltip(gui.label_conductance, "Estimates of ionospheric conductances are a key input to the Lompe inversion. \n Select the model representing the auroral precipitation contribution.")

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
    # Bottom panel - grid parameters

    gui.frame_gridparam = customtkinter.CTkFrame(gui, corner_radius=10)
    gui.frame_gridparam.grid(row=1, column=1, padx=(20, 0), pady=(10, 20), sticky="nsew")
    gui.frame_gridparam.grid_columnconfigure((0,1), weight=1)

    gui.label_gridparam = customtkinter.CTkLabel(gui.frame_gridparam, text="Grid parameters", font=customtkinter.CTkFont(size=14, weight="bold"))
    gui.label_gridparam.grid(row=0, column=0, columnspan=2, pady=(0, 10))

    gui.label_L = customtkinter.CTkLabel(gui.frame_gridparam, text="Along-track \n dimension (km):", anchor='center')
    gui.label_W = customtkinter.CTkLabel(gui.frame_gridparam, text="Cross-track \n dimension (km):", anchor='center')
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
    gui.entry_Lres.insert(0, "80")
    gui.entry_Wres.insert(0, "80")

    gui.label_wshift = customtkinter.CTkLabel(gui.frame_gridparam, text="Shift center (km):", anchor='center')
    gui.label_wshift.grid(row=6, column=0, padx=(10,0), pady=30, sticky='e')
    gui.entry_wshift = customtkinter.CTkEntry(gui.frame_gridparam, width=55)
    gui.entry_wshift.grid(row=6, column=1, padx=(7,0), pady=15, sticky='w')
    gui.entry_wshift.insert(0, 0)
    CustomTooltip(gui.entry_wshift, "Shift the grid center horizontally (cross-track) to align the Swarm track \n (positive = left, negative = right)")


def apply_example_date(gui):
    # example_start = datetime(2014, 12, 15, 1, 12, 0)
    # example_end   = datetime(2014, 12, 15, 1, 27, 0)
    example_start = datetime(2014, 12, 15, 1, 15, 0)
    example_end   = datetime(2014, 12, 15, 1, 16, 0) #TODO final version, change to 5 min interval? 
    gui.entry_start_time.set_datetime(example_start)
    gui.entry_end_time.set_datetime(example_end)

def reset_dates(gui):
    gui.entry_start_time.reset_to_placeholders()
    gui.entry_end_time.reset_to_placeholders()        

class DateTimeEntry(customtkinter.CTkFrame):
    """Custom datetime input widget"""

    def __init__(self, master, label):
        super().__init__(master)

        # -------- # 
        # Layout
        # -------- # 

        # Label
        lab = customtkinter.CTkLabel(self, text=label)
        lab.grid(row=0, column=0, columnspan=13, pady=(0, 5), sticky="w")
        CustomTooltip(lab, "User-defined time interval is used to define grid centers; \n actual data intervals are determined dynamically per grid.")

        # Placeholder setup
        self.placeholders = ["YYYY", "MM", "DD", "HH", "MIN", "SS"]
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

            # Separators between fields
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
        self.button_calendar = customtkinter.CTkButton(self, text="📅", width=20, command=self.open_calendar)
        self.button_calendar.grid(row=1, column=12, padx=(7, 0))
        CustomTooltip(self.button_calendar, "Pick the date from the calendar. Type YYYY to jump directly to that year.")

        # Force a stable grid layout inside DateTimeEntry
        for i in range(13): # 6 entries + 6 separators
            self.grid_columnconfigure(i, weight=0)


    def on_focus_in(self, event, placeholder):
        """Clear placeholder and select text when entry gains focus"""

        # Clear placeholder
        if event.widget.get() == placeholder:
            event.widget.delete(0, "end")

        # Select all text in entry
        event.widget.select_range(0, "end")
        event.widget.icursor("end")

    def on_focus_out(self, event, placeholder, index):
        """Restore placeholder and validate entry on focus loss"""

        # Put placeholder back if field left empty
        text = event.widget.get().strip()
        if text == "":
            event.widget.insert(0, placeholder)
            return 
        
        # Validate value
        ok = self.validate_datetime_field(text, placeholder, index)

        if not ok:
            # Replace invalid field by placeholder
            event.widget.delete(0, "end")
            event.widget.insert(0, placeholder)
            
            # Keep focus on invalid field so the user can correct it
            event.widget.focus_set()
            event.widget.icursor(0)

        # Automatic zero-padding (makes month/day/hour/min/sec two digits)
        if index > 0:  # skip year
            lengths = [4, 2, 2, 2, 2, 2]
            if text.isdigit() and len(text) < lengths[index]:
                text = text.zfill(lengths[index])
                event.widget.delete(0, "end")
                event.widget.insert(0, text)

    def validate_datetime_field(self, text, placeholder, index):
        """Validate a single datetime field"""

        # Must be numeric
        if not text.isdigit():
            messagebox.showerror("Invalid input", f"{placeholder} must be a number")
            return False

        datetime_rules = {"MM": (1, 12), "DD": (1, 31), "HH": (0, 23), "MIN": (0, 59), "SS": (0, 59)}
        
        value = int(text)
        key = self.placeholders[index]

        # skip year
        if key == "YYYY":
            return True

        # apply rules
        if key in datetime_rules:
            min_val, max_val = datetime_rules[key]

            if value < min_val or value > max_val:
                messagebox.showerror("Invalid input", f"{placeholder} must be between {min_val} and {max_val}")
                return False

        return True
            
    def auto_advance(self, event, index):
        """Move focus to the next field when the current entry is complete"""

        # Ignore navigation keys
        if event.keysym in ("Tab", "Left", "Right", "Up", "Down"):
            return

        # Move to next field
        lengths = [4, 2, 2, 2, 2, 2]
        if (event.widget.get().isdigit() and len(event.widget.get()) >= lengths[index] and index < len(self.entries) - 1):
            self.entries[index + 1].focus()

    def open_calendar(self):
        """Open a calendar popup and update the date fields from the selected date"""

        # Read current year/month/day entries if available
        y, m, d = None, None, None
        try:
            y = int(self.entries[0].get()) if self.entries[0].get().isdigit() else None
            m = int(self.entries[1].get()) if self.entries[1].get().isdigit() else 1
            d = int(self.entries[2].get()) if self.entries[2].get().isdigit() else 1
        except ValueError:
            pass

        # Fall back to today's date if year is missing
        if not y:
            today = date.today()
            y, m, d = today.year, today.month, today.day

        # Create popup window
        top = customtkinter.CTkToplevel(self)
        top.title("Select date")

        # Calendar widget
        cal = Calendar(top, selectmode="day", date_pattern="yyyy-mm-dd",
                       year=y, month=m, day=d, 
                       mindate=datetime(2013, 11, 25), maxdate=date.today(),
                       showothermonthdays=False,
                       headersforeground='darkgrey',
                       selectforeground='green',
                       normalforeground='white', 
                       weekendforeground='white',
                       disableddayforeground='grey')
        cal.pack(padx=10, pady=10)

        # Update entry fields from selected calendar date 

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

    # -------- # 
    # Helpers
    # -------- # 

    def get_datetime(self):
        """Return a datetime object built from the entry fields"""

        try:
            vals = [e.get() for e in self.entries]
            date_str = f"{vals[0]}-{vals[1]}-{vals[2]} {vals[3]}:{vals[4]}:{vals[5]}"
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        
        except Exception as e:
            return None
        
    def set_datetime(self, dt):
        """Fill all fields with a given datetime object"""
        
        vals = [str(dt.year), f"{dt.month:02d}", f"{dt.day:02d}",
                f"{dt.hour:02d}", f"{dt.minute:02d}", f"{dt.second:02d}"]
        
        for i, v in enumerate(vals):
            self.entries[i].delete(0, "end")
            self.entries[i].insert(0, v)

    def reset_to_placeholders(self):
        """Reset all fields to their default placeholders"""

        for entry, ph in zip(self.entries, self.placeholders):
            entry.delete(0, "end")
            entry.insert(0, ph)

    def link_datetime_entries(self, other):
        """Link start and end time entries"""

        self.other = other
        n = len(self.entries)

        for i, entry in enumerate(self.entries):

            # Mirror start datetime fields into end fields
            def mirror(idx):
                val = self.entries[idx].get()
                ph = self.placeholders[idx]

                if val != ph:
                    other.entries[idx].delete(0, "end")
                    other.entries[idx].insert(0, val)
                    other.entries[idx].configure(text_color="white")

            entry.bind("<KeyRelease>", lambda e, i=i: mirror(i) if e.keysym not in ("Left", "Right", "Up", "Down") else None)

            # Bind navigation between start and end time fields
            self.bind_navigation(other)
            other.bind_navigation(self)

    def bind_navigation(self, other):
        
        n = len(self.entries)
        for i, entry in enumerate(self.entries):

            def right(e, i=i):
                if i < n - 1:
                    self.entries[i + 1].focus_set()
                else:
                    other.entries[0].focus_set()
                return "break"

            def left(e, i=i):
                if i > 0:
                    self.entries[i - 1].focus_set()
                else:
                    other.entries[-1].focus_set()
                return "break"

            def down(e, i=i):
                other.entries[i].focus_set()
                return "break"

            def up(e, i=i):
                other.entries[i].focus_set()
                return "break"

            entry.bind("<Right>", right)
            entry.bind("<Left>", left)
            entry.bind("<Down>", down)
            entry.bind("<Up>", up)