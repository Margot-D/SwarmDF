from PIL import Image, ImageDraw, ImageFont
from tkinter import messagebox

def validate_entry(entry, name, default=None, min_val=None, max_val=None):
    """
    Read and validate a float value from an entry widget.
    
    Parameters
    ----------
    entry : Tkinter Entry
        The entry widget to read from.
    name : str
        Name of the parameter (used in error messages)
    default : float, optional
        Value to use if parsing fails
    min_val, max_val : float, optional
        Optional bounds to check. Can also be callables returning floats.
    """

    # Evaluate dynamic bounds if needed
    try:
        if callable(min_val):
            min_val = min_val()

        if callable(max_val):
            max_val = max_val()

    except (ValueError, TypeError):
        min_val = None
        max_val = None

    # Read entry value
    try:
        value = float(entry.get())

    except ValueError:
        value = default
        messagebox.showwarning("Invalid input", f"{name} is invalid. Using default value: {default}")

    if min_val is not None and value < min_val:
        messagebox.showwarning("Invalid input", f"{name} must be ≥ {min_val}. Using default: {default}")
        value = default

    if max_val is not None and value > max_val:
        messagebox.showwarning("Invalid input", f"{name} must be ≤ {max_val}. Using default: {default}")
        value = default

    # Reflect corrected value in UI
    if default is not None and value == default:
        entry.delete(0, "end")
        entry.insert(0, str(default))

    return # wrong if value is returned!


def make_error_frame(width, height, text="An error occurred..."):
    """Error placeholder"""

    img = Image.new("RGBA", (width, height), (150, 0, 0, 80))
    draw = ImageDraw.Draw(img)

    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # w, h = draw.textbbox((0,0), text, font=font)[2:] 

    draw.text(((width - w) // 2, (height - h) // 2), text, fill=(255, 255, 255, 255), font=font)

    return img


def resize_keep_aspect(img, max_w, max_h):
    """Resize image to fit within (max_w, max_h) while preserving aspect ratio."""

    orig_w, orig_h = img.size
    scale = min(max_w / orig_w, max_h / orig_h)

    new_size = (int(orig_w * scale), int(orig_h * scale))

    return img.resize(new_size, Image.Resampling.LANCZOS)