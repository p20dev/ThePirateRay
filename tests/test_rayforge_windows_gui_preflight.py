import json
import unittest
from pathlib import Path
import tempfile

from scripts.check_rayforge_windows_gui import inspect


ROOT = Path(__file__).parents[1]
RESULT = ROOT / "tests" / "fixtures" / "rayforge-windows-gui-preflight.json"


class RayforgeWindowsGuiPreflightTests(unittest.TestCase):
    def setUp(self):
        self.result = json.loads(RESULT.read_text(encoding="utf-8"))

    def test_preflight_is_transport_free(self):
        self.assertIsNone(self.result["transport"])
        self.assertFalse(self.result["controller_backend_reachable"])

    def test_missing_runtime_blocks_gui_claim(self):
        self.assertEqual("blocked", self.result["status"])
        self.assertFalse(self.result["ready_for_manual_gui_test"])
        self.assertFalse(self.result["installation_performed"])
        self.assertIn("pygobject_gi_available", self.result["missing_requirements"])

    def test_source_and_no_device_addon_are_present(self):
        checks = self.result["checks"]
        self.assertTrue(checks["pinned_source_present"])
        self.assertTrue(checks["application_entry_present"])
        self.assertTrue(checks["no_device_addon_present"])

    def test_result_records_the_requested_runtime_probe(self):
        self.assertIn("No module named 'gi'", self.result["observed_launch_error"])

    def test_missing_runtime_path_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = inspect(Path(temporary), Path(temporary) / "missing-python.exe")
        self.assertFalse(result["ready_for_manual_gui_test"])
        self.assertEqual("python runtime not found", result["observed_launch_error"])


if __name__ == "__main__":
    unittest.main()
