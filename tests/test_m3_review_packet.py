import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_m3_review_packet import ROOT, create_packet


TEMPLATE = ROOT / "tests" / "fixtures" / "m3-hardware-protocol-template.json"


class M3ReviewPacketTests(unittest.TestCase):
    def _ready_plan(self, root: Path) -> Path:
        plan = copy.deepcopy(json.loads(TEMPLATE.read_text(encoding="utf-8")))
        plan["roles"] = {
            "operator": "Synthetic Operator",
            "safety_observer": "Synthetic Observer",
            "protocol_reviewer": "Synthetic Reviewer",
        }
        for key in plan["physical_controls"]:
            plan["physical_controls"][key] = True
        plan["physical_controls"]["emission_inhibition_method"] = "Synthetic method"
        plan["software_controls"]["operation_allowlist_enforced"] = True
        plan["software_controls"]["reversible_driver_plan_reviewed"] = True
        plan["allowed_operations"] = [{
            "operation_id": "synthetic-read-identity",
            "purpose": "Synthetic packet test only",
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
            "machine_location": "Synthetic location",
            "planned_at": "2026-10-21T12:00:00+02:00",
            "ends_at": "2026-10-21T12:30:00+02:00",
            "notes": "Synthetic unit test only",
        }
        path = root / "source-plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        return path

    def test_packet_freezes_exact_plan_and_stays_non_authorizing(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            source = self._ready_plan(root)
            source_bytes = source.read_bytes()
            output = root / "packet"
            manifest = create_packet(source, output, repository_commit="a" * 40)
            review = json.loads((output / "approval-record-template.json").read_text())
            frozen_bytes = (output / "plan.json").read_bytes()
        self.assertEqual(source_bytes, frozen_bytes)
        self.assertEqual(hashlib.sha256(source_bytes).hexdigest(), review["binding"]["plan_sha256"])
        self.assertEqual("not_reviewed", review["decision"])
        self.assertFalse(review["hardware_access_authorized"])
        self.assertFalse(manifest["hardware_access_authorized"])
        self.assertEqual("a" * 40, manifest["repository_commit"])

    def test_incomplete_public_template_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            with self.assertRaisesRegex(ValueError, "not ready for review"):
                create_packet(TEMPLATE, Path(directory) / "packet", "b" * 40)

    def test_changed_plan_changes_binding(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            source = self._ready_plan(root)
            create_packet(source, root / "one", "c" * 40)
            one = json.loads((root / "one" / "approval-record-template.json").read_text())
            plan = json.loads(source.read_text())
            plan["session"]["notes"] = "Changed synthetic note"
            source.write_text(json.dumps(plan), encoding="utf-8")
            create_packet(source, root / "two", "c" * 40)
            two = json.loads((root / "two" / "approval-record-template.json").read_text())
        self.assertNotEqual(one["binding"]["plan_sha256"], two["binding"]["plan_sha256"])

    def test_nonempty_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            source = self._ready_plan(root)
            output = root / "packet"
            output.mkdir()
            sentinel = output / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not empty"):
                create_packet(source, output, "d" * 40)
            self.assertEqual("keep", sentinel.read_text(encoding="utf-8"))

    def test_manifest_hashes_every_packet_file(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            output = root / "packet"
            manifest = create_packet(self._ready_plan(root), output, "e" * 40)
            for record in manifest["files"]:
                path = output / record["path"]
                self.assertEqual(path.stat().st_size, record["bytes"])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record["sha256"])


if __name__ == "__main__":
    unittest.main()
