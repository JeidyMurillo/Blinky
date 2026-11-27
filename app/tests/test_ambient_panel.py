import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.models import AmbientReading
from fatiga_visual.ui.panels.ambient_panel import AmbientPanel, AmbientStrip


class FakeLabel:
    """Sustituye a CTkLabel para probar refresh() sin abrir una ventana."""

    def __init__(self):
        self.text = ""
        self.fg = ""

    def configure(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]
        if "fg" in kwargs:
            self.fg = kwargs["fg"]


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


class AmbientStripTests(unittest.TestCase):
    def _strip(self):
        strip = AmbientStrip.__new__(AmbientStrip)
        strip.settings = None
        strip.temperature = FakeLabel()
        strip.temperature_note = FakeLabel()
        strip.humidity = FakeLabel()
        strip.humidity_note = FakeLabel()
        strip.lux = FakeLabel()
        strip.lux_note = FakeLabel()
        return strip

    def test_strip_shows_all_three_sensor_values(self):
        strip = self._strip()
        reading = AmbientReading(
            timestamp=datetime(2026, 1, 1, 12, 0, 0),
            lux=420.0,
            temperature_c=23.4,
            humidity=48.0,
            connected=True,
        )

        strip.refresh(reading)

        self.assertEqual(strip.temperature.text, "23.4")
        self.assertEqual(strip.humidity.text, "48")
        self.assertEqual(strip.lux.text, "420")
        self.assertEqual(strip.temperature_note.text, "Óptima")
        self.assertEqual(strip.humidity_note.text, "Confortable")
        self.assertEqual(strip.lux_note.text, "Adecuada")

    def test_strip_without_node_shows_placeholders(self):
        strip = self._strip()

        strip.refresh(None)

        self.assertEqual(strip.temperature.text, "--")
        self.assertEqual(strip.humidity.text, "--")
        self.assertEqual(strip.lux.text, "--")
        self.assertEqual(strip.temperature_note.text, "Sin datos")
        self.assertEqual(strip.humidity_note.text, "Sin datos")
        self.assertEqual(strip.lux_note.text, "Sin datos")

    def test_strip_marks_readings_outside_configured_range(self):
        strip = self._strip()
        reading = AmbientReading(
            timestamp=datetime(2026, 1, 1, 12, 0, 0),
            lux=60.0,
            temperature_c=31.0,
            humidity=75.0,
            connected=True,
        )

        strip.refresh(reading)

        self.assertEqual(strip.temperature_note.text, "Fuera de rango")
        self.assertEqual(strip.humidity_note.text, "Fuera de rango")
        self.assertEqual(strip.lux_note.text, "Fuera de rango")

    def test_strip_keeps_last_values_when_node_is_offline(self):
        strip = self._strip()
        reading = AmbientReading(
            timestamp=datetime(2026, 1, 1, 12, 0, 0),
            lux=420.0,
            temperature_c=23.4,
            humidity=48.0,
            connected=False,
        )

        strip.refresh(reading)

        self.assertEqual(strip.temperature.text, "23.4")
        self.assertEqual(strip.humidity.text, "48")
        self.assertEqual(strip.lux.text, "420")
        self.assertEqual(strip.temperature_note.text, "Sin señal")
        self.assertEqual(strip.humidity_note.text, "Sin señal")
        self.assertEqual(strip.lux_note.text, "Sin señal")


if __name__ == "__main__":
    unittest.main()
