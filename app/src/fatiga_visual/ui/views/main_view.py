"""Interfaz 1: Monitoreo en vivo.

Qué va aquí:
- Camara en vivo, estado de los ojos, métricas de sesión y alerta prioritaria.
- Pausar/reanudar el monitoreo y activar/apagar la camara.

Se actualiza con refresh(topic). El reloj y la simulación de parpadeo los
controla MainWindow mediante AppState.
"""

import customtkinter as ctk

from fatiga_visual.ui.panels.blink_panel import BlinkPanel
from fatiga_visual.ui.theme import (
    ALERT_BG,
    ALERT_BORDER,
    BG,
    GREEN,
    GREEN_SOFT,
    GREEN_TEXT,
    GAP,
    MUTED,
    MUTED_SOFT,
    PAD,
    SALMON,
    TEXT,
    TEXT_STRONG,
    bind_tree,
    card_frame,
    fnt,
    icon_image,
    label,
)
from fatiga_visual.ui.widgets.camera_widget import CameraWidget


class MainView(ctk.CTkFrame):
    def __init__(self, master, state, on_stats, on_recommendations):
        super().__init__(master, fg_color=BG)
        self.state = state
        self.on_stats = on_stats
        self.on_recommendations = on_recommendations
        self.camera_on = False
        self._camera_busy = False

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=PAD, pady=(18, 22))

        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x")
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")
        label(left, "SESION ACTIVA", 10, "#6b5ce7", True, bg=BG).pack(anchor="w")
        label(left, "Buenos dias, Alex", 34, TEXT, True, bg=BG).pack(anchor="w", pady=(5, 0))
        label(
            left,
            "Blinky esta cuidando tu salud visual mientras trabajas.",
            13,
            MUTED,
            bg=BG,
        ).pack(anchor="w", pady=(7, 0))

        self.status_pill = ctk.CTkFrame(header, fg_color=GREEN_SOFT, corner_radius=15)
        self.status_pill.pack(side="right", anchor="s", pady=(0, 4))
        self.status_dot = ctk.CTkFrame(self.status_pill, width=7, height=7, fg_color=GREEN, corner_radius=4)
        self.status_dot.pack(side="left", padx=(11, 7))
        self.status_dot.pack_propagate(False)
        self.status_text = label(self.status_pill, "Monitoreo en curso", 11, GREEN_TEXT, True, bg=GREEN_SOFT)
        self.status_text.pack(side="left", padx=(0, 12), pady=6)

        grid = ctk.CTkFrame(main, fg_color="transparent")
        grid.pack(fill="x", pady=(18, 0))
        grid.grid_columnconfigure(0, weight=158)
        grid.grid_columnconfigure(1, weight=80)
        grid.grid_rowconfigure(0, weight=1)

        self._build_camera_card(grid)
        self.panel = BlinkPanel(grid, on_stats)
        self.panel.grid(row=0, column=1, sticky="nsew")
        self._build_alert(main)
        self._build_footer(main)
        self.refresh()

    def _build_camera_card(self, parent):
        card = card_frame(parent)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, GAP))

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=17, pady=(17, 0))

        titles = ctk.CTkFrame(top, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "Camara en vivo", 14, TEXT_STRONG, True).pack(anchor="w")
        label(titles, "Deteccion facial local", 10, MUTED_SOFT).pack(anchor="w", pady=(3, 0))

        self.camera_button = ctk.CTkButton(
            top,
            text="Activar camara",
            image=icon_image("camera", 15, "#676f83", 1.8),
            compound="left",
            command=self._toggle_camera,
            height=36,
            width=156,
            corner_radius=8,
            fg_color="#f6f7fa",
            hover_color="#f4f2ff",
            border_width=1,
            border_color="#e5e8ef",
            text_color="#676f83",
            font=fnt(11, True),
        )
        self.camera_button.pack(side="right")

        self.feed = CameraWidget(
            card,
            self._toggle_camera,
            stream=getattr(self.state, "camera_stream", None),
        )
        self.feed.on_lost = self._on_camera_lost
        self.feed.pack(padx=17, pady=(15, 0))

        sensor_strip = ctk.CTkFrame(card, fg_color="transparent", height=56)
        sensor_strip.pack(fill="x", padx=18)
        sensor_strip.grid_propagate(False)
        for column in range(3):
            sensor_strip.grid_columnconfigure(column, weight=1)

        self.sensor_values = {}
        sensors = [
            ("Camara", "En espera"),
            ("Sensor ambiental", "Conectado"),
            ("Deteccion facial", "En espera"),
        ]
        for index, (name, value) in enumerate(sensors):
            item = ctk.CTkFrame(sensor_strip, fg_color="transparent")
            item.grid(row=0, column=index, sticky="nsew")
            inner = ctk.CTkFrame(item, fg_color="transparent")
            inner.place(relx=0.5, rely=0.5, anchor="center")
            dot = ctk.CTkFrame(inner, width=6, height=6, fg_color="#44bc87", corner_radius=3)
            dot.pack(side="left", padx=(0, 6))
            dot.pack_propagate(False)
            label(inner, name, 9, "#9299aa").pack(side="left")
            value_label = label(inner, " " + value, 9, "#596176", True)
            value_label.pack(side="left")
            self.sensor_values[name] = value_label

    def _build_alert(self, parent):
        self.alert = ctk.CTkFrame(parent, fg_color=ALERT_BG, corner_radius=12, border_width=1, border_color=ALERT_BORDER)

        icon_tile = ctk.CTkFrame(self.alert, width=46, height=46, fg_color="#fee9e4", corner_radius=11)
        icon_tile.pack(side="left", padx=(17, 15), pady=15)
        icon_tile.pack_propagate(False)
        ctk.CTkLabel(
            icon_tile, text="", image=icon_image("eye_closed", 27, "#c66755", 1.7), fg_color="#fee9e4"
        ).place(relx=0.5, rely=0.5, anchor="center")

        text = ctk.CTkFrame(self.alert, fg_color="transparent")
        text.pack(side="left", fill="both", expand=True, pady=12)
        label(text, "FATIGA VISUAL DETECTADA", 8, "#c66f5d", True, bg=ALERT_BG).pack(anchor="w")
        self.alert_title = label(text, "Tus ojos necesitan una pausa", 12, "#4a3434", True, bg=ALERT_BG)
        self.alert_title.pack(anchor="w", pady=(2, 0))
        self.alert_message = label(text, "", 9, "#8f7774", bg=ALERT_BG, wrap=760)
        self.alert_message.pack(anchor="w", pady=(3, 0))

        actions = ctk.CTkFrame(self.alert, fg_color="transparent")
        actions.pack(side="right", padx=(15, 17), pady=15)
        ctk.CTkButton(
            actions,
            text="Ahora no",
            command=self._dismiss_alert,
            height=36,
            width=80,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#f5e8e4",
            text_color="#887b79",
            font=fnt(10, True),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            actions,
            text="Ver ejercicios",
            command=self.on_recommendations,
            height=36,
            width=136,
            corner_radius=8,
            fg_color=SALMON,
            hover_color="#b85f4d",
            text_color="#ffffff",
            font=fnt(10, True),
        ).pack(side="left")

    def _build_footer(self, parent):
        separator = ctk.CTkFrame(parent, height=1, fg_color="#e3e6ed", corner_radius=0)
        separator.pack(fill="x", pady=(10, 0))

        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.pack(fill="x", pady=(12, 0))
        left = ctk.CTkFrame(footer, fg_color="transparent")
        left.pack(side="left")
        dot = ctk.CTkFrame(left, width=7, height=7, fg_color=GREEN, corner_radius=4)
        dot.pack(side="left", padx=(1, 12))
        dot.pack_propagate(False)
        text = ctk.CTkFrame(left, fg_color="transparent")
        text.pack(side="left")
        label(text, "Todo funciona correctamente", 11, TEXT_STRONG, True, bg=BG).pack(anchor="w")
        label(text, "Ultima comprobacion hace 12 segundos", 9, "#9ba1af", bg=BG).pack(anchor="w", pady=(2, 0))

        self.pause_image = icon_image("pause", 14, "#656d7e", 1.8)
        self.play_image = icon_image("play", 14, "#656d7e", 1.8)
        self.pause_button = ctk.CTkButton(
            footer,
            text="Pausar monitoreo",
            image=self.pause_image,
            compound="left",
            command=self._toggle_monitoring,
            height=38,
            width=184,
            corner_radius=8,
            fg_color="#ffffff",
            hover_color="#f7f6ff",
            border_width=1,
            border_color="#dde1e8",
            text_color="#656d7e",
            font=fnt(11, True),
        )
        self.pause_button.pack(side="right")

    def _toggle_camera(self):
        if self._camera_busy:
            return
        if self.camera_on:
            self._stop_camera()
        else:
            self._start_camera()

    def _start_camera(self):
        self._camera_busy = True
        self.camera_button.configure(text="Conectando...", state="disabled")
        self.feed.set_state("connecting")
        self.sensor_values["Camara"].configure(text=" Conectando")
        self.sensor_values["Deteccion facial"].configure(text=" Conectando")
        self.feed.start(self._on_camera_ready)

    def _on_camera_ready(self, ok, message):
        self._camera_busy = False
        self.camera_button.configure(state="normal")
        if ok:
            self.camera_on = True
            self.camera_button.configure(text="Apagar camara")
            self.sensor_values["Camara"].configure(text=" Activa")
            self.sensor_values["Deteccion facial"].configure(text=" Activa")
        else:
            self.camera_on = False
            self.camera_button.configure(text="Activar camara")
            self.feed.set_state("error")
            self.sensor_values["Camara"].configure(text=" En espera")
            self.sensor_values["Deteccion facial"].configure(text=" En espera")
        self.state.set_camera(self.camera_on)

    def _stop_camera(self):
        self.camera_on = False
        self._camera_busy = False
        self.camera_button.configure(text="Activar camara", state="normal")
        self.feed.set_state("off")
        self.sensor_values["Camara"].configure(text=" En espera")
        self.sensor_values["Deteccion facial"].configure(text=" En espera")
        self.update_idletasks()
        self.feed.stop()
        self.state.set_camera(False)

    def _on_camera_lost(self, message):
        self.camera_on = False
        self._camera_busy = False
        self.camera_button.configure(text="Activar camara", state="normal")
        self.feed.stop()
        self.feed.set_state("error")
        self.sensor_values["Camara"].configure(text=" En espera")
        self.sensor_values["Deteccion facial"].configure(text=" En espera")
        self.state.set_camera(False)

    def _toggle_monitoring(self):
        self.state.toggle_running()

    def _dismiss_alert(self):
        self.state.set_alert_dismissed(True)

    def refresh(self, topic=None):
        state = self.state
        if state.running:
            self.status_pill.configure(fg_color=GREEN_SOFT)
            self.status_dot.configure(fg_color=GREEN)
            self.status_text.configure(text="Monitoreo en curso", fg=GREEN_TEXT, bg=GREEN_SOFT)
            self.pause_button.configure(text="Pausar monitoreo", image=self.pause_image)
        else:
            self.status_pill.configure(fg_color="#fff5df")
            self.status_dot.configure(fg_color="#e7a83d")
            self.status_text.configure(text="Monitoreo pausado", fg="#9c6d21", bg="#fff5df")
            self.pause_button.configure(text="Reanudar monitoreo", image=self.play_image)

        self.panel.refresh(state)

        primary = state.primary_recommendation()
        if primary is None or state.alert_dismissed:
            self.alert.pack_forget()
        else:
            self.alert_title.configure(text=primary.title)
            self.alert_message.configure(text=primary.message)
            self.alert.pack(fill="x", pady=(14, 0))

    def destroy(self):
        try:
            feed = getattr(self, "feed", None)
            if feed is not None:
                feed.stop()
        finally:
            super().destroy()
