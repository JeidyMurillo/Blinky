"""Tarjeta compacta de métrica (parpadeos, temperatura, luz, tiempo).

Qué va aquí:
- Icono, título, valor grande y unidad.
- Método update(value) sin reconstruir el widget.
"""

import customtkinter as ctk

from fatiga_visual.ui.theme import BG, TEXT_STRONG, icon_image, label


class MetricCard(ctk.CTkFrame):
    def __init__(self, master, title, icon, value, unit="", accent="#7d6bf0"):
        super().__init__(master, fg_color=BG, corner_radius=0)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text="", image=icon_image(icon, 15, "#858d9c", 1.7)).pack(side="left")
        label(top, title, 9, "#9ba1af", bg=BG).pack(side="left", padx=(6, 0))
        self.value_label = label(self, value, 20, TEXT_STRONG, True, bg=BG)
        self.value_label.pack(anchor="w", pady=(6, 0))
        self.unit_label = label(self, unit, 9, "#8b93a2", bg=BG)
        self.unit_label.pack(anchor="w", pady=(1, 0))
        self.accent = accent

    def update_value(self, value, unit=None):
        self.value_label.configure(text=value)
        if unit is not None:
            self.unit_label.configure(text=unit)
