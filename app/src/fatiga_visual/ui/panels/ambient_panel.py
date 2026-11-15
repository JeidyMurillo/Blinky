"""Tarjeta del sensor ambiental (ESP32).

Qué va aquí:
- Mostrar temperatura, iluminación y humedad recibidas por MQTT.
- Indicar si la última lectura está conectada o desactualizada.

Uso en Estadísticas y Recomendaciones para contexto del entorno.
"""

import customtkinter as ctk

from fatiga_visual.ui.theme import (
    MUTED_SOFT,
    TEXT_STRONG,
    card_frame,
    icon_image,
    label,
)


class AmbientPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        card = card_frame(self)
        card.pack(fill="x")

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=17, pady=(17, 0))
        titles = ctk.CTkFrame(top, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "Entorno de trabajo", 14, TEXT_STRONG, True).pack(anchor="w")
        label(titles, "Lecturas del sensor ambiental", 10, MUTED_SOFT).pack(anchor="w", pady=(3, 0))
        self.status = label(top, "Conectado", 9, "#39a977", True)
        self.status.pack(side="right", anchor="n", pady=(2, 0))

        values = ctk.CTkFrame(card, fg_color="transparent")
        values.pack(fill="x", padx=17, pady=(14, 17))
        for column in range(3):
            values.grid_columnconfigure(column, weight=1, uniform="ambient")

        self.temperature = self._item(values, 0, "thermo", "#dd8141", "#fff0e4", "TEMPERATURA", "23.4", "C")
        self.lux = self._item(values, 1, "sun", "#cb9821", "#fff7d9", "ILUMINACION", "420", "lux")
        self.humidity = self._item(values, 2, "eye", "#4786d4", "#e9f3ff", "HUMEDAD", "48", "%")

    def _item(self, parent, column, icon, icon_color, icon_bg, title, value, unit):
        box = ctk.CTkFrame(parent, fg_color="#fafbfc", corner_radius=10, border_width=1, border_color="#eceef4")
        box.grid(row=0, column=column, sticky="nsew", padx=(0, 5) if column < 2 else (0, 0))
        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=12)
        ctk.CTkLabel(inner, text="", image=icon_image(icon, 15, icon_color, 1.7), fg_color="#fafbfc").pack(anchor="w")
        label(inner, title, 8, "#9ba2b3").pack(anchor="w", pady=(6, 0))
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(anchor="w")
        value_label = label(row, value, 18, TEXT_STRONG, True)
        value_label.pack(side="left")
        label(row, unit, 9, TEXT_STRONG).pack(side="left", padx=(3, 0), pady=(4, 0))
        return value_label

    def refresh(self, ambient):
        if ambient is None:
            return
        self.temperature.configure(text=f"{ambient.temperature_c:.1f}")
        self.lux.configure(text=f"{ambient.lux:.0f}")
        self.humidity.configure(text=f"{ambient.humidity:.0f}")
        if getattr(ambient, "connected", False):
            self.status.configure(text="Conectado", fg="#39a977")
        else:
            self.status.configure(text="Sin datos", fg="#c96e5b")
