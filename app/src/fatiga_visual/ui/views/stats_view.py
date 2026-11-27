"""Interfaz 2: Estadísticas.

Qué va aquí:
- Evolución semanal de parpadeos leída desde SQLite.
- Historial de sesiones guardadas: parpadeo, exposición y alertas.
- Resumen de la sesión actual y lecturas ambientales desde AppState.
"""

import tkinter as tk
from datetime import datetime

import customtkinter as ctk

from fatiga_visual.ui.panels.ambient_panel import AmbientPanel
from fatiga_visual.ui.theme import (
    BG,
    CARD,
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
    format_clock,
    icon_image,
    label,
)

HISTORY_COLUMNS = (
    ("FECHA", 20),
    ("DURACION", 13),
    ("PARPADEOS", 14),
    ("RITMO/MIN", 13),
    ("PAUSAS", 11),
    ("ALERTAS", 11),
    ("ESTADO", 18),
)


def _parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _format_session_day(value):
    moment = _parse_iso(value)
    return moment.strftime("%d/%m %H:%M") if moment is not None else "—"


def _format_duration(session):
    if session.get("ended_at") is None:
        return "En curso"
    start = _parse_iso(session.get("started_at"))
    end = _parse_iso(session.get("ended_at"))
    if start is None or end is None:
        return "—"
    seconds = max(0, int((end - start).total_seconds()))
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}"


def _value(number, digits=0):
    if number is None:
        return "—"
    number = float(number)
    if digits:
        return f"{number:.{digits}f}"
    return str(int(round(number)))


def _configure_columns(frame):
    for index, (_title, weight) in enumerate(HISTORY_COLUMNS):
        frame.grid_columnconfigure(index, weight=weight, uniform="history")


class BlinkChart(tk.Canvas):
    def __init__(self, master):
        super().__init__(master, bg=CARD, highlightthickness=0, height=220)
        self.history = []
        self.bind("<Configure>", lambda _event: self.draw())

    def set_history(self, history):
        self.history = list(history)
        self.draw()

    def draw(self):
        self.delete("all")
        if not self.history:
            return
        width = max(self.winfo_width(), 200)
        height = max(self.winfo_height(), 120)
        left, right = 38, 18
        top, bottom = 34, 26
        plot_w = width - left - right
        plot_h = height - top - bottom
        baseline = height - bottom

        values = [value for _, value in self.history]
        peak = max(values) if values else 1
        ceiling = max(50, int((peak + 49) // 50) * 50)

        for step in range(5):
            level = ceiling * step / 4
            y = baseline - plot_h * step / 4
            self.create_line(left, y, width - right, y, fill="#eef1f6")
            self.create_text(
                left - 8,
                y,
                text=f"{int(level)}",
                anchor="e",
                fill="#a3a9b8",
                font=fnt(10),
            )

        slot = plot_w / len(self.history)
        bar_width = min(30, max(12, int(slot * 0.38)))
        for index, (day, value) in enumerate(self.history):
            x = left + slot * (index + 0.5)
            bar_h = plot_h * (value / ceiling) if ceiling else 0
            y_top = baseline - bar_h
            is_today = index == len(self.history) - 1
            color = PURPLE if is_today else "#cfc9f5"
            self.create_line(x, baseline, x, y_top, width=bar_width, capstyle=tk.ROUND, fill=color)
            self.create_text(
                x,
                y_top - 12,
                text=str(value),
                fill=TEXT_STRONG if is_today else "#9aa1b2",
                font=fnt(11, is_today),
            )
            self.create_text(
                x,
                height - 10,
                text=day,
                fill="#7d8497" if is_today else "#a3a9b8",
                font=fnt(11, is_today),
            )


class StatsView(ctk.CTkFrame):
    def __init__(self, master, state, repository=None):
        super().__init__(master, fg_color=BG)
        self.state = state
        self.repository = repository
        self._history_signature = None

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=PAD, pady=(28, 36))

        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x")
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")
        label(left, "ESTADISTICAS", 11, "#6b5ce7", True, bg=BG).pack(anchor="w")
        label(left, "Tu progreso visual", 36, TEXT, True, bg=BG).pack(anchor="w", pady=(5, 0))
        label(left, "Tendencias de parpadeo y habitos de la semana.", 14, MUTED, bg=BG).pack(
            anchor="w", pady=(7, 0)
        )

        period = ctk.CTkFrame(header, fg_color=PURPLE_SOFT, corner_radius=15)
        period.pack(side="right", anchor="s", pady=(0, 4))
        label(period, "Ultimos 7 dias", 12, "#5a4fd1", True, bg=PURPLE_SOFT).pack(padx=16, pady=6)

        grid = ctk.CTkFrame(main, fg_color="transparent")
        grid.pack(fill="both", expand=True, pady=(24, 0))
        grid.grid_columnconfigure(0, weight=2, uniform="stats")
        grid.grid_columnconfigure(1, weight=1, uniform="stats")
        grid.grid_rowconfigure(0, weight=1)

        chart_card = card_frame(grid)
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, GAP))
        top = ctk.CTkFrame(chart_card, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(18, 0))
        titles = ctk.CTkFrame(top, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "Parpadeos por dia", 15, TEXT_STRONG, True).pack(anchor="w")
        label(titles, "Datos guardados en la base local", 11, MUTED_SOFT).pack(anchor="w", pady=(3, 0))
        self.average_label = label(top, "", 12, "#39a977", True)
        self.average_label.pack(side="right", anchor="n", pady=(2, 0))

        self.chart = BlinkChart(chart_card)
        self.chart.pack(fill="both", expand=True, padx=18, pady=(12, 16))

        side = ctk.CTkFrame(grid, fg_color="transparent")
        side.grid(row=0, column=1, sticky="nsew")

        summary = card_frame(side)
        summary.pack(fill="x")
        top = ctk.CTkFrame(summary, fg_color="transparent")
        top.pack(fill="x", padx=17, pady=(17, 0))
        titles = ctk.CTkFrame(top, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "Resumen de hoy", 15, TEXT_STRONG, True).pack(anchor="w")
        label(titles, "Sesion actual", 11, MUTED_SOFT).pack(anchor="w", pady=(3, 0))

        self.summary = {}
        body = ctk.CTkFrame(summary, fg_color="transparent")
        body.pack(fill="x", padx=17, pady=(13, 17))
        rows = [
            ("clock", "Tiempo activo", "00:00:00"),
            ("clock", "Tiempo continuo", "00:00:00"),
            ("eye", "Parpadeos", "0"),
            ("chart", "Ritmo por minuto", "0"),
            ("pause", "Pausas tomadas", "0"),
            ("pause", "Ultima pausa", "—"),
        ]
        for index, (icon, title, value) in enumerate(rows):
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x", pady=(0 if index == 0 else 10, 0))
            tile = ctk.CTkFrame(row, width=30, height=30, fg_color="#f4f5f9", corner_radius=8)
            tile.pack(side="left")
            tile.pack_propagate(False)
            ctk.CTkLabel(tile, text="", image=icon_image(icon, 16, "#6b7280", 1.7), fg_color="#f4f5f9").place(
                relx=0.5, rely=0.5, anchor="center"
            )
            label(row, title, 12, MUTED).pack(side="left", padx=(10, 0))
            value_label = label(row, value, 13, TEXT_STRONG, True)
            value_label.pack(side="right")
            self.summary[title] = value_label

        self.ambient_panel = AmbientPanel(side)
        self.ambient_panel.pack(fill="x", pady=(14, 0))

        history_card = card_frame(main)
        history_card.pack(fill="x", pady=(18, 0))
        top = ctk.CTkFrame(history_card, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(16, 0))
        titles = ctk.CTkFrame(top, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "Historial de sesiones", 15, TEXT_STRONG, True).pack(anchor="w")
        label(
            titles,
            "Parpadeo, exposicion y alertas guardados en SQLite",
            11,
            MUTED_SOFT,
        ).pack(anchor="w", pady=(3, 0))
        self.history_count = label(top, "", 11, "#8b93a2")
        self.history_count.pack(side="right", anchor="n", pady=(2, 0))

        self.history_body = ctk.CTkScrollableFrame(
            history_card, fg_color=CARD, scrollbar_button_color="#e1e4eb", height=170
        )
        self.history_body.pack(fill="x", padx=12, pady=(10, 14))

        insight = card_frame(main)
        insight.pack(fill="x", pady=(18, 0))
        tile = ctk.CTkFrame(insight, width=38, height=38, fg_color="#e9f7f0", corner_radius=10)
        tile.pack(side="left", padx=(17, 13), pady=13)
        tile.pack_propagate(False)
        ctk.CTkLabel(tile, text="", image=icon_image("check", 19, "#2f9c72", 1.9), fg_color="#e9f7f0").place(
            relx=0.5, rely=0.5, anchor="center"
        )
        text = ctk.CTkFrame(insight, fg_color="transparent")
        text.pack(side="left", pady=10)
        label(text, "Vas por buen camino", 13, TEXT_STRONG, True).pack(anchor="w")
        self.insight_label = label(text, "", 11, "#7b8498")
        self.insight_label.pack(anchor="w", pady=(2, 0))
        self.insight_value = label(insight, "", 19, PURPLE, True)
        self.insight_value.pack(side="right", padx=20)

        self.refresh()

    def _daily_history(self):
        if self.repository is None:
            return list(self.state.blink_history)
        try:
            rows = self.repository.daily_blinks(days=7)
        except Exception:
            return []
        return [
            (str(row["day"])[5:], int(row["max_blinks"] or 0))
            for row in rows
        ]

    def _history_signature_of(self, sessions):
        return tuple(
            (
                row.get("id"),
                row.get("started_at"),
                row.get("ended_at"),
                row.get("blinks"),
                row.get("avg_blink_rate"),
                row.get("breaks_taken"),
                row.get("alerts"),
                row.get("current"),
            )
            for row in sessions
        )

    def _history_row(self, session, index):
        background = "#f9fafe" if index % 2 else CARD
        row = ctk.CTkFrame(self.history_body, fg_color=background, corner_radius=8)
        row.pack(fill="x", pady=1)
        _configure_columns(row)
        values = (
            _format_session_day(session.get("started_at")),
            _format_duration(session),
            _value(session.get("blinks")),
            _value(session.get("avg_blink_rate"), 1),
            _value(session.get("breaks_taken")),
            _value(session.get("alerts")),
            "Actual" if session.get("current") else "Guardada",
        )
        for column, value in enumerate(values):
            is_current = column == 6 and session.get("current")
            color = PURPLE if is_current else TEXT_STRONG if column in (0, 6) else MUTED
            label(row, value, 11, color, bool(session.get("current")) or column == 0, bg=background).grid(
                row=0, column=column, sticky="w", padx=(8, 4), pady=7
            )

    def _render_history(self, sessions):
        signature = self._history_signature_of(sessions)
        if signature == self._history_signature:
            return
        self._history_signature = signature

        for child in self.history_body.winfo_children():
            child.destroy()

        header_bg = "#f1f3f9"
        header = ctk.CTkFrame(self.history_body, fg_color=header_bg, corner_radius=8)
        header.pack(fill="x", pady=(0, 4))
        _configure_columns(header)
        for column, (title, _weight) in enumerate(HISTORY_COLUMNS):
            label(header, title, 9, MUTED, True, bg=header_bg).grid(
                row=0, column=column, sticky="w", padx=(8, 4), pady=6
            )

        if not sessions:
            empty = ctk.CTkFrame(self.history_body, fg_color="#fafbfe", corner_radius=10)
            empty.pack(fill="x", pady=4)
            message = (
                "Todavia no hay sesiones guardadas."
                if self.repository is not None
                else "Almacenamiento desactivado."
            )
            label(empty, message, 12, MUTED, bg="#fafbfe").pack(pady=16)
            return

        for index, session in enumerate(sessions):
            self._history_row(session, index)

    def refresh(self, topic=None):
        history = self._daily_history()
        self.chart.set_history(history)
        if history:
            average = sum(value for _, value in history) / len(history)
            self.average_label.configure(text=f"Promedio {average:.0f} al dia")
        else:
            self.average_label.configure(text="Sin datos guardados")

        sessions = []
        if self.repository is not None:
            try:
                sessions = self.repository.session_history(limit=20)
            except Exception:
                sessions = []
        self._render_history(sessions)
        self.history_count.configure(
            text=f"{len(sessions)} sesiones guardadas" if self.repository else "Sin almacenamiento"
        )

        self.summary["Tiempo activo"].configure(text=format_clock(self.state.session_seconds))
        self.summary["Tiempo continuo"].configure(
            text=format_clock(self.state.continuous_seconds)
        )
        self.summary["Parpadeos"].configure(text=str(self.state.blinks))
        self.summary["Ritmo por minuto"].configure(text=f"{self.state.blink_rate:.0f}")
        self.summary["Pausas tomadas"].configure(text=str(self.state.exposure.breaks_taken))
        last_break = getattr(self.state, "last_break", None)
        self.summary["Ultima pausa"].configure(
            text=(
                format_clock(int(getattr(last_break, "duration_seconds", 0)))
                if last_break is not None
                else "—"
            )
        )
        self.ambient_panel.refresh(self.state.ambient)

        continuous = self.state.exposure.continuous_seconds // 60
        self.insight_label.configure(
            text=(
                f"Llevas {continuous} minutos de trabajo continuo. "
                "Una pausa corta mantiene tu vista descansada."
            )
        )
        self.insight_value.configure(text=f"{self.state.blinks} parpadeos")
