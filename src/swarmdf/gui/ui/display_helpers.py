import customtkinter
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

def compute_widget_size(widget, margin=40):
    widget.update_idletasks()
    w = max(widget.winfo_width() - margin, 1)
    h = max(widget.winfo_height(), 1)
    return w, h


def pil_to_ctk_images(frames_pil, resize_fn, w, h):
    return [customtkinter.CTkImage(light_image=resize_fn(f, w, h), size=resize_fn(f, w, h).size) for f in frames_pil]


def open_interactive_window(frames_pil, title="Frames", figsize=(12, 9)):

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

    combined = []

    for left, right in zip(frames_left, frames_right):

        # Match heights if needed
        h = max(left.height, right.height)

        total_width = left.width + right.width

        canvas = Image.new("RGB", (total_width, h), "white")

        canvas.paste(left, (0, 0))
        canvas.paste(right, (left.width, 0))

        combined.append(canvas)

    return combined