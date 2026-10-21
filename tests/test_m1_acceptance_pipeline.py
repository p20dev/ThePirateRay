import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "scripts" / "run_m1_no_device_acceptance.py"
BUILD = ROOT / "scripts" / "build_rayforge_windows_checkpoint.ps1"
VERIFY = ROOT / "scripts" / "verify_rayforge_windows_checkpoint.py"
UPSTREAM = ROOT / "upstreams" / "rayforge.json"


class M1AcceptancePipelineTests(unittest.TestCase):
    def test_acceptance_collects_every_current_offline_proof(self):
        source = ACCEPTANCE.read_text(encoding="utf-8")
        expected = (
            "rayforge-addon-spike.json",
            "rayforge-graphical-workflow.json",
            "rayforge-layer-model.json",
            "rayforge-recipe-model.json",
            "rayforge-jcz-equivalence.json",
            "rayforge-jcz-negative-cases.json",
            "rayforge-jcz-cancel-recovery.json",
            "rayforge-lightburn-mopa-import.json",
            "rayforge-lightburn-device-import.json",
        )
        for script in expected:
            self.assertIn(script, source)

    def test_acceptance_is_pinned_and_reports_remaining_manual_gates(self):
        manifest = json.loads(UPSTREAM.read_text(encoding="utf-8"))
        source = ACCEPTANCE.read_text(encoding="utf-8")
        self.assertIn(manifest["commit"], source)
        self.assertIn("packaged Windows GUI interaction", source)
        self.assertIn("known-working private LightBurn project import", source)
        self.assertIn('"-m", "unittest", "discover"', source)
        self.assertIn("scripts/check_public_repo.py", source)
        self.assertIn("timeout=120", source)

    def test_build_is_explicit_pinned_and_packages_the_addon(self):
        source = BUILD.read_text(encoding="utf-8")
        self.assertNotIn("InstallWindowsDependencies", source)
        self.assertIn("prepare_rayforge_build.ps1", source)
        self.assertIn("rayforge-addon-the-pirate-ray-jcz", source)
        self.assertIn("Compress-Archive", source)
        self.assertIn("Get-FileHash -Algorithm SHA256", source)
        self.assertIn("schema_version = 2", source)
        self.assertIn("Rayforge-LICENSE.txt", source)
        self.assertIn("license_files", source)
        self.assertIn("GetFullPath", source)
        self.assertIn("Remove-Item -LiteralPath $resolvedAddonDestination", source)
        self.assertIn("AllowStagedPirateRayAddon", source)

    def test_acceptance_has_no_hardware_commands(self):
        source = ACCEPTANCE.read_text(encoding="utf-8").lower()
        for forbidden in ("usb.core", "import usb", "open_device"):
            self.assertNotIn(forbidden, source)

    def test_build_rejects_transport_imports_in_staged_addon(self):
        source = BUILD.read_text(encoding="utf-8").lower()
        for forbidden in ("import usb", "import serial", "import socket"):
            self.assertIn(forbidden, source)

    def test_checkpoint_has_a_non_executing_artifact_verifier(self):
        source = VERIFY.read_text(encoding="utf-8")
        self.assertIn("zipfile.ZipFile", source)
        self.assertIn("Rayforge commit does not match", source)
        self.assertIn('"executed_binaries": False', source)
        self.assertIn("license sidecar", source)
        self.assertNotIn("subprocess", source)


if __name__ == "__main__":
    unittest.main()
