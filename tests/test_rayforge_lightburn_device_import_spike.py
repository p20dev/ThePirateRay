import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
RESULT = ROOT / "tests" / "fixtures" / "rayforge-lightburn-device-import.json"
SOURCE = ROOT / "tests" / "fixtures" / "synthetic-jcz-device.lbdev"


class RayforgeLightBurnDeviceImportSpikeTests(unittest.TestCase):
    def test_public_fixture_is_synthetic_and_contains_no_private_identity(self):
        source = json.loads(SOURCE.read_text(encoding="utf-8"))
        self.assertEqual(
            "synthetic public data; not a machine export",
            source["FixtureProvenance"],
        )
        rendered = SOURCE.read_text(encoding="utf-8").lower()
        self.assertNotIn("serial", rendered)
        self.assertNotIn("guid", rendered)

    def test_common_profile_fields_survive(self):
        result = json.loads(RESULT.read_text(encoding="utf-8"))
        self.assertIsNone(result["transport"])
        self.assertEqual("JCZFiber", result["raw_profile"]["type"])
        self.assertEqual([110, 110], result["mapped_profile"]["work_area_mm"])
        self.assertEqual(
            "Synthetic JCZ MOPA", result["mapped_profile"]["name"]
        )

    def test_jcz_specific_fields_fail_closed(self):
        result = json.loads(RESULT.read_text(encoding="utf-8"))
        gaps = result["gap_matrix"]
        self.assertIsNone(result["mapped_profile"]["driver"])
        self.assertFalse(gaps["jczfiber_driver_mapped"])
        self.assertFalse(gaps["require_frame_before_start_mapped"])
        self.assertFalse(gaps["cut_list_mapped"])
        self.assertFalse(gaps["frequency_mapped"])
        self.assertFalse(gaps["q_pulse_width_mapped"])
        self.assertFalse(gaps["safe_for_jcz_use"])


if __name__ == "__main__":
    unittest.main()
