
import customtkinter

# Small info box pops up when hovering widget 
class CustomTooltip:
    """
    """
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay  # delay in ms before showing
        self.tooltip_label = None
        self.after_id = None

        widget.bind("<Enter>", self.schedule_show)
        widget.bind("<Leave>", self.hide_tooltip)
        widget.bind("<Motion>", self.move_tooltip)

    def schedule_show(self, event=None):
        self.after_id = self.widget.after(self.delay, self.show_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_label is not None:
            return  # already showing

        root = self.widget.winfo_toplevel()  # top-level window

        self.tooltip_label = customtkinter.CTkLabel(root,  # parent is the top-level window
                                                    text=self.text,
                                                    fg_color="grey90", # background
                                                    text_color="black",
                                                    corner_radius=5,
                                                    font=customtkinter.CTkFont(size=11))

        self.place_tooltip()

    def place_tooltip(self):
        if self.tooltip_label is None:
            return

        # Get widget position relative to root window
        root = self.widget.winfo_toplevel()
        x = self.widget.winfo_rootx() - root.winfo_rootx() + 20
        y = self.widget.winfo_rooty() - root.winfo_rooty() + self.widget.winfo_height() + 5

        # Keep inside root bounds
        root_width = root.winfo_width()
        root_height = root.winfo_height()

        self.tooltip_label.update_idletasks()
        tip_width = self.tooltip_label.winfo_width()
        tip_height = self.tooltip_label.winfo_height()

        if x + tip_width > root_width:
            x = root_width - tip_width - 5
        if y + tip_height > root_height:
            y = root_height - tip_height - 5

        self.tooltip_label.place(x=x, y=y)

    def move_tooltip(self, event=None):
        if self.tooltip_label is not None:
            self.place_tooltip()

    def hide_tooltip(self, event=None):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        if self.tooltip_label:
            self.tooltip_label.destroy()
            self.tooltip_label = None

