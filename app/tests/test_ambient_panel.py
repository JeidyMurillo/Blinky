import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.models import AmbientReading
from fatiga_visual.ui.panels.ambient_panel import AmbientPanel


class FakeLabel:
    """Sustituye a CTkLabel para probar refresh() sin abrir una ventana."""

    def __init__(self):
        self.text = ""

    def configure(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]


class AmbientPanelTests(unittest.TestCase):
    def _panel(self):
        # __new__ evita construir widgets Tk: solo necesitamos las etiquetas.
        panel = AmbientPanel.__new__(AmbientPanel)
        panel.temperature = FakeLabel()
        panel.lux = FakeLabel()
        panel.humidity = FakeLabel()
        panel.status = FakeLabel()
        return panel

    def test_shows_humidity_next_to_temperature_and_lux(self):
        panel = self._panel()
        reading = AmbientReading(
            timestamp=datetime(2026, 1, 1, 12, 0, 0),
            lux=420.0,
            temperature_c=23.4,
            humidity=48.0,
            connected=True,
        )

        panel.refresh(reading)

        self.assertEqual(panel.temperature.text, "23.4")
        self.assertEqual(panel.lux.text, "420")
        self.assertEqual(panel.humidity.text, "48")
        self.assertEqual(panel.status.text, "Conectado")

    def test_missing_node_shows_placeholders(self):
        panel = self._panel()

        panel.refresh(None)

        self.assertEqual(panel.temperature.text, "--")
        self.assertEqual(panel.lux.text, "--")
        self.assertEqual(panel.humidity.text, "--")
        self.assertEqual(panel.status.text, "Sin datos")

    def test_disconnected_node_shows_placeholders(self):
        panel = self._panel()
        reading = AmbientReading(
            timestamp=datetime(2026, 1, 1, 12, 0, 0),
            lux=420.0,
            temperature_c=23.4,
            humidity=48.0,
            connected=False,
        )

        panel.refresh(reading)

        self.assertEqual(panel.humidity.text, "--")
        self.assertEqual(panel.status.text, "Sin datos")


if __name__ == "__main__":
    unittest.main()
