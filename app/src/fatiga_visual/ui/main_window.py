"""Ventana principal: barra, navegacion entre las 3 interfaces y reloj global.

Contenido:
- Marco sin bordes de 1512x1000 centrado, arrastrable y con controles.
- Pestanas Monitoreo / Estadisticas / Recomendaciones.
- Tick de 1 segundo que avanza AppState y anima el parpadeo simulado.
"""

import ctypes
import os

import customtkinter as ctk

from fatiga_visual.ui.state import AppState
from fatiga_visual.ui.theme import (
    BG,
    TEXT_STRONG,
    bind_tree,
    fnt,
    get_work_area,
    icon_image,
    label,
)
from fatiga_visual.ui.views.main_view import MainView
from fatiga_visual.ui.views.recommendations_view import RecommendationsView
from fatiga_visual.ui.views.stats_view import StatsView

TABS = (
    ("monitoring", "Monitoreo"),
    ("stats", "Estadisticas"),
    ("recommendations", "Recomendaciones"),
)

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020


class MainWindow(ctk.CTk):
    def __init__(self, state: AppState, repository=None):
        super().__init__(fg_color=BG)
        self.app_state = state
        self.repository = repository
        self.title("Blinky")
        self.overrideredirect(True)
        self.resizable(False, False)
        left, top, right, bottom = get_work_area()
        x = left + (right - left - 1512) // 2
        y = top + (bottom - top - 1000) // 2
        self._normal_geometry = f"1512x1000+{x}+{y}"
        self.geometry(self._normal_geometry)
        self.configure(fg_color=BG)

        self._views = {}
        self._current = None
        self._tab_buttons = {}
        self._drag_offset = (0, 0)
        self._tick_job = None
        self._poll_job = None
        self._pending_borderless = False

        self.protocol("WM_DELETE_WINDOW", self._close)
        self.bind("<Map>", self._on_map)
        self._build_bar()
        self._content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self._content.pack(fill="both", expand=True)

        self.show("monitoring")
        self._tick_job = self.after(1000, self._tick)
        self._poll_job = self.after(100, self._poll_state)

    def _build_bar(self):
        bar = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=0, height=50)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        brand = ctk.CTkFrame(bar, fg_color="transparent")
        brand.pack(side="left", padx=20)

        mark = ctk.CTkFrame(brand, width=32, height=32, fg_color="#6357dc", corner_radius=9)
        mark.pack(side="left", padx=(0, 10))
        mark.pack_propagate(False)
        ctk.CTkLabel(
            mark, text="", image=icon_image("eye", 21, "#ffffff", 1.8), fg_color="#6357dc"
        ).place(relx=0.5, rely=0.5, anchor="center")

        label(brand, "Blinky", 15, TEXT_STRONG, True, bg="#ffffff").pack(side="left")
        separator = ctk.CTkFrame(brand, width=1, height=18, fg_color="#dde1e9", corner_radius=0)
        separator.pack(side="left", padx=9)
        label(brand, "Monitor de fatiga ocular", 13, "#667087", bg="#ffffff").pack(side="left")

        nav = ctk.CTkFrame(bar, fg_color="transparent")
        nav.pack(side="left", padx=(26, 0))
        for key, text in TABS:
            button = ctk.CTkButton(
                nav,
                text=text,
                command=lambda selected=key: self.show(selected),
                height=38,
                width=126 if key != "recommendations" else 168,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#f2f2f8",
                text_color="#6b7385",
                font=fnt(12, True),
            )
            button.pack(side="left", padx=(0, 4))
            self._tab_buttons[key] = button

        controls = ctk.CTkFrame(bar, fg_color="transparent", corner_radius=0)
        controls.pack(side="right", fill="y")
        ctk.CTkButton(
            controls,
            text="",
            image=icon_image("minimize", 19, "#667087", 1.9),
            command=self._minimize,
            width=52,
            height=50,
            corner_radius=0,
            fg_color="transparent",
            hover_color="#edf0f5",
        ).pack(side="left")
        ctk.CTkButton(
            controls,
            text="",
            image=icon_image("close", 18, "#667087", 1.9),
            command=self._close,
            width=52,
            height=50,
            corner_radius=0,
            fg_color="transparent",
            hover_color="#e85555",
        ).pack(side="left")

        border = ctk.CTkFrame(self, height=1, fg_color="#e4e8f1", corner_radius=0)
        border.pack(fill="x")

        self._make_draggable(brand)

    def _make_view(self, key):
        if key == "monitoring":
            return MainView(
                self._content,
                self.app_state,
                on_stats=lambda: self.show("stats"),
                on_recommendations=lambda: self.show("recommendations"),
            )
        if key == "stats":
            return StatsView(self._content, self.app_state, repository=self.repository)
        return RecommendationsView(self._content, self.app_state)

    def show(self, key):
        if self._current == key:
            return
        if self._current is not None:
            self._views[self._current].pack_forget()
        if key not in self._views:
            self._views[key] = self._make_view(key)
        self._current = key
        self._views[key].pack(fill="both", expand=True)
        self._views[key].refresh()
        self._update_tabs()

    def _update_tabs(self):
        for key, button in self._tab_buttons.items():
            if key == self._current:
                button.configure(fg_color="#eeecff", text_color="#5a4fd1", hover_color="#e9e7ff")
            else:
                button.configure(fg_color="transparent", text_color="#6b7385", hover_color="#f2f2f8")

    def _on_state(self, topic):
        current = self._views.get(self._current)
        if current is not None:
            current.refresh(topic)

    def _poll_state(self):
        self._poll_job = None
        try:
            seen = set()
            for topic in self.app_state.drain_events():
                if topic in seen:
                    continue
                seen.add(topic)
                self._on_state(topic)
                if topic == "blink":
                    self.after(180, self.app_state.release_blink_visual)
        finally:
            self._poll_job = self.after(100, self._poll_state)

    def _tick(self):
        self._tick_job = None
        try:
            if self.app_state.tick():
                self.after(180, self.app_state.finish_blink)
        finally:
            self._tick_job = self.after(1000, self._tick)

    def _make_draggable(self, widget):
        bind_tree(widget, "<ButtonPress-1>", self._drag_start)
        bind_tree(widget, "<B1-Motion>", self._drag_move)

    def _drag_start(self, event):
        self._drag_offset = (event.x_root - self.winfo_x(), event.y_root - self.winfo_y())

    def _drag_move(self, event):
        x = event.x_root - self._drag_offset[0]
        y = event.y_root - self._drag_offset[1]
        self.geometry(f"+{x}+{y}")
        self._normal_geometry = f"1512x1000+{x}+{y}"

    def _window_handle(self):
        user32 = ctypes.windll.user32
        user32.GetAncestor.restype = ctypes.c_void_p
        user32.GetAncestor.argtypes = (ctypes.c_void_p, ctypes.c_uint)
        user32.GetWindowLongW.restype = ctypes.c_long
        user32.GetWindowLongW.argtypes = (ctypes.c_void_p, ctypes.c_int)
        user32.SetWindowLongW.restype = ctypes.c_long
        user32.SetWindowLongW.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_long)
        user32.SetWindowPos.argtypes = (
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint,
        )
        handle = user32.GetAncestor(self.winfo_id(), 2)
        return handle or self.winfo_id(), user32

    def _ensure_taskbar_entry(self):
        if os.name != "nt":
            return
        try:
            handle, user32 = self._window_handle()
            style = user32.GetWindowLongW(handle, GWL_EXSTYLE)
            style = (style | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
            user32.SetWindowLongW(handle, GWL_EXSTYLE, style)
            user32.SetWindowPos(
                handle,
                0,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
            )
        except Exception:
            pass

    def _minimize(self):
        # Una ventana overrideredirect NO tiene botón en la barra de tareas:
        # si se iconifica directamente queda inaccesible. Se vuelve normal,
        # se le asegura entrada en la barra y entonces sí se iconifica.
        if os.name == "nt":
            self.overrideredirect(False)
            self.update_idletasks()
            self._ensure_taskbar_entry()
        self._pending_borderless = True
        self.iconify()

    def _on_map(self, event):
        if self._pending_borderless:
            self.after_idle(self._restore_borderless)

    def _restore_borderless(self):
        if not self._pending_borderless:
            return
        if self.state() != "normal":
            self.after(100, self._restore_borderless)
            return
        self._pending_borderless = False
        self.overrideredirect(True)
        self.geometry(self._normal_geometry)
        self._ensure_taskbar_entry()
        self.lift()
        self.focus_force()

    def _close(self):
        self.destroy()

    def destroy(self):
        for attribute in ("_tick_job", "_poll_job"):
            job = getattr(self, attribute)
            if job is not None:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
                setattr(self, attribute, None)
        for view in list(self._views.values()):
            try:
                view.destroy()
            except Exception:
                pass
        self._views.clear()
        super().destroy()
