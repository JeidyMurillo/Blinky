"""Panel derecho de Monitoreo: ojos, métricas de sesión y acceso a estadísticas.

Qué va aquí:
- Tarjeta de estado ocular (ojo izquierdo/derecho).
- Tarjetas de parpadeos, temperatura, iluminación y tiempo activo.
- Botón grande que navega a la vista de Estadísticas.

Se refresca con refresh(state) sin conocer la cámara ni MQTT.
"""

import customtkinter as ctk

from fatiga_visual.ui.theme import (
    BG,
    GREEN,
    GREEN_SOFT,
    GREEN_TEXT,
    MUTED_SOFT,
    TEXT_STRONG,
    bind_tree,
    card_frame,
    format_clock,
    icon_image,
    label,
    sp,
)


class BlinkPanel(ctk.CTkFrame):
    def __init__(self, master, on_stats):
        super().__init__(master, fg_color="transparent")
        self.on_stats = on_stats

        eye_card = card_frame(self)
        eye_card.pack(fill="x")
        top = ctk.CTkFrame(eye_card, fg_color="transparent")
        top.pack(fill="x", padx=17, pady=(17, 0))
        titles = ctk.CTkFrame(top, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "Estado de los ojos", 14, TEXT_STRONG, True).pack(anchor="w")
        self.eye_subtitle = label(titles, "Actualizado ahora", 10, MUTED_SOFT)
        self.eye_subtitle.pack(anchor="w", pady=(3, 0))

        self.status_pill = ctk.CTkFrame(top, fg_color=GREEN_SOFT, corner_radius=15)
        self.status_pill.pack(side="right", anchor="n")
        self.status_dot = ctk.CTkFrame(
            self.status_pill, width=7, height=7, fg_color=GREEN, corner_radius=4
        )
        self.status_dot.pack(side="left", padx=(9, 6), pady=7)
        self.status_dot.pack_propagate(False)
        self.status_label = label(
            self.status_pill, "Normal", 10, GREEN_TEXT, True, bg=GREEN_SOFT
        )
        self.status_label.pack(side="left", padx=(0, 10), pady=5)

        eyes = ctk.CTkFrame(eye_card, fg_color="transparent")
        eyes.pack(fill="x", padx=17, pady=(14, 0))
        eyes.grid_columnconfigure(0, weight=1, uniform="eyes")
        eyes.grid_columnconfigure(1, weight=1, uniform="eyes")
        self.eye_open_image = icon_image("eye", 48, "#5f55cc", 1.5)
        self.eye_closed_image = icon_image("eye_closed", 48, "#5f55cc", 1.5)
        self.eye_labels = []
        for column in range(2):
            box = ctk.CTkFrame(eyes, fg_color="#f7f8fb", corner_radius=10, border_width=1, border_color="#eceef4", height=70)
            box.grid(row=0, column=column, sticky="nsew", padx=(0, 5) if column == 0 else (5, 0))
            box.grid_propagate(False)
            image_label = ctk.CTkLabel(box, text="", image=self.eye_open_image, fg_color="#f7f8fb")
            image_label.place(relx=0.5, rely=0.5, anchor="center")
            self.eye_labels.append(image_label)

        labels_row = ctk.CTkFrame(eye_card, fg_color="transparent")
        labels_row.pack(fill="x", padx=17, pady=(8, 17))
        labels_row.grid_columnconfigure(0, weight=1, uniform="eyelabels")
        labels_row.grid_columnconfigure(1, weight=1, uniform="eyelabels")
        self.eye_state_labels = []
        for column, name in enumerate(("Ojo izquierdo", "Ojo derecho")):
            row = ctk.CTkFrame(labels_row, fg_color="transparent")
            row.grid(row=0, column=column, sticky="ew", padx=(0, 7) if column == 0 else (7, 0))
            label(row, name, 9, "#9ba1b0").pack(side="left")
            value = label(row, "Abierto", 9, "#39a977", True)
            value.pack(side="right")
            self.eye_state_labels.append(value)

        metrics = card_frame(self)
        metrics.pack(fill="x", pady=(14, 0))
        top = ctk.CTkFrame(metrics, fg_color="transparent")
        top.pack(fill="x", padx=17, pady=(17, 0))
        titles = ctk.CTkFrame(top, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "Metricas de sesion", 14, TEXT_STRONG, True).pack(anchor="w")
        label(titles, "Datos en tiempo real", 10, MUTED_SOFT).pack(anchor="w", pady=(3, 0))

        metrics_grid = ctk.CTkFrame(metrics, fg_color="transparent")
        metrics_grid.pack(fill="x", padx=17, pady=(13, 17))
        metrics_grid.grid_columnconfigure(0, weight=1, uniform="metric")
        metrics_grid.grid_columnconfigure(1, weight=1, uniform="metric")

        _, self.blink_value, _, self.blink_subtitle = self._metric(
            metrics_grid, 0, 0, "eye", "#675cdd", "#eeecff", "PARPADEOS", "0", None, "0 por minuto"
        )
        _, self.temp_value, _, self.temp_subtitle = self._metric(
            metrics_grid, 0, 1, "thermo", "#dd8141", "#fff0e4", "TEMPERATURA", "23.4", "C", "Optima"
        )
        _, self.light_value, _, self.light_subtitle = self._metric(
            metrics_grid, 1, 0, "sun", "#cb9821", "#fff7d9", "ILUMINACION", "420", "lux", "Adecuada"
        )
        _, self.timer_value, _, _ = self._metric(
            metrics_grid, 1, 1, "clock", "#4786d4", "#e9f3ff", "TIEMPO ACTIVO", "00:00:00", None, "Sesion actual", 14
        )
        self.detail_label = label(metrics, "Deteccion pendiente", 9, MUTED_SOFT)
        self.detail_label.pack(anchor="w", padx=17, pady=(0, 14))

        stats = ctk.CTkFrame(self, fg_color="#6b5de0", corner_radius=12, height=64)
        stats.pack(fill="x", pady=(14, 0))
        stats.pack_propagate(False)
        inner = ctk.CTkFrame(stats, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)
        tile = ctk.CTkFrame(inner, width=34, height=34, fg_color="#7c6de8", corner_radius=9)
        tile.pack(side="left", padx=(0, 11))
        tile.pack_propagate(False)
        ctk.CTkLabel(tile, text="", image=icon_image("chart", 17, "#ffffff", 1.8), fg_color="#7c6de8").place(
            relx=0.5, rely=0.5, anchor="center"
        )
        copy = ctk.CTkFrame(inner, fg_color="transparent")
        copy.pack(side="left", fill="both", expand=True)
        label(copy, "Ver estadisticas", 12, "#ffffff", True, bg="#6b5de0").pack(anchor="w")
        label(copy, "Consulta tu progreso y tendencias", 9, "#d7d2f7", bg="#6b5de0").pack(anchor="w", pady=(3, 0))
        ctk.CTkLabel(
            inner,
            text="",
            image=icon_image("chevron_right", 16, "#ffffff", 2.0),
            fg_color="#6b5de0",
        ).pack(side="right", padx=(8, 2))
        bind_tree(stats, "<Button-1>", lambda _event: self.on_stats(), skip_buttons=False)

    def _metric(self, parent, row, column, icon, icon_color, icon_bg, title, value, unit, subtitle, value_px=19):
        card = ctk.CTkFrame(
            parent,
            fg_color="#fafbfc",
            corner_radius=10,
            border_width=1,
            border_color="#eceef4",
            height=max(85, sp(68)),
        )
        card.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=(0, 5) if column == 0 else (5, 0),
            pady=(0, 10) if row == 0 else (0, 0),
        )
        card.pack_propagate(False)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=12)
        tile = ctk.CTkFrame(inner, width=34, height=34, fg_color=icon_bg, corner_radius=9)
        tile.pack(side="left", padx=(0, 10))
        tile.pack_propagate(False)
        ctk.CTkLabel(tile, text="", image=icon_image(icon, 18, icon_color, 1.8), fg_color=icon_bg).place(
            relx=0.5, rely=0.5, anchor="center"
        )
        text = ctk.CTkFrame(inner, fg_color="transparent")
        text.pack(side="left", fill="x", expand=True)
        label(text, title, 8, "#9ba2b3").pack(anchor="w")
        value_row = ctk.CTkFrame(text, fg_color="transparent")
        value_row.pack(anchor="w", pady=(2, 0))
        value_label = label(value_row, value, value_px, TEXT_STRONG, True)
        value_label.pack(side="left")
        if unit:
            label(value_row, unit, 10, TEXT_STRONG).pack(side="left", padx=(3, 0), pady=(5, 0))
        subtitle_label = label(text, subtitle, 8, "#5eb68d")
        subtitle_label.pack(anchor="w", pady=(2, 0))
        return card, value_label, value_row, subtitle_label

    def refresh(self, state):
        self.blink_value.configure(text=str(state.blinks))
        self.blink_subtitle.configure(text=f"{state.blink_rate:.0f} por minuto")
        self.temp_value.configure(text=f"{state.ambient.temperature_c:.1f}")
        self.light_value.configure(text=f"{state.ambient.lux:.0f}")
        self.timer_value.configure(text=format_clock(state.session_seconds))
        image = self.eye_closed_image if state.eyes_closed else self.eye_open_image
        eye_text = "Cerrado" if state.eyes_closed else "Abierto"
        color = "#c96e5b" if state.eyes_closed else "#39a977"
        for image_label in self.eye_labels:
            image_label.configure(image=image)
        for value_label in self.eye_state_labels:
            value_label.configure(text=eye_text, fg=color)

        settings = getattr(state, "settings", None)
        perclos_high = (
            settings.get("thresholds.perclos_high", 0.15) if settings else 0.15
        )
        long_limit = (
            settings.get("thresholds.long_closures_per_minute", 3) if settings else 3
        )
        status = getattr(state, "vision_status", None)
        available = getattr(status, "available", True)
        backend = getattr(status, "backend", "") or ""
        calibrating = bool(getattr(status, "calibrating", False))
        progress = getattr(state, "calibration_progress", 0.0)
        face_found = bool(getattr(status, "face_found", False))
        stream = getattr(state, "camera_stream", None)
        camera_running = bool(
            getattr(state, "camera_on", False)
            or (
                stream is not None
                and getattr(stream, "state", lambda: "")() == "running"
            )
        )

        if backend == "simulated":
            title, fg, dot, text = "Simulada", "#eef0f4", "#9ba1b0", "#667087"
            subtitle = "Fuente simulada activa"
        elif not available:
            title, fg, dot, text = "Sin camara", "#eef0f4", "#9ba1b0", "#667087"
            subtitle = getattr(status, "message", "") or "Detector no disponible"
        elif not camera_running:
            title, fg, dot, text = "Sin camara", "#eef0f4", "#9ba1b0", "#667087"
            subtitle = "Activa la camara para detectar parpadeos"
        elif calibrating:
            title, fg, dot, text = "Calibrando", "#fff7d9", "#cb9821", "#8a6a12"
            subtitle = f"Calibrando mirada... {progress * 100:.0f}%"
        elif not face_found:
            title, fg, dot, text = "Sin rostro", "#eef0f4", "#9ba1b0", "#667087"
            subtitle = "Colocate frente a la camara"
        elif state.perclos >= perclos_high or state.long_closures >= long_limit:
            title, fg, dot, text = "Fatiga alta", "#fdeceb", "#c96e5b", "#a84536"
            subtitle = "Cierres largos detectados"
        elif state.perclos >= perclos_high * 0.55:
            title, fg, dot, text = "Vigilar", "#fff0e4", "#dd8141", "#a65a21"
            subtitle = "Deteccion activa"
        else:
            title, fg, dot, text = "Normal", "#e9f8f1", "#39a977", "#2d8a63"
            subtitle = "Deteccion activa"

        self.status_label.configure(text=title, fg=text, bg=fg)
        self.status_pill.configure(fg_color=fg)
        self.status_dot.configure(fg_color=dot)
        self.eye_subtitle.configure(text=subtitle)
        self.detail_label.configure(
            text=(
                f"Duracion media {state.blink_duration_ms:.0f} ms  ·  "
                f"PERCLOS {state.perclos * 100:.1f}%  ·  "
                f"{state.long_closures} cierres largos"
            )
        )
