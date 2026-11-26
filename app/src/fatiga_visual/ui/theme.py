"""Tema visual compartido de la aplicación.

Qué va aquí:
- Tokens de diseño (colores, tamaños, tipografías) usados por las 3 interfaces.
- Ajuste de DPI para que la ventana use píxeles físicos en Windows.
- Helpers de UI: etiquetas tkinter, tarjetas CTk, iconos dibujados con PIL.

No debe contener lógica de negocio, cámara, MQTT ni reglas.
"""

import math
import tkinter as tk

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont

ctk.set_appearance_mode("light")


def native_dpi_scaling():
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return ctypes.windll.user32.GetDpiForSystem() / 96
    except Exception:
        return 1.0


DPI_SCALING = native_dpi_scaling()
ctk.set_widget_scaling(1.0 / DPI_SCALING)
ctk.set_window_scaling(1.0 / DPI_SCALING)

FONT = "Segoe UI"
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_REGULAR = "C:/Windows/Fonts/segoeui.ttf"

BG = "#f6f8fc"
CARD = "#ffffff"
BORDER = "#e5e9f1"
TEXT = "#17233c"
TEXT_STRONG = "#222d48"
MUTED = "#7b8498"
MUTED_SOFT = "#969db0"
PURPLE = "#6559de"
PURPLE_DARK = "#5549ca"
PURPLE_SOFT = "#eeecff"
GREEN = "#35b77f"
GREEN_TEXT = "#27845e"
GREEN_SOFT = "#e9f7f0"
AMBER = "#e7a83d"
AMBER_TEXT = "#9c6d21"
AMBER_SOFT = "#fff5df"
ALERT_BG = "#fff9f6"
ALERT_BORDER = "#f0cfc8"
SALMON = "#c96e5b"
SALMON_DARK = "#b85f4d"
BLUE = "#4786d4"

WINDOW_W = 1512
WINDOW_H = 1000
PAD = 56
GAP = 20
LEFT_W = round((WINDOW_W - PAD * 2 - GAP) * 158 / 238)
FEED_W = LEFT_W - 36
FEED_H = 360

# Las medidas del diseño Figma están en píxeles CSS; mantener 1:1 evita que
# el contenido de Monitoreo se salga de la ventana fija de 1512x1000.
UI_SCALE = 1.25

PIL_FONT_CACHE = {}
ICON_CACHE = {}


def sp(px):
    return max(1, int(round(px * UI_SCALE)))


def fnt(px, bold=False):
    return (FONT, -sp(px), "bold" if bold else "normal")


def pil_font(px, bold=False):
    size = sp(px)
    key = (size, bold)
    if key not in PIL_FONT_CACHE:
        try:
            PIL_FONT_CACHE[key] = ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)
        except OSError:
            PIL_FONT_CACHE[key] = ImageFont.load_default()
    return PIL_FONT_CACHE[key]


def render_icon(name, px, color, stroke=1.8):
    scale = 4
    size = max(8, int(px * scale))
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    u = size / 24
    width = max(1, int(round(stroke * u)))

    def line(points, fill=color, w=width):
        draw.line([(x * u, y * u) for x, y in points], fill=fill, width=w, joint="curve")

    def ellipse(box, outline=color, w=width):
        draw.ellipse([box[0] * u, box[1] * u, box[2] * u, box[3] * u], outline=outline, width=w)

    def rrect(box, radius, outline=color, w=width):
        draw.rounded_rectangle(
            [box[0] * u, box[1] * u, box[2] * u, box[3] * u],
            radius=radius * u,
            outline=outline,
            width=w,
        )

    if name == "eye":
        cx, cy = 12, 12
        ew, eh = 19, 11.2
        top = [(cx - ew / 2 + ew * i / 32, cy - eh / 2 * math.sin(math.pi * i / 32)) for i in range(33)]
        bottom = [(cx - ew / 2 + ew * i / 32, cy + eh / 2 * math.sin(math.pi * i / 32)) for i in range(33)]
        line(top + list(reversed(bottom)) + [top[0]])
        ellipse([cx - 2.7, cy - 2.7, cx + 2.7, cy + 2.7])
    elif name == "eye_closed":
        line([(3.5, 13.5), (5.5, 12.2), (8, 11.1), (10, 10.5), (12, 10.3), (14, 10.5), (16, 11.1), (18.5, 12.2), (20.5, 13.5)])
        line([(8.5, 11.2), (7.5, 9.2)])
        line([(15.5, 11.2), (16.5, 9.2)])
    elif name == "camera":
        rrect([2, 7, 22, 21], 2.2)
        rrect([7.5, 4.4, 16.5, 8], 1.2)
        ellipse([8.6, 10.8, 15.4, 17.6])
    elif name == "sun":
        ellipse([8.6, 8.6, 15.4, 15.4])
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            line(
                [
                    (12 + 6.2 * math.cos(rad), 12 + 6.2 * math.sin(rad)),
                    (12 + 8.8 * math.cos(rad), 12 + 8.8 * math.sin(rad)),
                ]
            )
    elif name == "thermo":
        rrect([9.3, 2.8, 14.7, 16], 2.7)
        ellipse([8.5, 14.2, 15.5, 21.2])
        line([(12, 7.2), (12, 16)])
    elif name == "droplet":
        line(
            [(12, 3), (8.4, 8.2), (6.3, 11.2), (6.3, 14.4), (8.2, 18),
             (12, 20.6), (15.8, 18), (17.7, 14.4), (17.7, 11.2),
             (15.6, 8.2), (12, 3)]
        )
        line([(9.2, 15.3), (9.2, 16.8), (10.4, 18.2)])
    elif name == "gauge":
        line([(4.2, 17.8), (5.6, 13.5), (8.8, 9.2), (12, 7.6),
              (15.2, 9.2), (18.4, 13.5), (19.8, 17.8)])
        line([(12, 7.6), (12, 14.2), (16.4, 16.4)])
        ellipse([10.6, 12.8, 13.4, 15.6])
    elif name == "clock":
        ellipse([3, 3, 21, 21])
        line([(12, 7), (12, 12), (15.5, 14)])
    elif name == "chart":
        line([(5, 19), (5, 10.5)])
        line([(10, 19), (10, 5.5)])
        line([(15, 19), (15, 12)])
        line([(20, 19), (20, 8)])
        line([(2.5, 19.5), (21.5, 19.5)])
    elif name == "pause":
        line([(9, 5.5), (9, 18.5)], w=width + 1)
        line([(15, 5.5), (15, 18.5)], w=width + 1)
    elif name == "play":
        line([(9, 5.5), (18.5, 12), (9, 18.5), (9, 5.5)])
    elif name == "arrow":
        line([(14.5, 5.5), (8.5, 12), (14.5, 18.5)])
    elif name == "check":
        line([(4.5, 12.5), (9.5, 17.5), (19.5, 6.5)])
    elif name == "close":
        line([(6.5, 6.5), (17.5, 17.5)])
        line([(17.5, 6.5), (6.5, 17.5)])
    elif name == "minimize":
        line([(5, 12), (19, 12)], w=width + 1)
    elif name == "chevron_right":
        line([(9.5, 5.5), (15.5, 12), (9.5, 18.5)])

    img = img.resize((max(8, int(px)), max(8, int(px))), Image.LANCZOS)
    return img


def icon_image(name, px, color, stroke=1.8):
    size = sp(px)
    key = (name, size, color, stroke)
    if key not in ICON_CACHE:
        img = render_icon(name, size, color, stroke)
        ICON_CACHE[key] = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
    return ICON_CACHE[key]


def label(parent, text, px, color, bold=False, bg=CARD, anchor="w", wrap=0, justify="left"):
    widget = tk.Label(
        parent,
        text=text,
        font=fnt(px, bold),
        fg=color,
        bg=bg,
        anchor=anchor,
        justify=justify,
        bd=0,
        padx=0,
        pady=0,
        highlightthickness=0,
    )
    if wrap:
        widget.configure(wraplength=wrap)
    return widget


def card_frame(parent, radius=14, bg=CARD, border=BORDER):
    return ctk.CTkFrame(parent, fg_color=bg, corner_radius=radius, border_width=1, border_color=border)


def bind_tree(widget, sequence, handler, skip_buttons=True):
    if not (skip_buttons and isinstance(widget, ctk.CTkButton)):
        widget.bind(sequence, handler)
    for child in widget.winfo_children():
        bind_tree(child, sequence, handler, skip_buttons)


def get_work_area():
    try:
        import ctypes
        from ctypes import wintypes

        rect = wintypes.RECT()
        ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
        return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        return 0, 0, 1536, 864


def format_clock(total_seconds):
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
