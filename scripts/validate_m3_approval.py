"""Validate an M3 review packet and separate human approval record."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import re
from pathlib import Path

if __package__:
    from scripts.validate_m3_hardware_protocol import validate as validate_plan
else:
    from validate_m3_hardware_protocol import validate as validate_plan


SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
PACKET_FILES = {"plan.json", "approval-record-template.json"}
STATEMENTS = {
    "exact_plan_bytes_reviewed",
    "operation_evidence_reviewed",
    "physical_controls_reviewed",
    "driver_and_rollback_reviewed",
    "abort_and_recovery_reviewed",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def validate(packet: Path, approval_path: Path) -> dict:
    packet = packet.resolve()
    errors = []
    manifest_path = packet / "packet-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        manifest = {}
        errors.append("packet manifest is missing or malformed")

    commit = manifest.get("repository_commit")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("packet") != "M3 hardware research plan review"
        or manifest.get("contains_private_evidence") is not False
        or manifest.get("hardware_access_authorized") is not False
        or not isinstance(commit, str)
        or COMMIT.fullmatch(commit) is None
    ):
        errors.append("packet manifest contract is invalid")

    records = manifest.get("files", [])
    if not isinstance(records, list):
        records = []
    record_names = {
        record.get("path") for record in records if isinstance(record, dict)
    }
    if record_names != PACKET_FILES or len(records) != len(PACKET_FILES):
        errors.append("packet file set is invalid")
    for record in records:
        if not isinstance(record, dict) or record.get("path") not in PACKET_FILES:
            continue
        path = packet / record["path"]
        digest = record.get("sha256")
        size = record.get("bytes")
        if (
            not path.is_file()
            or not isinstance(digest, str)
            or SHA256.fullmatch(digest) is None
            or _sha256(path) != digest
            or type(size) is not int
            or path.stat().st_size != size
        ):
            errors.append(f"packet file binding failed: {record['path']}")

    plan_path = packet / "plan.json"
    template_path = packet / "approval-record-template.json"
    plan = {}
    if plan_path.is_file():
        plan_result = validate_plan(plan_path)
        if plan_result["status"] != "ready_for_review":
            errors.append("frozen plan is not ready for review")
        try:
            plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            errors.append("frozen plan is malformed")
    else:
        errors.append("frozen plan is missing")

    try:
        template = json.loads(template_path.read_text(encoding="utf-8-sig"))
        approval = json.loads(approval_path.resolve().read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        template = {}
        approval = {}
        errors.append("approval template or record is missing or malformed")

    if set(approval) != set(template):
        errors.append("approval record fields do not match the packet template")
    expected_binding = {
        "plan_path": "plan.json",
        "plan_sha256": _sha256(plan_path) if plan_path.is_file() else None,
        "repository_commit": commit,
    }
    if approval.get("binding") != expected_binding:
        errors.append("approval record is not bound to this plan and commit")

    expected_window = {
        "starts_at": plan.get("session", {}).get("planned_at"),
        "ends_at": plan.get("session", {}).get("ends_at"),
    }
    if approval.get("session_window") != expected_window:
        errors.append("approval session window does not match the frozen plan")
    if approval.get("decision") != "approved":
        errors.append("approval decision is not approved")
    reviewer = approval.get("reviewer")
    if reviewer != plan.get("roles", {}).get("protocol_reviewer"):
        errors.append("approval reviewer does not match the plan reviewer")
    reviewed_at = _timestamp(approval.get("reviewed_at"))
    starts_at = _timestamp(expected_window["starts_at"])
    if reviewed_at is None:
        errors.append("reviewed_at is not an ISO-8601 timestamp with timezone")
    elif starts_at is not None and reviewed_at >= starts_at:
        errors.append("approval must be recorded before the session starts")

    statements = approval.get("statements", {})
    if not isinstance(statements, dict) or set(statements) != STATEMENTS:
        errors.append("approval safety statements do not match the contract")
    elif any(value is not True for value in statements.values()):
        errors.append("every approval safety statement must be confirmed")
    if approval.get("hardware_access_authorized") is not False:
        errors.append("approval record must not claim automatic hardware authorization")
    if approval.get("separate_human_approval_required") is not True:
        errors.append("separate human approval requirement cannot be removed")

    valid = not errors
    return {
        "status": "approval_record_valid" if valid else "invalid",
        "errors": errors,
        "administrative_approval_valid": valid,
        "hardware_access_authorized": False,
        "live_preflight_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("approval", type=Path)
    args = parser.parse_args()
    result = validate(args.packet, args.approval)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "approval_record_valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
