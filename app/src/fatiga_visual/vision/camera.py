"""Captura de la webcam en segundo plano.

Qué va aquí:
- Abrir/cerrar la cámara física y liberar el dispositivo al apagar.
- Exponer el último fotograma RGB sin bloquear la interfaz.

La UI (ui/widgets/camera_widget.py) solo consulta state(), read_frame() y fps.
"""

import os
import threading
import time

try:
    import cv2
except Exception:
    cv2 = None


class CameraStream:
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"

    def __init__(self, index=0, width=1280, height=720, fps=30):
        self.index = index
        self.width = width
        self.height = height
        self.target_fps = fps
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None
        self._state = self.IDLE
        self._message = ""
        self._latest_rgb = None
        self._seq = 0
        self._measured_fps = 0.0

    def state(self):
        with self._lock:
            return self._state

    def message(self):
        with self._lock:
            return self._message

    def read_frame(self):
        with self._lock:
            return self._seq, self._latest_rgb, self._measured_fps

    def start(self):
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._state = self.STARTING
            self._message = ""
            self._latest_rgb = None
            self._seq = 0
            self._measured_fps = 0.0
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        thread = self._thread
        self._thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.5)
        with self._lock:
            self._state = self.IDLE
            self._message = ""
            self._latest_rgb = None
            self._seq = 0
            self._measured_fps = 0.0

    def _set_state(self, state, message=""):
        with self._lock:
            self._state = state
            self._message = message

    def _worker(self):
        cap = None
        try:
            if cv2 is None:
                raise RuntimeError("OpenCV no está instalado")
            backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
            cap = cv2.VideoCapture(self.index, backend)
            if not cap.isOpened():
                raise RuntimeError("No se pudo abrir la cámara")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if self._stop_event.is_set():
                return
            frame = None
            for _ in range(10):
                ok, candidate = cap.read()
                if ok:
                    frame = candidate
                    break
                time.sleep(0.03)
            if frame is None:
                raise RuntimeError("La cámara no entregó imagen")
            with self._lock:
                self._latest_rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
                self._seq += 1
                self._state = self.RUNNING
                self._message = ""
            self._read_loop(cap)
        except Exception as exc:
            if not self._stop_event.is_set():
                self._set_state(self.ERROR, str(exc))
        finally:
            if cap is not None:
                cap.release()

    def _read_loop(self, cap):
        last = time.perf_counter()
        count = 0
        failures = 0
        while not self._stop_event.is_set():
            ok, frame = cap.read()
            if not ok:
                failures += 1
                if failures >= 30:
                    self._set_state(self.ERROR, "Se perdió la conexión con la cámara")
                    return
                time.sleep(0.03)
                continue
            failures = 0
            rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
            with self._lock:
                self._latest_rgb = rgb
                self._seq += 1
            count += 1
            now = time.perf_counter()
            if now - last >= 0.5:
                with self._lock:
                    self._measured_fps = count / (now - last)
                last = now
                count = 0
