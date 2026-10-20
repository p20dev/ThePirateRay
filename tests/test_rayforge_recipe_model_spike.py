import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "rayforge-recipe-model.json"
SCRIPT = ROOT / "scripts" / "spike_rayforge_recipe_model.py"


class RayforgeRecipeModelSpikeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_recipe_matching_fails_closed_without_required_context(self):
        model = self.result["model"]
        self.assertTrue(model["matches_complete_context"])
        self.assertTrue(model["rejects_wrong_material"])
        self.assertTrue(model["rejects_missing_stock_context"])

    def test_recipe_payload_is_allowlisted_per_step(self):
        model = self.result["model"]
        self.assertTrue(model["unknown_setting_rejected_by_step"])
        self.assertTrue(model["disabled_setting_left_unchanged"])
        self.assertEqual(
            sorted(model["step_allowlisted_settings"]),
            ["frequency", "power", "pulse_width"],
        )

    def test_units_and_compatibility_axes_are_present(self):
        contract = self.result["source_contract"]
        for key in (
            "machine_match",
            "head_match",
            "material_match",
            "thickness_match",
            "step_type_match",
            "frequency_hz",
            "pulse_width_ns",
            "file_per_recipe_yaml",
            "forward_compatible_extra_metadata",
        ):
            self.assertTrue(contract[key], key)

    def test_pirateray_metadata_gaps_are_not_claimed_as_native(self):
        contract = self.result["source_contract"]
        for key in (
            "native_approval_status",
            "native_provenance",
            "native_lens_match",
            "native_correction_match",
            "native_named_collections",
        ):
            self.assertFalse(contract[key], key)
        self.assertEqual(
            self.result["model"]["extra_metadata_roundtrip"]
            ["pirateray_provenance"]["status"],
            "synthetic-unverified",
        )

    def test_spike_is_hardware_free(self):
        self.assertFalse(self.result["hardware_access"])
        source = SCRIPT.read_text(encoding="utf-8").lower()
        for forbidden in ("pyusb", "usb.core", "9588", "9899"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
