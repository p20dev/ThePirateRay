import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "upstreams" / "rayforge.json"
PREPARE = ROOT / "scripts" / "prepare_rayforge_build.ps1"
PIN = "c28918c87f8273dd1d244f5a057addc192807fa5"


class UpstreamBuildReferenceTests(unittest.TestCase):
    def test_rayforge_reference_is_exact_and_https(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["commit"], PIN)
        self.assertEqual(
            data["repository"], "https://github.com/barebaric/rayforge.git"
        )

    def test_prepare_script_is_on_demand_and_uses_ignored_cache(self):
        script = PREPARE.read_text(encoding="utf-8")
        self.assertIn('".build\\upstreams"', script)
        self.assertIn("SupportsShouldProcess", script)
        self.assertNotIn("InstallWindowsDependencies", script)
        self.assertIn("BuildWindowsBundle", script)
        self.assertIn("No dependencies were installed", script)

    def test_prepare_script_has_no_hardware_path(self):
        script = PREPARE.read_text(encoding="utf-8").lower()
        for forbidden in ("pyusb", "usb.core", "9588", "9899", "frame", "mark"):
            self.assertNotIn(forbidden, script)


if __name__ == "__main__":
    unittest.main()
