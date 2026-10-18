import json
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).parents[1]
RESULT = ROOT / "tests" / "fixtures" / "rayforge-lightburn-mopa-import.json"
SOURCE = ROOT / "tests" / "fixtures" / "synthetic-mopa-import.lbrn2"


class RayforgeLightBurnImportSpikeTests(unittest.TestCase):
    def test_public_fixture_is_small_and_synthetic(self):
        root = ET.fromstring(SOURCE.read_bytes())
        self.assertEqual("synthetic-public-fixture", root.get("AppVersion"))
        self.assertEqual(1, len(root.findall("Shape")))
        self.assertNotIn("serial", SOURCE.read_text(encoding="utf-8").lower())

    def test_observed_values_survive_raw_import(self):
        result = json.loads(RESULT.read_text(encoding="utf-8"))
        self.assertIsNone(result["transport"])
        self.assertEqual(40000, result["raw_cut_setting"]["frequency"])
        self.assertEqual(0.5, result["mapped_layer_settings"]["power"])
        self.assertEqual(15000, result["mapped_layer_settings"]["cut_speed"])
        self.assertEqual([54.0, 54.0, 56.0, 56.0], result["geometry_bounds_mm"])

    def test_incomplete_mopa_import_fails_the_encoding_gate(self):
        result = json.loads(RESULT.read_text(encoding="utf-8"))
        survival = result["mopa_survival"]
        self.assertTrue(survival["frequency_preserved_in_source_metadata"])
        self.assertFalse(survival["frequency_mapped_to_workflow"])
        self.assertFalse(survival["pulse_width_source_field_observed"])
        self.assertFalse(survival["pulse_width_mapped_to_workflow"])
        self.assertFalse(survival["safe_for_jcz_encoding"])


if __name__ == "__main__":
    unittest.main()
