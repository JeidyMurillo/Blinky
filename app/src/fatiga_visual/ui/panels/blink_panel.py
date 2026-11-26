"""Panel derecho de Monitoreo: ojos, tiempo de sesión y métricas de parpadeo.

Qué va aquí:
- Tarjeta de estado ocular (ojo izquierdo/derecho).
- Tarjeta compacta con el tiempo de la sesión.
- Cuatro métricas de parpadeo: parpadeos, duración media, cierres largos y PERCLOS.
- Botón grande que navega a la vista de Estadísticas.

Se refresca con refresh(state) sin conocer la cámara ni MQTT.
"""

from datetime import datetime

import customtkinter as ctk

from fatiga_visual.core.config import DEFAULTS

from fatiga_visual.ui.theme import (
    AMBER,
    AMBER_SOFT,
    AMBER_TEXT,
    BG,
    GREEN,
    GREEN_SOFT,
    GREEN_TEXT,
    MUTED_SOFT,
    SALMON,
    TEXT_STRONG,
    bind_tree,
    card_frame,
    format_clock,
    icon_image,
    label,
)


class BlinkPanel(ctk.CTkFrame):
    def __init__(self, master, on_stats):
        super().__init__(master, fg_color="transparent")
        self.on_stats = on_stats

        eye_card = card_frame(self)
        eye_card.pack(fill="x")
        top = ctk.CTkFrame(eye_card, fg_color="transparent")
        top.pack(fill="x", padx=17, pady=(14, 0))
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
        eyes.pack(fill="x", padx=17, pady=(12, 0))
        eyes.grid_columnconfigure(0, weight=1, uniform="eyes")
        eyes.grid_columnconfigure(1, weight=1, uniform="eyes")
        self.eye_open_image = icon_image("eye", 40, "#5f55cc", 1.5)
        self.eye_closed_image = icon_image("eye_closed", 40, "#5f55cc", 1.5)
        self.eye_labels = []
        for column in range(2):
            box = ctk.CTkFrame(
                eyes,
                fg_color="#f7f8fb",
                corner_radius=10,
                border_width=1,
                border_color="#eceef4",
                height=64,
            )
            box.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=(0, 5) if column == 0 else (5, 0),
            )
            box.grid_propagate(False)
            image_label = ctk.CTkLabel(
                box, text="", image=self.eye_open_image, fg_color="#f7f8fb"
            )
            image_label.place(relx=0.5, rely=0.5, anchor="center")
            self.eye_labels.append(image_label)

        labels_row = ctk.CTkFrame(eye_card, fg_color="transparent")
        labels_row.pack(fill="x", padx=17, pady=(6, 12))
        labels_row.grid_columnconfigure(0, weight=1, uniform="eyelabels")
        labels_row.grid_columnconfigure(1, weight=1, uniform="eyelabels")
        self.eye_state_labels = []
        for column, name in enumerate(("Ojo izquierdo", "Ojo derecho")):
            row = ctk.CTkFrame(labels_row, fg_color="transparent")
            row.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=(0, 7) if column == 0 else (7, 0),
            )
            label(row, name, 9, "#9ba1b0").pack(side="left")
            value = label(row, "Abierto", 9, "#39a977", True)
            value.pack(side="right")
            self.eye_state_labels.append(value)

        # Tarjeta compacta de tiempo de sesión (session-time-card en Figma).
        chrono = card_frame(self)
        chrono.configure(height=82)
        chrono.pack(fill="x", pady=(14, 0))
        chrono.pack_propagate(False)
        chrono_inner = ctk.CTkFrame(chrono, fg_color="transparent")
        chrono_inner.pack(fill="both", expand=True, padx=17, pady=9)

        tile = ctk.CTkFrame(chrono_inner, width=34, height=34, fg_color="#e9f3ff", corner_radius=9)
        tile.pack(side="left", padx=(0, 12))
        tile.pack_propagate(False)
        ctk.CTkLabel(
            tile,
            text="",
            image=icon_image("clock", 18, "#4786d4", 1.8),
            fg_color="#e9f3ff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        chrono_copy = ctk.CTkFrame(chrono_inner, fg_color="transparent")
        chrono_copy.pack(side="left", fill="both", expand=True)
        label(chrono_copy, "TIEMPO DE LA SESIÓN", 8, "#9ba2b3").pack(anchor="w")
        self.chrono_value = label(chrono_copy, "00:00:00", 20, TEXT_STRONG, True)
        self.chrono_value.pack(anchor="w", pady=(3, 0))
        self.chrono_note = label(chrono_copy, "Monitoreo activo", 8, "#6b7488")
        self.chrono_note.pack(anchor="w", pady=(2, 0))

        self.chrono_pill = ctk.CTkFrame(chrono_inner, fg_color=GREEN_SOFT, corner_radius=13)
        self.chrono_pill.pack(side="right", anchor="center")
        self.chrono_status = label(
            self.chrono_pill, "En curso", 10, GREEN_TEXT, True, bg=GREEN_SOFT
        )
        self.chrono_status.pack(padx=(10, 10), pady=5)

        # Cuatro métricas de parpadeo (metric-grid en Figma).
        metrics = card_frame(self)
        metrics.pack(fill="x", pady=(14, 0))
        top = ctk.CTkFrame(metrics, fg_color="transparent")
        top.pack(fill="x", padx=17, pady=(14, 0))
        titles = ctk.CTkFrame(top, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "Métricas de parpadeo", 14, TEXT_STRONG, True).pack(anchor="w")
        label(titles, "Análisis ocular en tiempo real", 10, MUTED_SOFT).pack(
            anchor="w", pady=(3, 0)
        )

        metrics_grid = ctk.CTkFrame(metrics, fg_color="transparent")
        metrics_grid.pack(fill="x", padx=17, pady=(11, 12))
        metrics_grid.grid_columnconfigure(0, weight=1, uniform="metric")
        metrics_grid.grid_columnconfigure(1, weight=1, uniform="metric")

        _, self.blink_value, self.blink_subtitle = self._metric(
            metrics_grid, 0, 0, "eye", "#675cdd", "#eeecff", "PARPADEOS", "0",
            "0 por minuto",
        )
        _, self.duration_value, self.duration_subtitle = self._metric(
            metrics_grid, 0, 1, "clock", "#675cdd", "#eeecff", "DURACIÓN MEDIA", "184",
            "Parpadeo normal", "ms", 19,
        )
        _, self.long_closures_value, self.long_closures_subtitle = self._metric(
            metrics_grid, 1, 0, "eye_closed", "#c5656d", "#fdecef", "CIERRES LARGOS",
            "0", "En esta sesión",
        )
        _, self.perclos_value, self.perclos_subtitle = self._metric(
            metrics_grid, 1, 1, "gauge", "#278f96", "#e5f6f7", "PERCLOS", "0.0",
            "Rango saludable", "%", 19,
        )

        stats = ctk.CTkFrame(self, fg_color="#6b5de0", corner_radius=12, height=60)
        stats.pack(fill="x", pady=(12, 0))
        stats.pack_propagate(False)
        inner = ctk.CTkFrame(stats, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=10)
        tile = ctk.CTkFrame(inner, width=34, height=34, fg_color="#7c6de8", corner_radius=9)
        tile.pack(side="left", padx=(0, 11))
        tile.pack_propagate(False)
        ctk.CTkLabel(
            tile, text="", image=icon_image("chart", 17, "#ffffff", 1.8), fg_color="#7c6de8"
        ).place(relx=0.5, rely=0.5, anchor="center")
        copy = ctk.CTkFrame(inner, fg_color="transparent")
        copy.pack(side="left", fill="both", expand=True)
        label(copy, "Ver estadísticas", 12, "#ffffff", True, bg="#6b5de0").pack(anchor="w")
        label(
            copy, "Consulta tu progreso y tendencias", 9, "#d7d2f7", bg="#6b5de0"
        ).pack(anchor="w", pady=(3, 0))
        ctk.CTkLabel(
            inner,
            text="",
            image=icon_image("chevron_right", 16, "#ffffff", 2.0),
            fg_color="#6b5de0",
        ).pack(side="right", padx=(8, 2))
        bind_tree(stats, "<Button-1>", lambda _event: self.on_stats(), skip_buttons=False)

    def _metric(
        self, parent, row, column, icon, icon_color, icon_bg, title, value,
        subtitle, unit=None, value_px=19,
    ):
        card = ctk.CTkFrame(
            parent,
            fg_color="#fafbfc",
            corner_radius=10,
            border_width=1,
            border_color="#eceef4",
            height=78,
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
        inner.pack(fill="both", expand=True, padx=10, pady=8)
        tile = ctk.CTkFrame(inner, width=34, height=34, fg_color=icon_bg, corner_radius=9)
        tile.pack(side="left", padx=(0, 10))
        tile.pack_propagate(False)
        ctk.CTkLabel(
            tile, text="", image=icon_image(icon, 18, icon_color, 1.8), fg_color=icon_bg
        ).place(relx=0.5, rely=0.5, anchor="center")
        text = ctk.CTkFrame(inner, fg_color="transparent")
        text.pack(side="left", fill="x", expand=True)
        label(text, title, 8, "#9ba2b3").pack(anchor="w")
        value_row = ctk.CTkFrame(text, fg_color="transparent")
        value_row.pack(anchor="w", pady=(2, 0))
        value_label = label(value_row, value, value_px, TEXT_STRONG, True)
        value_label.pack(side="left")
        if unit:
            label(value_row, unit, 10, TEXT_STRONG).pack(side="left", padx=(2, 0), pady=(5, 0))
        subtitle_label = label(text, subtitle, 8, "#5eb68d")
        subtitle_label.pack(anchor="w", pady=(2, 0))
        return card, value_label, subtitle_label

    def refresh(self, state):
        # Estados de los ojos.
        image = self.eye_closed_image if state.eyes_closed else self.eye_open_image
        eye_text = "Cerrado" if state.eyes_closed else "Abierto"
        color = "#c96e5b" if state.eyes_closed else "#39a977"
        for image_label in self.eye_labels:
            image_label.configure(image=image)
        for value_label in self.eye_state_labels:
            value_label.configure(text=eye_text, fg=color)

        settings = getattr(state, "settings", None)
        defaults = DEFAULTS["thresholds"]
        perclos_high = (
            settings.get("thresholds.perclos_high") if settings else defaults["perclos_high"]
        )
        long_limit = (
            settings.get("thresholds.long_closures_per_minute")
            if settings
            else defaults["long_closures_per_minute"]
        )
        blink_rate_low = (
            settings.get("thresholds.blink_rate_low")
            if settings
            else defaults["blink_rate_low"]
        )
        perclos_min = (
            settings.get("thresholds.perclos_min_observation_seconds")
            if settings
            else defaults["perclos_min_observation_seconds"]
        )
        perclos_ready = (getattr(state, "blink_elapsed_seconds", 0.0) or 0.0) >= perclos_min
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
        elif state.long_closures >= long_limit:
            title, fg, dot, text = "Fatiga alta", "#fdeceb", "#c96e5b", "#a84536"
            subtitle = "Cierres largos detectados"
        elif state.perclos >= perclos_high and perclos_ready:
            title, fg, dot, text = "Fatiga alta", "#fdeceb", "#c96e5b", "#a84536"
            subtitle = f"PERCLOS {state.perclos * 100:.0f}%"
        elif state.perclos >= perclos_high * 0.55:
            title, fg, dot, text = "Vigilar", "#fff0e4", "#dd8141", "#a65a21"
            subtitle = "PERCLOS en aumento"
        else:
            title, fg, dot, text = "Normal", "#e9f8f1", "#39a977", "#2d8a63"
            subtitle = "Deteccion activa"

        self.status_label.configure(text=title, fg=text, bg=fg)
        self.status_pill.configure(fg_color=fg)
        self.status_dot.configure(fg_color=dot)
        self.eye_subtitle.configure(text=subtitle)

        # Tiempo de sesión y estado del cronómetro.
        continuous = state.continuous_seconds
        limit = state.break_after_seconds
        self.chrono_value.configure(text=format_clock(state.session_seconds))
        if getattr(state, "break_active", False):
            active = state.active_break
            started = getattr(active, "started_at", datetime.now())
            status, bg, fg, color = (
                "En pausa", "#eaf3ff", "#4786d4", "#4786d4",
            )
            note = f"Pausa en curso desde {started:%H:%M}"
        elif state.break_due:
            status, bg, fg, color = (
                "Pausa debida", "#fdeceb", SALMON, SALMON,
            )
            note = "Momento de descansar la vista"
        elif not state.running:
            status, bg, fg, color = (
                "En pausa", AMBER_SOFT, AMBER_TEXT, AMBER,
            )
            note = "Monitoreo detenido"
        elif not state.user_present:
            status, bg, fg, color = (
                "En espera", "#eef0f4", "#667087", "#9ba1b0",
            )
            note = "Esperando deteccion de rostro"
        else:
            status, bg, fg, color = (
                "En curso", GREEN_SOFT, GREEN_TEXT, GREEN,
            )
            note = f"Proxima pausa en {format_clock(max(0, limit - continuous))}"

        self.chrono_status.configure(text=status, fg=fg, bg=bg)
        self.chrono_pill.configure(fg_color=bg)
        self.chrono_note.configure(text=note, fg=color)

        # Métricas de parpadeo.
        self.blink_value.configure(text=str(state.blinks))
        rate_status = state.blink_rate_status(blink_rate_low)
        trend = {1: "↑", -1: "↓", 0: "→"}.get(state.blink_rate_trend(), "→")
        rate_text = f"{state.blink_rate:.0f}/min · {rate_status} {trend}"
        self.blink_subtitle.configure(
            text=rate_text,
            fg="#c96e5b" if rate_status == "Baja" else "#5eb68d" if rate_status == "Normal" else None,
        )
        duration = state.blink_duration_ms
        self.duration_value.configure(text=f"{duration:.0f}")
        if duration <= 0:
            duration_note, duration_color = "Sin datos", MUTED_SOFT
        elif 100 <= duration <= 300:
            duration_note, duration_color = "Parpadeo normal", "#5eb68d"
        else:
            duration_note, duration_color = "Revisar duración", "#dd8141"
        self.duration_subtitle.configure(text=duration_note, fg=duration_color)
        self.long_closures_value.configure(text=str(state.long_closures))
        self.long_closures_subtitle.configure(
            text="En esta sesión",
            fg="#5eb68d" if state.long_closures < long_limit else "#c96e5b",
        )
        self.perclos_value.configure(text=f"{state.perclos * 100:.1f}")
        self.perclos_subtitle.configure(
            text="Rango saludable" if state.perclos < perclos_high else "Nivel alto",
            fg="#5eb68d" if state.perclos < perclos_high else "#c96e5b",
        )
