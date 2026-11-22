"""Vista de la camara en vivo.

Qué va aquí:
- Presentar el feed 880x480 con overlay y estados off/connecting/on/error.
- Consultar vision.camera.CameraStream desde el hilo de Tk con after().
- Dibujar los landmarks que el pipeline publica en AppState.face_overlay; si no
  hay rostro, mostrar una guía genérica.
- Avisar a la vista cuando la camara se pierde.

No abrir cv2 aquí: toda la captura pertenece a vision.camera.
"""

import math

import customtkinter as ctk
from PIL import Image, ImageDraw

from fatiga_visual.ui.theme import (
    CARD,
    FEED_H,
    FEED_W,
    PURPLE,
    PURPLE_DARK,
    fnt,
    pil_font,
    render_icon,
)
from fatiga_visual.vision.camera import CameraStream
from fatiga_visual.vision.overlay import project_overlay


class CameraWidget(ctk.CTkFrame):
    def __init__(self, master, on_toggle, stream=None, state=None):
        super().__init__(master, width=FEED_W, height=FEED_H, fg_color="#1b2130", corner_radius=11)
        self.pack_propagate(False)
        self.on_toggle = on_toggle
        self.on_lost = None
        self.stream = stream or CameraStream()
        self.state = state
        self._state = "off"
        self._on_ready = None
        self._start_job = None
        self._render_job = None
        self._last_seq = 0
        self._dead_reported = False

        self._radial = self._radial_mask(FEED_W, FEED_H)
        self._round_mask = Image.new("L", (FEED_W, FEED_H), 0)
        ImageDraw.Draw(self._round_mask).rounded_rectangle(
            [0, 0, FEED_W - 1, FEED_H - 1], radius=11, fill=255
        )
        self.image_open = self._make_image("off")
        self.image_connecting = self._make_image("connecting")
        self.image_error = self._make_image("error")
        self.image_active = self._make_image("on")
        self.live_image = ctk.CTkImage(
            light_image=self.image_active.cget("light_image"),
            dark_image=self.image_active.cget("dark_image"),
            size=(FEED_W, FEED_H),
        )
        self.live_overlay = self._make_live_overlay()

        self.canvas_label = ctk.CTkLabel(self, text="", image=self.image_open, fg_color="transparent")
        self.canvas_label.pack(fill="both", expand=True)
        self.placeholder_button = ctk.CTkButton(
            self,
            text="Activar camara",
            command=on_toggle,
            height=38,
            width=142,
            corner_radius=8,
            fg_color=PURPLE,
            hover_color=PURPLE_DARK,
            text_color="#ffffff",
            font=fnt(11, True),
        )
        self.placeholder_button.place(relx=0.5, rely=0.5, anchor="center", y=59)

    @property
    def state_name(self):
        return self._state

    def _radial_mask(self, width, height):
        small = Image.new("L", (160, 160), 0)
        pixels = small.load()
        for y in range(160):
            for x in range(160):
                dist = math.sqrt(((x - 80) / 80) ** 2 + ((y - 80) / 80) ** 2)
                pixels[x, y] = int(44 * max(0.0, 1 - dist) ** 2)
        return small.resize((width, height), Image.BILINEAR)

    def _make_image(self, mode):
        width, height = FEED_W, FEED_H
        cx, cy = width / 2, height / 2
        base = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(base)
        top = (37, 43, 59)
        bottom = (21, 25, 35)
        for y in range(height):
            t = y / (height - 1)
            draw.line(
                [(0, y), (width, y)],
                fill=(
                    int(top[0] + (bottom[0] - top[0]) * t),
                    int(top[1] + (bottom[1] - top[1]) * t),
                    int(top[2] + (bottom[2] - top[2]) * t),
                ),
            )
        base = Image.composite(Image.new("RGB", (width, height), (121, 107, 224)), base, self._radial)

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)

        if mode == "on":
            od.ellipse(
                [cx - width * 0.195, cy - height * 0.32, cx + width * 0.195, cy + height * 0.32],
                outline=(117, 244, 195, 205),
                width=2,
            )
            od.text(
                (cx, cy + height * 0.32 + 20),
                "Rostro detectado",
                font=pil_font(9, True),
                fill=(107, 229, 182, 235),
                anchor="mm",
            )
        else:
            od.rounded_rectangle([cx - 35, cy - 105, cx + 35, cy - 35], radius=22, fill=(255, 255, 255, 26))
            camera_icon = render_icon("camera", 46, (255, 255, 255, 228), 1.8)
            overlay.alpha_composite(camera_icon, (int(cx - 23), int(cy - 93)))
            if mode == "connecting":
                title = "Conectando con la camara"
                detail = "Un momento, estamos iniciando el video."
            elif mode == "error":
                title = "No se pudo acceder a la camara"
                detail = "Revisa los permisos y que no este en uso."
            else:
                title = "La camara esta desactivada"
                detail = "Activala para comenzar la deteccion ocular."
            od.text(
                (cx, cy - 12),
                title,
                font=pil_font(14, True),
                fill=(255, 255, 255, 255),
                anchor="mm",
            )
            od.text(
                (cx, cy + 9),
                detail,
                font=pil_font(11, False),
                fill=(169, 175, 191, 255),
                anchor="mm",
            )

        if mode == "on":
            dot, status, right = (67, 220, 156, 255), "CAMARA CONECTADA", "720p - 30 FPS"
        elif mode == "connecting":
            dot, status, right = (235, 154, 74, 255), "CONECTANDO CAMARA", "-"
        elif mode == "error":
            dot, status, right = (201, 110, 91, 255), "CAMARA NO DISPONIBLE", "-"
        else:
            dot, status, right = (235, 154, 74, 255), "CAMARA EN ESPERA", "720p - 30 FPS"

        od.ellipse([14, 21, 21, 28], fill=dot)
        od.text(
            (30, 24.5),
            status,
            font=pil_font(9, True),
            fill=(205, 210, 220, 225),
            anchor="lm",
        )
        od.text(
            (width - 15, 24.5),
            right,
            font=pil_font(9, False),
            fill=(190, 196, 208, 200),
            anchor="rm",
        )

        composed = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
        result = Image.new("RGB", (width, height), CARD)
        result.paste(composed, (0, 0), self._round_mask)
        return ctk.CTkImage(light_image=result, dark_image=result, size=(width, height))

    def _make_live_overlay(self):
        width, height = FEED_W, FEED_H
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        for y in range(92):
            draw.line(
                [(0, y), (width, y)],
                fill=(10, 14, 22, int(115 * (1 - y / 92) ** 1.4)),
            )
        for y in range(height - 76, height):
            t = (y - (height - 76)) / 76
            draw.line(
                [(0, y), (width, y)],
                fill=(10, 14, 22, int(65 * t ** 1.3)),
            )
        draw.ellipse([14, 21, 21, 28], fill=(67, 220, 156, 255))
        draw.text(
            (30, 24.5),
            "CAMARA CONECTADA",
            font=pil_font(9, True),
            fill=(225, 230, 239, 235),
            anchor="lm",
        )
        return overlay

    def _draw_face_guide(self, draw):
        """Guía genérica cuando no hay landmarks (fuente simulada o sin rostro)."""
        cx, cy = FEED_W / 2, FEED_H / 2
        draw.ellipse(
            [
                cx - FEED_W * 0.195,
                cy - FEED_H * 0.32,
                cx + FEED_W * 0.195,
                cy + FEED_H * 0.32,
            ],
            outline=(117, 244, 195, 190),
            width=2,
        )
        draw.text(
            (cx, cy + FEED_H * 0.32 + 20),
            "Rostro detectado",
            font=pil_font(9, True),
            fill=(122, 240, 194, 240),
            anchor="mm",
        )

    def _draw_landmarks(self, draw, overlay, source_w, source_h):
        """Dibuja contorno facial, ojos e iris sobre el feed ya recortado."""
        points = project_overlay(overlay, source_w, source_h, FEED_W, FEED_H)
        oval = points["oval"]
        if len(oval) > 2:
            draw.line(list(oval) + [oval[0]], fill=(117, 244, 195, 200), width=2)
        for key in ("left_eye", "right_eye"):
            eye = points[key]
            if len(eye) > 2:
                draw.line(list(eye) + [eye[0]], fill=(126, 214, 255, 235), width=2)
        for x, y in points["irises"]:
            draw.ellipse(
                [x - 3, y - 3, x + 3, y + 3],
                fill=(255, 255, 255, 235),
                outline=(117, 244, 195, 255),
                width=1,
            )
        if oval:
            bottom = max(y for _, y in oval)
            draw.text(
                (FEED_W / 2, min(FEED_H - 16, bottom + 20)),
                "Rostro detectado",
                font=pil_font(9, True),
                fill=(122, 240, 194, 240),
                anchor="mm",
            )

    def _compose_live(self, rgb, fps, overlay=None):
        source_h, source_w = rgb.shape[:2]
        frame = Image.fromarray(rgb)
        scale = max(FEED_W / source_w, FEED_H / source_h)
        new_w = max(FEED_W, round(source_w * scale))
        new_h = max(FEED_H, round(source_h * scale))
        frame = frame.resize((new_w, new_h), Image.BILINEAR)
        left = (new_w - FEED_W) // 2
        top = (new_h - FEED_H) // 2
        frame = frame.crop((left, top, left + FEED_W, top + FEED_H)).convert("RGBA")
        frame = Image.alpha_composite(frame, self.live_overlay)
        draw = ImageDraw.Draw(frame, "RGBA")
        if overlay is not None and getattr(overlay, "visible", False):
            self._draw_landmarks(draw, overlay, source_w, source_h)
        else:
            self._draw_face_guide(draw)
        fps_text = f"{source_h}p - {max(1, round(fps or 30))} FPS"
        draw.text(
            (FEED_W - 15, 24.5),
            fps_text,
            font=pil_font(9, False),
            fill=(225, 230, 239, 220),
            anchor="rm",
        )
        composed = frame.convert("RGB")
        result = Image.new("RGB", (FEED_W, FEED_H), CARD)
        result.paste(composed, (0, 0), self._round_mask)
        return result

    def set_state(self, state):
        self._state = state
        if state == "on":
            self.canvas_label.configure(image=self.live_image)
            self.placeholder_button.place_forget()
        elif state == "connecting":
            self.canvas_label.configure(image=self.image_connecting)
            self.placeholder_button.place_forget()
        elif state == "error":
            self.canvas_label.configure(image=self.image_error)
            self.placeholder_button.configure(text="Reintentar")
            self.placeholder_button.place(relx=0.5, rely=0.5, anchor="center", y=59)
        else:
            self.canvas_label.configure(image=self.image_open)
            self.placeholder_button.configure(text="Activar camara")
            self.placeholder_button.place(relx=0.5, rely=0.5, anchor="center", y=59)

    def start(self, on_ready):
        if self.stream.state() in (CameraStream.STARTING, CameraStream.RUNNING):
            return
        self._on_ready = on_ready
        self._dead_reported = False
        self._last_seq = 0
        if self.state is not None and hasattr(self.state, "clear_face_overlay"):
            self.state.clear_face_overlay()
        self.live_image.configure(
            light_image=self.image_active.cget("light_image"),
            dark_image=self.image_active.cget("dark_image"),
        )
        self.stream.start()
        self._start_job = self.after(60, self._poll_start)

    def _poll_start(self):
        self._start_job = None
        state = self.stream.state()
        if state == CameraStream.STARTING:
            self._start_job = self.after(60, self._poll_start)
            return
        if state == CameraStream.RUNNING:
            self._state = "on"
            self.canvas_label.configure(image=self.live_image)
            self.placeholder_button.place_forget()
            self._render_job = self.after(15, self._render_tick)
            ok, message = True, ""
        else:
            ok, message = False, self.stream.message()
        callback = self._on_ready
        self._on_ready = None
        if callback is not None:
            callback(ok, message)

    def _render_tick(self):
        self._render_job = None
        seq, rgb, fps = self.stream.read_frame()
        if rgb is not None and seq != self._last_seq:
            self._last_seq = seq
            overlay = getattr(self.state, "face_overlay", None) if self.state else None
            frame = self._compose_live(rgb, fps, overlay)
            self.live_image.configure(light_image=frame, dark_image=frame)
        if self.stream.state() == CameraStream.ERROR:
            if not self._dead_reported:
                self._dead_reported = True
                if self.on_lost is not None:
                    self.on_lost(self.stream.message())
            return
        self._render_job = self.after(15, self._render_tick)

    def stop(self):
        for attribute in ("_start_job", "_render_job"):
            job = getattr(self, attribute)
            if job is not None:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
                setattr(self, attribute, None)
        self.stream.stop()
        if self.state is not None and hasattr(self.state, "clear_face_overlay"):
            self.state.clear_face_overlay()
        self._last_seq = 0
        self._dead_reported = False
        self._on_ready = None
