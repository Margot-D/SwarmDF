from PIL import Image, ImageTk, ImageDraw

class Icons:
    """
    Create play/pause and previous/next icons
    """
    def __init__(self, color="snow"):
        self.play = self._create_play_icon(25, color) #25
        self.pause = self._create_pause_icon(25, color)
        self.previous = self._create_previous_icon(15, color) #15
        self.next = self._create_next_icon(15, color)

    def _create_play_icon(self, size, color):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.polygon([(6, 5), (20, 12), (6, 19)], fill=color) # triangle
        return ImageTk.PhotoImage(img)

    def _create_pause_icon(self, size, color):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([5, 5, 10, 20], fill=color)   # left bar
        draw.rectangle([15, 5, 20, 20], fill=color)  # right bar
        return ImageTk.PhotoImage(img)
    
    def _create_previous_icon(self, size, color):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.polygon([(12, 3), (3, 7), (12, 12)], fill=color) # triangle pointing left
        return ImageTk.PhotoImage(img)

    def _create_next_icon(self, size, color):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.polygon([(3, 3), (12, 7), (3, 12)], fill=color) # triangle pointing right
        return ImageTk.PhotoImage(img)
