import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
RESULT = ROOT / "tests" / "fixtures" / "rayforge-graphical-workflow.json"


class RayforgeGraphicalWorkflowSpikeTests(unittest.TestCase):
    def setUp(self):
        self.result = json.loads(RESULT.read_text(encoding="utf-8"))

    def test_workflow_is_transport_free(self):
        self.assertIsNone(self.result["transport"])
        self.assertFalse(self.result["controller_backend_reachable"])

    def test_mopa_controls_have_explicit_units(self):
        controls = self.result["workflow_controls"]
        self.assertEqual("Hz", controls["frequency"]["unit_contract"])
        self.assertEqual("ns", controls["pulse_width"]["unit_contract"])
        self.assertTrue(self.result["ui_contract"]["varset_generated_rows"])
        self.assertTrue(
            self.result["ui_contract"]["machine_section_is_capability_gated"]
        )

    def test_step_round_trip_preserves_process_values(self):
        self.assertTrue(all(self.result["round_trip_preserved"].values()))
        step = self.result["serialized_step"]
        self.assertEqual(40000, step["frequency"])
        self.assertEqual(100, step["pulse_width"])

    def test_preview_exists_without_machine_code(self):
        preview = self.result["preview"]
        self.assertTrue(preview["available"])
        self.assertGreater(preview["operation_count"], 0)
        self.assertIsNone(preview["machine_code"])

    def test_manual_gtk_evidence_is_not_claimed(self):
        self.assertGreater(len(self.result["remaining_manual_evidence"]), 0)
        self.assertIn("headless", self.result["assessment_scope"])


if __name__ == "__main__":
    unittest.main()
