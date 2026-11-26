"""Interfaz 3: Recomendaciones.

Qué va aquí:
- Recomendaciones activas generadas por decision.engine.
- Rutina de alivio visual y lecturas del entorno.
- Marcar una recomendación como completada actualiza AppState.
"""

from datetime import datetime

import customtkinter as ctk

from fatiga_visual.ui.panels.ambient_panel import AmbientPanel
from fatiga_visual.ui.theme import (
    BG,
    GAP,
    MUTED,
    MUTED_SOFT,
    PAD,
    PURPLE,
    PURPLE_SOFT,
    TEXT,
    TEXT_STRONG,
    card_frame,
    fnt,
    icon_image,
    label,
)

SEVERITY = {
    "high": ("#fff3ef", "#f3d8d1", "#c96e5b", "Prioridad alta"),
    "medium": ("#fff9ec", "#f3e6c9", "#d79a3f", "Prioridad media"),
    "low": ("#eef7f2", "#d9ede2", "#3ba478", "Sugerencia"),
}


class RecommendationsView(ctk.CTkFrame):
    def __init__(self, master, state):
        super().__init__(master, fg_color=BG)
        self.state = state

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=PAD, pady=(28, 36))

        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x")
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")
        label(left, "RECOMENDACIONES", 11, "#6b5ce7", True, bg=BG).pack(anchor="w")
        label(left, "Cuida tu vista", 36, TEXT, True, bg=BG).pack(anchor="w", pady=(5, 0))
        label(
            left,
            "Ejercicios y habitos generados a partir de tu monitoreo.",
            14,
            MUTED,
            bg=BG,
        ).pack(anchor="w", pady=(7, 0))

        self.count_pill = ctk.CTkFrame(header, fg_color=PURPLE_SOFT, corner_radius=15)
        self.count_pill.pack(side="right", anchor="s", pady=(0, 4))
        self.count_label = label(self.count_pill, "", 12, "#5a4fd1", True, bg=PURPLE_SOFT)
        self.count_label.pack(padx=16, pady=6)

        grid = ctk.CTkFrame(main, fg_color="transparent")
        grid.pack(fill="both", expand=True, pady=(24, 0))
        grid.grid_columnconfigure(0, weight=3, uniform="recs")
        grid.grid_columnconfigure(1, weight=2, uniform="recs")
        grid.grid_rowconfigure(0, weight=1)

        self.list_card = card_frame(grid)
        self.list_card.grid(row=0, column=0, sticky="nsew", padx=(0, GAP))
        top = ctk.CTkFrame(self.list_card, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(18, 0))
        titles = ctk.CTkFrame(top, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "Para ti ahora", 15, TEXT_STRONG, True).pack(anchor="w")
        label(titles, "Basado en tu sesion de hoy", 11, MUTED_SOFT).pack(anchor="w", pady=(3, 0))
        self.list_hint = label(top, "", 11, "#8b93a2")
        self.list_hint.pack(side="right", anchor="n", pady=(2, 0))

        self.list_body = ctk.CTkScrollableFrame(
            self.list_card, fg_color="transparent", scrollbar_button_color="#e1e4eb", height=470
        )
        self.list_body.pack(fill="both", expand=True, padx=12, pady=(10, 16))

        side = ctk.CTkFrame(grid, fg_color="transparent")
        side.grid(row=0, column=1, sticky="nsew")

        routine = card_frame(side)
        routine.pack(fill="x")
        top = ctk.CTkFrame(routine, fg_color="transparent")
        top.pack(fill="x", padx=17, pady=(17, 0))
        titles = ctk.CTkFrame(top, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "Rutina 20-20-20", 15, TEXT_STRONG, True).pack(anchor="w")
        label(titles, "Alivio rapido para tus ojos", 11, MUTED_SOFT).pack(anchor="w", pady=(3, 0))
        ctk.CTkLabel(top, text="", image=icon_image("clock", 20, "#858d9c", 1.7)).pack(side="right", anchor="n")

        steps = ctk.CTkFrame(routine, fg_color="transparent")
        steps.pack(fill="x", padx=17, pady=(13, 17))
        for index, (title, detail) in enumerate(
            (
                ("Cada 20 minutos", "Haz una pausa breve de la pantalla."),
                ("Mira a 6 metros", "Enfoca un objeto lejano durante 20 segundos."),
                ("Parpadea lento", "Cierra los ojos y respira profundo."),
            )
        ):
            row = ctk.CTkFrame(steps, fg_color="transparent")
            row.pack(fill="x", pady=(0 if index == 0 else 10, 0))
            badge = ctk.CTkFrame(row, width=28, height=28, fg_color=PURPLE_SOFT, corner_radius=8)
            badge.pack(side="left")
            badge.pack_propagate(False)
            ctk.CTkLabel(
                badge,
                text=str(index + 1),
                font=fnt(12, True),
                text_color="#5a4fd1",
                fg_color=PURPLE_SOFT,
            ).place(relx=0.5, rely=0.5, anchor="center")
            text = ctk.CTkFrame(row, fg_color="transparent")
            text.pack(side="left", padx=(10, 0), fill="x", expand=True)
            label(text, title, 12, TEXT_STRONG, True).pack(anchor="w")
            label(text, detail, 10, MUTED).pack(anchor="w", pady=(1, 0))

        self.ambient_panel = AmbientPanel(side)
        self.ambient_panel.pack(fill="x", pady=(14, 0))

        streak = ctk.CTkFrame(side, fg_color="#6b5de0", corner_radius=12, height=74)
        streak.pack(fill="x", pady=(14, 0))
        streak.pack_propagate(False)
        inner = ctk.CTkFrame(streak, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=12)
        tile = ctk.CTkFrame(inner, width=36, height=36, fg_color="#7c6de8", corner_radius=9)
        tile.pack(side="left", padx=(0, 12))
        tile.pack_propagate(False)
        ctk.CTkLabel(tile, text="", image=icon_image("check", 18, "#ffffff", 1.9), fg_color="#7c6de8").place(
            relx=0.5, rely=0.5, anchor="center"
        )
        copy = ctk.CTkFrame(inner, fg_color="transparent")
        copy.pack(side="left")
        label(copy, "Racha de cuidado", 12, "#ffffff", True, bg="#6b5de0").pack(anchor="w")
        label(copy, "4 dias cumpliendo tus pausas", 10, "#d7d2f7", bg="#6b5de0").pack(anchor="w", pady=(3, 0))
        self._signature = None
        self.refresh()

    def refresh(self, topic=None):
        self.ambient_panel.refresh(self.state.ambient)
        if topic not in (None, "recommendations"):
            return

        recommendations = list(self.state.recommendations)
        signature = tuple(
            (item.id, item.severity, item.title, item.message, item.action)
            for item in recommendations
        )
        if signature == self._signature:
            return
        self._signature = signature

        for child in self.list_body.winfo_children():
            child.destroy()

        total = len(recommendations)
        self.count_label.configure(text=f"{total} activas" if total else "Todo al dia")
        self.list_hint.configure(text=f"{total} sugerencias" if total else "")

        if not recommendations:
            empty = ctk.CTkFrame(self.list_body, fg_color="#f8fafc", corner_radius=10, border_width=1, border_color="#eceef4")
            empty.pack(fill="x", padx=6, pady=6)
            label(empty, "Estas al dia", 14, TEXT_STRONG, True, bg="#f8fafc").pack(pady=(26, 4))
            label(
                empty,
                "No hay recomendaciones activas. Sigue con tus pausas.",
                11,
                MUTED,
                bg="#f8fafc",
            ).pack(pady=(0, 26))
            return

        for index, recommendation in enumerate(recommendations):
            self._item(recommendation, first=index == 0)

    def _item(self, recommendation, first=False):
        bg, border, accent, severity_text = SEVERITY.get(
            recommendation.severity, SEVERITY["low"]
        )
        card = ctk.CTkFrame(
            self.list_body,
            fg_color=bg if first else "#fbfcfd",
            corner_radius=11,
            border_width=1,
            border_color=border if first else "#eceef4",
        )
        card.pack(fill="x", padx=6, pady=(0 if first else 8, 8))

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=14, pady=12)

        tile = ctk.CTkFrame(body, width=34, height=34, fg_color="#ffffff", corner_radius=9)
        tile.pack(side="left", anchor="n", padx=(0, 12))
        tile.pack_propagate(False)
        ctk.CTkLabel(
            tile,
            text="",
            image=icon_image("eye_closed" if recommendation.severity == "high" else "eye", 18, accent, 1.8),
            fg_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        content = ctk.CTkFrame(body, fg_color="transparent")
        content.pack(side="left", fill="x", expand=True)
        meta = ctk.CTkFrame(content, fg_color="transparent")
        meta.pack(fill="x")
        label(meta, severity_text.upper(), 10, accent, True, bg=bg if first else "#fbfcfd").pack(side="left")
        if first:
            badge = ctk.CTkFrame(meta, fg_color="#ffffff", corner_radius=8)
            badge.pack(side="left", padx=(8, 0))
            label(badge, "Ahora", 10, accent, True, bg="#ffffff").pack(padx=7, pady=1)
        label(meta, self._age(recommendation), 10, "#9aa1b2", bg=bg if first else "#fbfcfd").pack(side="right")

        label(content, recommendation.title, 14, TEXT_STRONG, True, bg=bg if first else "#fbfcfd").pack(
            anchor="w", pady=(4, 0)
        )
        label(
            content,
            recommendation.message,
            11,
            "#7d8497",
            bg=bg if first else "#fbfcfd",
            wrap=520,
        ).pack(anchor="w", pady=(3, 8))

        ctk.CTkButton(
            content,
            text="Marcar como hecha",
            command=lambda: self.after(0, lambda: self.state.complete_recommendation(recommendation.id)),
            height=34,
            width=150,
            corner_radius=7,
            fg_color="#ffffff",
            hover_color="#f4f5f9",
            border_width=1,
            border_color="#e5e8ef",
            text_color="#656d7e",
            font=fnt(10, True),
        ).pack(anchor="w")

    def _age(self, recommendation):
        seconds = max(0, int((datetime.now() - recommendation.created_at).total_seconds()))
        minutes = seconds // 60
        if minutes < 1:
            return "Hace instantes"
        if minutes < 60:
            return f"Hace {minutes} min"
        return f"Hace {minutes // 60} h"
