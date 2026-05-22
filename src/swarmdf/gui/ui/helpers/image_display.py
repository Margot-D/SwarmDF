import customtkinter
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

"""
Image utilities for GUI display and visualization.
"""

####################
####################
# # Image adaptation to GUI 

def resize_keep_aspect(img, max_w, max_h):
    """Resize image to fit within bounds while preserving aspect ratio"""

    orig_w, orig_h = img.size
    scale = min(max_w / orig_w, max_h / orig_h)

    new_size = (int(orig_w * scale), int(orig_h * scale))

    return img.resize(new_size, Image.Resampling.LANCZOS)


def pil_to_ctk_images(frames_pil, widget, margin=40):
    """Convert a list of PIL images into CustomTkinter images sized for a widget"""

    widget.update_idletasks()
    w = max(widget.winfo_width() - margin, 1)
    h = max(widget.winfo_height(), 1)

    ctk_frames = []
    for f in frames_pil:
        resized = resize_keep_aspect(f, w, h)
        ctk_frames.append(customtkinter.CTkImage(light_image=resized, size=resized.size))

    return ctk_frames


def make_error_frame(widget, margin=40):
    """Create a simple placeholder image used when rendering fails"""

    widget.update_idletasks()
    w = max(widget.winfo_width() - margin, 1)
    h = max(widget.winfo_height(), 1)

    img = Image.new("RGBA", (w, h), (150, 0, 0, 80))

    return customtkinter.CTkImage(light_image=img, size=(w, h))

####################
####################
# # Visualization helpers

def open_interactive_window(frames_pil, title="Frames", figsize=(12, 9)):
    """Open a matplotlib viewer for browsing image frames with keyboard navigation"""

    plt.switch_backend("TkAgg")

    frames = [np.array(f) for f in frames_pil]

    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")
    ax.set_title(f"{title} — Frame 1 / {len(frames)}", fontsize=15, color="gray", pad=10)
    ax.text(0.5, 1.0001, "< use keyboard navigation >", transform=ax.transAxes, ha="center", fontsize=9, color="gray")

    im = ax.imshow(frames[0])
    state = {"i": 0}

    def update():
        im.set_data(frames[state["i"]])
        ax.set_title(f"{title} — Frame {state['i']+1} / {len(frames)}", fontsize=15, color="gray", pad=10)
        fig.canvas.draw_idle()

    def on_key(event):

        if event.key == "right":
            state["i"] = (state["i"] + 1) % len(frames)
            update()

        elif event.key == "left":
            state["i"] = (state["i"] - 1) % len(frames)
            update()

        elif event.key == " ":
            state["i"] = (state["i"] + 1) % len(frames)
            update()

    fig.canvas.mpl_connect("key_press_event", on_key)

    plt.tight_layout()
    plt.show()


def combine_validation_frames(frames_left, frames_right):
    """Combine Gamera and LompeOSSE PIL frames side-by-side for visualization in matplotlib viewer"""

    combined = []

    for left, right in zip(frames_left, frames_right):

        h = max(left.height, right.height)
        total_width = left.width + right.width

        canvas = Image.new("RGB", (total_width, h), "white")

        canvas.paste(left, (0, 0))
        canvas.paste(right, (left.width, 0))

        combined.append(canvas)

    return combined