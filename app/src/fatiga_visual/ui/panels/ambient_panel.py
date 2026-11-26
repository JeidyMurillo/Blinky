"""Tarjeta del sensor ambiental (ESP32).

Qué va aquí:
- Mostrar temperatura, iluminación y humedad recibidas por MQTT.
- Indicar si la última lectura está conectada o desactualizada.

Uso en Estadísticas y Recomendaciones para contexto del entorno.
"""

import customtkinter as ctk

from fatiga_visual.core.config import DEFAULTS
from fatiga_visual.ui.theme import (
    AMBER_TEXT,
    MUTED_SOFT,
    SALMON,
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
        """Sin lectura valida muestra 'Sin datos', nunca un valor viejo o falso."""
        if ambient is None or not getattr(ambient, "connected", False):
            self.temperature.configure(text="--")
            self.lux.configure(text="--")
            self.humidity.configure(text="--")
            self.status.configure(text="Sin datos", fg="#c96e5b")
            return
        self.temperature.configure(text=f"{ambient.temperature_c:.1f}")
        self.lux.configure(text=f"{ambient.lux:.0f}")
        self.humidity.configure(text=f"{ambient.humidity:.0f}")
        self.status.configure(text="Conectado", fg="#39a977")


class AmbientStrip(ctk.CTkFrame):
    """Franja sensor-strip bajo la cámara: temperatura, humedad e iluminación."""

    def __init__(self, master, settings=None):
        super().__init__(master, fg_color="#ffffff", corner_radius=0, height=88)
        self.settings = settings
        self.pack_propagate(False)
        self.grid_propagate(False)
        for column in range(3):
            self.grid_columnconfigure(column, weight=1)

        ctk.CTkFrame(self, fg_color="#edf0f5", height=1).place(
            relx=0, rely=0, relwidth=1
        )

        self.temperature, self.temperature_note = self._item(
            0, "thermo", "#dd8141", "#fff0e4", "TEMPERATURA", "°C"
        )
        self.humidity, self.humidity_note = self._item(
            1, "droplet", "#3b9d72", "#e7f7ef", "HUMEDAD", "%"
        )
        self.lux, self.lux_note = self._item(
            2, "sun", "#cb9821", "#fff7d9", "ILUMINACIÓN", "lux"
        )

    def _item(self, column, icon, icon_color, icon_bg, title, unit):
        item = ctk.CTkFrame(self, fg_color="#ffffff", height=88)
        item.grid(row=0, column=column, sticky="nsew")
        item.grid_propagate(False)
        if column:
            ctk.CTkFrame(item, fg_color="#edf0f5", width=1).place(
                relx=0, rely=0.2, relheight=0.6
            )

        inner = ctk.CTkFrame(item, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        tile = ctk.CTkFrame(inner, width=30, height=30, fg_color=icon_bg, corner_radius=8)
        tile.pack(side="left", padx=(0, 9))
        tile.pack_propagate(False)
        ctk.CTkLabel(
            tile, text="", image=icon_image(icon, 16, icon_color, 1.8), fg_color=icon_bg
        ).place(relx=0.5, rely=0.5, anchor="center")

        text = ctk.CTkFrame(inner, fg_color="transparent")
        text.pack(side="left")
        label(text, title, 7, "#9ba2b3").pack(anchor="w")
        value_row = ctk.CTkFrame(text, fg_color="transparent")
        value_row.pack(anchor="w", pady=(2, 0))
        value = label(value_row, "--", 15, TEXT_STRONG, True)
        value.pack(side="left")
        label(value_row, unit, 9, TEXT_STRONG).pack(side="left", padx=(2, 0), pady=(5, 0))
        note = label(text, "Sin datos", 7, "#c96e5b")
        note.pack(anchor="w", pady=(2, 0))
        return value, note

    def _threshold(self, name):
        defaults = DEFAULTS["thresholds"]
        if self.settings is None:
            return defaults[name], defaults[f"{name.split('_')[0]}_max"]
        return (
            self.settings.get(f"thresholds.{name}", defaults[name]),
            self.settings.get(
                f"thresholds.{name.split('_')[0]}_max", defaults[f"{name.split('_')[0]}_max"]
            ),
        )

    def refresh(self, ambient):
        """Muestra la última lectura; si el nodo está offline lo indica."""
        if ambient is None:
            for value, note in (
                (self.temperature, self.temperature_note),
                (self.humidity, self.humidity_note),
                (self.lux, self.lux_note),
            ):
                value.configure(text="--", fg=SALMON)
                note.configure(text="Sin datos", fg=SALMON)
            return

        connected = bool(getattr(ambient, "connected", False))
        offline_note = "Sin señal" if not connected else None
        offline_color = AMBER_TEXT if not connected else None
        value_color = MUTED_SOFT if not connected else TEXT_STRONG

        temp_min, temp_max = self._threshold("temperature_min")
        hum_min, hum_max = self._threshold("humidity_min")
        lux_min, lux_max = self._threshold("lux_min")
        temp_ok = temp_min <= ambient.temperature_c <= temp_max
        hum_ok = hum_min <= ambient.humidity <= hum_max
        lux_ok = lux_min <= ambient.lux <= lux_max

        self.temperature.configure(text=f"{ambient.temperature_c:.1f}", fg=value_color)
        self.temperature_note.configure(
            text=offline_note or ("Óptima" if temp_ok else "Fuera de rango"),
            fg=offline_color or ("#5eb68d" if temp_ok else "#dd8141"),
        )
        self.humidity.configure(text=f"{ambient.humidity:.0f}", fg=value_color)
        self.humidity_note.configure(
            text=offline_note or ("Confortable" if hum_ok else "Fuera de rango"),
            fg=offline_color or ("#5eb68d" if hum_ok else "#dd8141"),
        )
        self.lux.configure(text=f"{ambient.lux:.0f}", fg=value_color)
        self.lux_note.configure(
            text=offline_note or ("Adecuada" if lux_ok else "Fuera de rango"),
            fg=offline_color or ("#5eb68d" if lux_ok else "#dd8141"),
        )
