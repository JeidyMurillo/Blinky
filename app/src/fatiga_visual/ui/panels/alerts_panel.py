from datetime import datetime

import customtkinter as ctk

from fatiga_visual.ui.theme import MUTED, TEXT_STRONG, fnt, icon_image, label

SEVERITY = {
    "high": ("#fff3ef", "#f3d8d1", "#c96e5b", "Prioridad alta"),
    "medium": ("#fff9ec", "#f3e6c9", "#d79a3f", "Prioridad media"),
    "low": ("#eef7f2", "#d9ede2", "#3ba478", "Sugerencia"),
}


def priority_text(severity):
    return SEVERITY.get(severity, SEVERITY["low"])[3]


def alert_time(created_at, now=None):
    now = now or datetime.now()
    seconds = max(0, int((now - created_at).total_seconds()))
    minutes = seconds // 60
    if minutes < 1:
        age = "Hace instantes"
    elif minutes < 60:
        age = f"Hace {minutes} min"
    else:
        age = f"Hace {minutes // 60} h"
    return f"{created_at.strftime('%H:%M')} - {age}"


class AlertsPanel(ctk.CTkFrame):
    def __init__(self, master, state):
        super().__init__(master, fg_color="transparent")
        self.state = state
        self._signature = None

    def refresh(self):
        items = list(self.state.visible_recommendations())
        signature = tuple(
            (item.id, item.severity, item.title, item.message, item.created_at)
            for item in items
        )
        if signature == self._signature:
            return
        self._signature = signature
        for child in self.winfo_children():
            child.destroy()
        if not items:
            label(self, "Estas al dia", 14, TEXT_STRONG, True).pack(pady=(26, 4))
            label(
                self,
                "No hay alertas activas. Sigue con tus pausas.",
                11,
                MUTED,
            ).pack(pady=(0, 26))
            return
        for index, item in enumerate(items):
            self._item(item, first=index == 0)

    def _item(self, recommendation, first=False):
        bg, border, accent, severity_text = SEVERITY.get(
            recommendation.severity, SEVERITY["low"]
        )
        card = ctk.CTkFrame(
            self,
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
            image=icon_image(
                "eye_closed" if recommendation.severity == "high" else "eye",
                18,
                accent,
                1.8,
            ),
            fg_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        content = ctk.CTkFrame(body, fg_color="transparent")
        content.pack(side="left", fill="x", expand=True)
        meta = ctk.CTkFrame(content, fg_color="transparent")
        meta.pack(fill="x")
        label(meta, severity_text.upper(), 10, accent, True, bg=bg if first else "#fbfcfd").pack(
            side="left"
        )
        if first:
            badge = ctk.CTkFrame(meta, fg_color="#ffffff", corner_radius=8)
            badge.pack(side="left", padx=(8, 0))
            label(badge, "Ahora", 10, accent, True, bg="#ffffff").pack(padx=7, pady=1)
        label(
            meta,
            alert_time(recommendation.created_at),
            10,
            "#9aa1b2",
            bg=bg if first else "#fbfcfd",
        ).pack(side="right")

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

        recommendation_id = recommendation.id
        ctk.CTkButton(
            content,
            text="Descartar",
            command=lambda: self.after(
                0, lambda: self.state.dismiss_recommendation(recommendation_id)
            ),
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
