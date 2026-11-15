"""Banner de alerta reutilizable.

Qué va aquí:
- Mostrar la recomendación prioritaria (alta o media).
- Botón de acción y cierre; no calcula reglas.
"""

import customtkinter as ctk

from fatiga_visual.ui.theme import BG, fnt, icon_image, label


class AlertBanner(ctk.CTkFrame):
    def __init__(self, master, on_action=None, on_close=None):
        super().__init__(master, fg_color="#fff7ec", corner_radius=9, border_width=1, border_color="#f3e2c6")
        self.on_action = on_action
        self.on_close = on_close

        icon = ctk.CTkFrame(self, width=36, height=36, fg_color="#f7e6c8", corner_radius=9)
        icon.pack(side="left", padx=(12, 10), pady=11)
        icon.pack_propagate(False)
        ctk.CTkLabel(icon, text="!", font=fnt(15, True), text_color="#b37a25").place(
            relx=0.5, rely=0.5, anchor="center"
        )

        text = ctk.CTkFrame(self, fg_color="transparent")
        text.pack(side="left", pady=8)
        self.title_label = label(text, "", 11, "#7c5a1f", True, bg="#fff7ec")
        self.title_label.pack(anchor="w")
        self.message_label = label(text, "", 9, "#9a8259", bg="#fff7ec")
        self.message_label.pack(anchor="w", pady=(2, 0))

        self.action_button = ctk.CTkButton(
            self,
            text="Ver recomendaciones",
            command=self._action,
            height=32,
            width=160,
            corner_radius=7,
            fg_color="#ffffff",
            hover_color="#fdf3e3",
            border_width=1,
            border_color="#ecd9b6",
            text_color="#8a641f",
            font=fnt(9, True),
        )
        self.action_button.pack(side="right", padx=(6, 0), pady=11)

        self.close_button = ctk.CTkButton(
            self,
            text="",
            image=icon_image("close", 14, "#a98b55", 1.8),
            command=self._close,
            height=30,
            width=30,
            corner_radius=15,
            fg_color="transparent",
            hover_color="#f6ecd9",
        )
        self.close_button.pack(side="right", padx=(0, 8), pady=11)

    def show(self, recommendation):
        if recommendation is None:
            self.pack_forget()
            return
        self.title_label.configure(text=recommendation.title)
        self.message_label.configure(text=recommendation.message)
        self.action_button.configure(text=recommendation.action)
        self.pack(fill="x")

    def _action(self):
        if self.on_action is not None:
            self.on_action()

    def _close(self):
        if self.on_close is not None:
            self.on_close()
        else:
            self.pack_forget()
