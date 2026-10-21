import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_m3_hardware_protocol import validate


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "tests" / "fixtures" / "m3-hardware-protocol-template.json"


class M3HardwareProtocolTests(unittest.TestCase):
    def setUp(self):
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def _write(self, root: Path, plan: dict) -> Path:
        path = root / "plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        return path

    def _complete(self) -> dict:
        plan = copy.deepcopy(self.template)
        plan["roles"] = {
            "operator": "Synthetic Operator",
            "safety_observer": "Synthetic Observer",
            "protocol_reviewer": "Synthetic Reviewer",
        }
        plan["physical_controls"] = {
            key: True for key in plan["physical_controls"]
            if key != "emission_inhibition_method"
        }
        plan["physical_controls"]["emission_inhibition_method"] = (
            "Synthetic reviewed isolation method"
        )
        plan["software_controls"]["operation_allowlist_enforced"] = True
        plan["software_controls"]["reversible_driver_plan_reviewed"] = True
        plan["allowed_operations"] = [{
            "operation_id": "synthetic-read-identity",
            "purpose": "Synthetic validator fixture only",
            "evidence_artifact_id": "sha256-0123456789abcdef0123",
            "evidence_level": "independently-implemented",
            "safety_class": "read-only-no-motion-no-emission",
            "direction": "host-to-controller-request-response",
            "request_hex": "0102",
            "expected_response": "Synthetic fixed response contract",
            "timeout_ms": 1000,
            "maximum_attempts": 1,
            "state_change_expected": False,
        }]
        plan["recovery"].update({
            "power_down_procedure_reviewed": True,
            "driver_rollback_procedure_reviewed": True,
            "incident_record_destination_prepared": True,
        })
        plan["session"] = {
            "machine_location": "Synthetic test location",
            "planned_at": "2026-10-21T12:00:00+02:00",
            "ends_at": "2026-10-21T12:30:00+02:00",
            "notes": "No hardware is used by this unit test.",
        }
        return plan

    def test_public_template_is_incomplete_and_never_authorizes_hardware(self):
        result = validate(TEMPLATE)
        self.assertEqual("incomplete", result["status"])
        self.assertFalse(result["hardware_access_authorized"])
        self.assertTrue(result["separate_human_approval_required"])
        self.assertIn(
            "no evidence-backed USB operation is allowlisted",
            result["incomplete"],
        )

    def test_complete_plan_is_only_ready_for_review(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            result = validate(self._write(Path(directory), self._complete()))
        self.assertEqual("ready_for_review", result["status"])
        self.assertEqual(1, result["validated_operations"])
        self.assertFalse(result["hardware_access_authorized"])

    def test_roles_must_be_distinct(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            plan = self._complete()
            plan["roles"]["safety_observer"] = plan["roles"]["operator"]
            result = validate(self._write(Path(directory), plan))
        self.assertEqual("invalid", result["status"])
        self.assertIn(
            "operator, safety observer and protocol reviewer must be distinct",
            result["errors"],
        )
        self.assertFalse(result["hardware_access_authorized"])

    def test_session_window_must_be_bounded_and_ordered(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            plan = self._complete()
            plan["session"]["ends_at"] = plan["session"]["planned_at"]
            result = validate(self._write(Path(directory), plan))
        self.assertEqual("invalid", result["status"])
        self.assertIn("session end must be later than session start", result["errors"])
        self.assertFalse(result["hardware_access_authorized"])

    def test_safety_boundary_cannot_be_narrowed(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            plan = self._complete()
            plan["scope"]["prohibited_capabilities"].remove("laser_emission")
            result = validate(self._write(Path(directory), plan))
        self.assertEqual("invalid", result["status"])
        self.assertIn(
            "prohibited capability set does not match the safety boundary",
            result["errors"],
        )

    def test_operation_requires_exact_bytes_provenance_and_no_retry(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            plan = self._complete()
            operation = plan["allowed_operations"][0]
            operation["request_hex"] = "unknown"
            operation["evidence_artifact_id"] = "private-path"
            operation["maximum_attempts"] = 2
            result = validate(self._write(Path(directory), plan))
        self.assertEqual("invalid", result["status"])
        self.assertGreaterEqual(len(result["errors"]), 3)
        self.assertFalse(result["hardware_access_authorized"])

    def test_motion_or_state_change_operation_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            plan = self._complete()
            operation = plan["allowed_operations"][0]
            operation["safety_class"] = "motion"
            operation["state_change_expected"] = True
            result = validate(self._write(Path(directory), plan))
        self.assertEqual("invalid", result["status"])
        self.assertTrue(any("unsafe classification" in item for item in result["errors"]))
        self.assertTrue(any("expects a state change" in item for item in result["errors"]))

    def test_malformed_types_fail_closed_instead_of_crashing(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            plan = self._complete()
            plan["scope"] = None
            plan["roles"] = []
            operation = plan["allowed_operations"][0]
            operation["request_hex"] = 102
            operation["evidence_artifact_id"] = False
            operation["timeout_ms"] = True
            result = validate(self._write(Path(directory), plan))
        self.assertEqual("invalid", result["status"])
        self.assertGreaterEqual(len(result["errors"]), 6)
        self.assertFalse(result["hardware_access_authorized"])


if __name__ == "__main__":
    unittest.main()
