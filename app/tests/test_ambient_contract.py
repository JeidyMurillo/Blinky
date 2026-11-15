import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.ambient.mqtt_client import parse_reading, reading_from_mapping

ROOT = Path(__file__).resolve().parents[2]


class AmbientContractTests(unittest.TestCase):
    def test_schema_file_is_valid_json(self):
        schema = json.loads((ROOT / "contracts" / "ambient.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["title"], "AmbientReading")
        self.assertEqual(set(schema["required"]), {"lux", "temperature", "humidity"})

    def test_valid_payload(self):
        reading = reading_from_mapping(
            {"lux": 420.5, "temperature": 23.4, "humidity": 48.0, "seq": 7}
        )
        self.assertAlmostEqual(reading.lux, 420.5)
        self.assertAlmostEqual(reading.temperature_c, 23.4)
        self.assertAlmostEqual(reading.humidity, 48.0)
        self.assertTrue(reading.connected)

    def test_parse_bytes_payload(self):
        reading = parse_reading(b'{"lux": 100, "temperature": 22, "humidity": 50}')
        self.assertAlmostEqual(reading.lux, 100.0)

    def test_missing_field_is_rejected(self):
        with self.assertRaises(ValueError):
            reading_from_mapping({"lux": 420, "temperature": 23.4})

    def test_unknown_field_is_rejected(self):
        with self.assertRaises(ValueError):
            reading_from_mapping(
                {"lux": 420, "temperature": 23.4, "humidity": 48, "extra": 1}
            )

    def test_out_of_range_is_rejected(self):
        with self.assertRaises(ValueError):
            reading_from_mapping({"lux": -1, "temperature": 23.4, "humidity": 48})
        with self.assertRaises(ValueError):
            reading_from_mapping({"lux": 420, "temperature": 23.4, "humidity": 120})

    def test_non_numeric_is_rejected(self):
        with self.assertRaises(ValueError):
            reading_from_mapping({"lux": "420", "temperature": 23.4, "humidity": 48})
        with self.assertRaises(ValueError):
            reading_from_mapping({"lux": True, "temperature": 23.4, "humidity": 48})

    def test_nan_is_rejected(self):
        with self.assertRaises(ValueError):
            reading_from_mapping({"lux": float("nan"), "temperature": 23.4, "humidity": 48})


if __name__ == "__main__":
    unittest.main()
