import json
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_m3_review_packet import ROOT, create_packet
from scripts.validate_m3_approval import validate
from tests.test_m3_review_packet import write_ready_plan


class M3ApprovalTests(unittest.TestCase):
    def _packet_and_approval(self, root: Path) -> tuple[Path, Path]:
        packet = root / "packet"
        create_packet(write_ready_plan(root), packet, "a" * 40)
        template = packet / "approval-record-template.json"
        approval = json.loads(template.read_text(encoding="utf-8"))
        approval["decision"] = "approved"
        approval["reviewer"] = "Synthetic Reviewer"
        approval["reviewed_at"] = "2026-10-21T11:30:00+02:00"
        approval["statements"] = {
            key: True for key in approval["statements"]
        }
        approval_path = root / "approval-record.json"
        approval_path.write_text(json.dumps(approval), encoding="utf-8")
        return packet, approval_path

    def test_exact_approval_record_is_valid_but_not_hardware_authorization(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            packet, approval = self._packet_and_approval(Path(directory))
            result = validate(packet, approval)
        self.assertEqual("approval_record_valid", result["status"])
        self.assertTrue(result["administrative_approval_valid"])
        self.assertFalse(result["hardware_access_authorized"])
        self.assertTrue(result["live_preflight_required"])

    def test_changed_plan_or_manifest_binding_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            packet, approval = self._packet_and_approval(Path(directory))
            (packet / "plan.json").write_text("{}", encoding="utf-8")
            result = validate(packet, approval)
        self.assertEqual("invalid", result["status"])
        self.assertTrue(any("binding failed" in item for item in result["errors"]))
        self.assertFalse(result["hardware_access_authorized"])

    def test_reviewer_and_session_window_must_match_plan(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            packet, approval_path = self._packet_and_approval(root)
            approval = json.loads(approval_path.read_text())
            approval["reviewer"] = "Someone Else"
            approval["session_window"]["ends_at"] = "2026-10-21T13:00:00+02:00"
            approval_path.write_text(json.dumps(approval), encoding="utf-8")
            result = validate(packet, approval_path)
        self.assertEqual("invalid", result["status"])
        self.assertGreaterEqual(len(result["errors"]), 2)

    def test_late_review_or_unconfirmed_statement_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            packet, approval_path = self._packet_and_approval(root)
            approval = json.loads(approval_path.read_text())
            approval["reviewed_at"] = "2026-10-21T12:00:00+02:00"
            approval["statements"]["physical_controls_reviewed"] = False
            approval_path.write_text(json.dumps(approval), encoding="utf-8")
            result = validate(packet, approval_path)
        self.assertEqual("invalid", result["status"])
        self.assertTrue(any("before the session" in item for item in result["errors"]))
        self.assertTrue(any("every approval" in item for item in result["errors"]))

    def test_automatic_hardware_authorization_claim_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            packet, approval_path = self._packet_and_approval(root)
            approval = json.loads(approval_path.read_text())
            approval["hardware_access_authorized"] = True
            approval_path.write_text(json.dumps(approval), encoding="utf-8")
            result = validate(packet, approval_path)
        self.assertEqual("invalid", result["status"])
        self.assertFalse(result["hardware_access_authorized"])


if __name__ == "__main__":
    unittest.main()
