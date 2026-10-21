import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_m1_manual_acceptance import ROOT, STEP_IDS, validate


TEMPLATE = ROOT / "tests" / "fixtures" / "m1-manual-acceptance-template.json"


class M1ManualAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def _write(self, root: Path, report: dict) -> Path:
        path = root / "acceptance.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        return path

    def _bind_reports(self, root: Path, report: dict) -> None:
        manifest = {
            "schema_version": 2,
            "kit": "M1 packaged no-device desktop acceptance",
            "repository_commit": "b" * 40,
            "hardware_access_authorized": False,
            "contains_private_evidence": False,
            "files": [],
        }
        manifest_path = root / "kit-manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        report["acceptance_kit"] = {
            "manifest_path": manifest_path.name,
            "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "repository_commit": "b" * 40,
        }
        verification = {
            "status": "passed",
            "hardware_access": False,
            "executed_binaries": False,
            "manual_interaction_required": True,
        }
        verification_path = root / "artifact-verification.json"
        verification_path.write_text(json.dumps(verification), encoding="utf-8")
        report["artifact_verification"] = {
            "status": "passed",
            "report_path": verification_path.name,
            "report_sha256": hashlib.sha256(
                verification_path.read_bytes()
            ).hexdigest(),
        }

    def _passing(self, root: Path) -> dict:
        report = copy.deepcopy(self.template)
        self._bind_reports(root, report)
        report["environment"] = {
            "windows_version": "synthetic-test-environment",
            "hardware_disconnected": True,
            "fresh_app_data": True,
        }
        for step in report["steps"]:
            step["status"] = "passed"
        report["stop_conditions"] = {
            key: False for key in report["stop_conditions"]
        }
        screenshot = root / "evidence" / "offline-state.png"
        screenshot.parent.mkdir(exist_ok=True)
        screenshot.write_bytes(b"synthetic screenshot placeholder")
        report["evidence"] = [{
            "path": "evidence/offline-state.png",
            "sha256": hashlib.sha256(screenshot.read_bytes()).hexdigest(),
        }]
        return report

    def test_template_is_valid_but_incomplete(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            report = copy.deepcopy(self.template)
            self._bind_reports(root, report)
            report["artifact_verification"]["status"] = "not_run"
            result = validate(self._write(root, report))
        self.assertEqual(result["status"], "incomplete")
        self.assertTrue(result["schema_valid"])
        self.assertEqual(result["required_steps"], len(STEP_IDS))

    def test_complete_no_device_report_passes(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            result = validate(self._write(root, self._passing(root)))
        self.assertEqual(result["status"], "passed")
        self.assertFalse(result["hardware_access_authorized"])
        self.assertTrue(result["manual_review_required"])

    def test_any_stop_condition_fails_checkpoint(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            report = self._passing(root)
            report["stop_conditions"]["transport_attempt"] = True
            result = validate(self._write(root, report))
        self.assertEqual(result["status"], "failed")

    def test_missing_step_cannot_pass(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            report = self._passing(root)
            report["steps"].pop()
            result = validate(self._write(root, report))
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["schema_valid"])

    def test_changed_or_external_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            report = self._passing(root)
            report["evidence"][0]["sha256"] = "0" * 64
            result = validate(self._write(root, report))
            self.assertEqual(result["status"], "failed")
            report["evidence"][0]["path"] = "../private.png"
            result = validate(self._write(root, report))
            self.assertEqual(result["status"], "failed")

    def test_unbound_or_changed_provenance_reports_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            report = self._passing(root)
            report["artifact_verification"]["report_sha256"] = "0" * 64
            result = validate(self._write(root, report))
            self.assertEqual(result["status"], "failed")
            self.assertIn("artifact-verification report SHA-256 mismatch", result["errors"][0])

            report = self._passing(root)
            report["acceptance_kit"]["repository_commit"] = "c" * 40
            result = validate(self._write(root, report))
            self.assertEqual(result["status"], "failed")
            self.assertIn("acceptance-kit repository commit mismatch", result["errors"])


if __name__ == "__main__":
    unittest.main()
