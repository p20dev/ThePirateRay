import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "rayforge-layer-model.json"
SCRIPT = ROOT / "scripts" / "spike_rayforge_layer_model.py"


class RayforgeLayerModelSpikeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_visibility_and_output_states_are_independent(self):
        self.assertTrue(self.result["model"]["states_are_independent"])
        self.assertFalse(self.result["model"]["layer_visible"])
        self.assertTrue(self.result["model"]["step_visible"])

    def test_states_name_color_and_order_survive_serialization(self):
        restored = self.result["model"]["roundtrip"]
        self.assertEqual(restored["layer_name"], "Engraving")
        self.assertEqual(restored["layer_color"], "#123456")
        self.assertFalse(restored["layer_visible"])
        self.assertEqual(restored["step_name"], "Mark outline")
        self.assertTrue(restored["step_visible"])
        self.assertEqual(
            self.result["model"]["serialized_layer_order"],
            ["Second", "First"],
        )

    def test_canvas_and_job_pipeline_use_different_states(self):
        contract = self.result["source_contract"]
        self.assertTrue(contract["canvas_checks_layer_visibility"])
        self.assertTrue(contract["job_pipeline_checks_step_visibility"])
        self.assertFalse(contract["job_pipeline_checks_layer_visibility"])
        self.assertTrue(contract["layer_visibility_control"])
        self.assertTrue(contract["step_visibility_control"])

    def test_spike_is_hardware_free(self):
        self.assertFalse(self.result["hardware_access"])
        source = SCRIPT.read_text(encoding="utf-8").lower()
        for forbidden in ("pyusb", "usb.core", "9588", "9899"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
