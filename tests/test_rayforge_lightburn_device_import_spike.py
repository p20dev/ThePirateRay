import json
import unittest
from copy import deepcopy
from pathlib import Path
import sys


ROOT = Path(__file__).parents[1]
RESULT = ROOT / "tests" / "fixtures" / "rayforge-lightburn-device-import.json"
SOURCE = ROOT / "tests" / "fixtures" / "synthetic-jcz-device.lbdev"
ADDON = ROOT / "spikes" / "rayforge-jcz-no-device-addon"
sys.path.insert(0, str(ADDON))

from pirate_ray_jcz.profile_import import (  # noqa: E402
    JCZProfileImportError,
    import_lightburn_jcz_profile,
)


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

    def test_addon_seam_preserves_raw_values_but_blocks_encoding(self):
        result = json.loads(RESULT.read_text(encoding="utf-8"))
        seam = result["addon_profile_seam"]
        self.assertEqual("PirateRayJCZNoDeviceDriver", seam["driver"])
        self.assertIsNone(seam["transport"])
        self.assertFalse(seam["encoding_allowed"])
        self.assertEqual("normalized-offline-not-authorized", seam["process_metadata"]["status"])
        entry = seam["process_metadata"]["cut_list"][0]
        self.assertEqual(40000, entry["frequency"]["raw_value"])
        self.assertEqual(40000, entry["frequency"]["value_hz"])
        self.assertEqual(40, entry["frequency"]["value_khz"])
        self.assertEqual(100, entry["q_pulse_width"]["raw_value"])
        self.assertEqual(100, entry["q_pulse_width"]["value_ns"])
        contract = seam["observed_device_contract"]
        self.assertEqual([1, 4000], contract["frequency_ui_range_khz"])
        self.assertEqual("IPG_YLPM", contract["fiber_type_ui_label"])
        self.assertEqual(
            "label-is-not-manufacturer-identity",
            contract["fiber_type_identity_status"],
        )

    def test_addon_seam_rejects_wrong_backend_and_missing_frame_gate(self):
        source = json.loads(SOURCE.read_text(encoding="utf-8"))
        wrong_backend = deepcopy(source)
        wrong_backend["DeviceList"][0]["Type"] = "Ruida"
        with self.assertRaises(JCZProfileImportError):
            import_lightburn_jcz_profile(wrong_backend)

        no_frame_gate = deepcopy(source)
        no_frame_gate["DeviceList"][0]["Settings"][
            "RequireFrameBeforeStart"
        ] = False
        with self.assertRaises(JCZProfileImportError):
            import_lightburn_jcz_profile(no_frame_gate)

        wrong_identity = deepcopy(source)
        wrong_identity["SyntheticProfileId"] = "some-other-profile"
        with self.assertRaises(JCZProfileImportError):
            import_lightburn_jcz_profile(wrong_identity)

        ambiguous_frequency = deepcopy(source)
        ambiguous_frequency["DeviceList"][0]["CutList"][0][
            "frequency"
        ] = True
        with self.assertRaises(JCZProfileImportError):
            import_lightburn_jcz_profile(ambiguous_frequency)

        for frequency in (500, 4_001_000):
            outside_range = deepcopy(source)
            outside_range["DeviceList"][0]["CutList"][0]["frequency"] = frequency
            with self.subTest(frequency=frequency):
                with self.assertRaisesRegex(JCZProfileImportError, "outside"):
                    import_lightburn_jcz_profile(outside_range)

    def test_observed_profile_contract_fails_closed_on_mismatch(self):
        source = json.loads(SOURCE.read_text(encoding="utf-8"))
        mutations = (
            ("wrong version", lambda doc: doc.update(AppVersion="2.2.00")),
            ("wrong width", lambda doc: doc["DeviceList"][0].update(Width=300)),
            ("q pulse disabled", lambda doc: doc["DeviceList"][0]["Settings"].update(
                Laser_QPulseWidthEnabled=False)),
            ("wrong fiber code", lambda doc: doc["DeviceList"][0]["Settings"].update(
                Laser_FiberType=2)),
            ("reversed frequency range", lambda doc: doc["DeviceList"][0]["Settings"].update(
                Laser_MinFreq=4000, Laser_MaxFreq=1)),
        )
        for label, mutate in mutations:
            candidate = deepcopy(source)
            mutate(candidate)
            with self.subTest(label=label):
                with self.assertRaises(JCZProfileImportError):
                    import_lightburn_jcz_profile(candidate)


if __name__ == "__main__":
    unittest.main()
