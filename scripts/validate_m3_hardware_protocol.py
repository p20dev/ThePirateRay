"""Validate an M3 hardware-research plan without authorizing or using hardware."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import re
from pathlib import Path


PROTOCOL_NAME = "M3 controller identity and status research"
EXPECTED_TARGET = {
    "profile_id": "makerspace-naestved-jpt-e2-mopa-100w",
    "controller_family": "JCZ",
    "usb_vid": "9588",
    "usb_pid": "9899",
    "device_description": "USBLMCV4",
    "lens_field_mm": 110,
    "lens_status": "operator-confirmed-on-control-machine",
}
PROHIBITED_CAPABILITIES = {
    "persistent_write",
    "job_upload",
    "list_execution",
    "galvo_motion",
    "physical_framing",
    "source_arm",
    "laser_emission",
}
ABORT_CONDITIONS = {
    "unexpected_motion",
    "emission_or_source_arm_indication",
    "interlock_state_change",
    "unexpected_device_reset_or_disconnect",
    "unallowlisted_transfer_attempt",
    "unexpected_response",
    "operator_or_observer_stop",
}
PHYSICAL_CHECKS = (
    "emission_inhibited_and_verified",
    "work_area_cleared",
    "emergency_stop_accessible_and_tested",
    "observer_present",
    "machine_profile_physically_confirmed",
)
SHA256_ARTIFACT = re.compile(r"^sha256-[0-9a-f]{20}$")
HEX_BYTES = re.compile(r"^(?:[0-9a-f]{2})+$")
OPERATION_KEYS = {
    "operation_id",
    "purpose",
    "evidence_artifact_id",
    "evidence_level",
    "safety_class",
    "direction",
    "request_hex",
    "expected_response",
    "timeout_ms",
    "maximum_attempts",
    "state_change_expected",
}


def _timestamp_with_timezone(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _validate_operation(operation: dict, seen: set[str]) -> list[str]:
    errors = []
    if set(operation) != OPERATION_KEYS:
        errors.append("allowed operation fields do not match the protocol contract")
        return errors
    operation_id = operation["operation_id"]
    if not isinstance(operation_id, str) or not operation_id.strip():
        errors.append("allowed operation requires a non-empty operation_id")
    elif operation_id in seen:
        errors.append(f"duplicate allowed operation: {operation_id}")
    else:
        seen.add(operation_id)
    if not isinstance(operation["purpose"], str) or not operation["purpose"].strip():
        errors.append(f"allowed operation {operation_id!r} requires a purpose")
    evidence_id = operation["evidence_artifact_id"]
    if not isinstance(evidence_id, str) or SHA256_ARTIFACT.fullmatch(evidence_id) is None:
        errors.append(f"allowed operation {operation_id!r} lacks public evidence provenance")
    if operation["evidence_level"] not in {"observed", "independently-implemented"}:
        errors.append(f"allowed operation {operation_id!r} has unsupported evidence level")
    if operation["safety_class"] != "read-only-no-motion-no-emission":
        errors.append(f"allowed operation {operation_id!r} has an unsafe classification")
    if operation["direction"] != "host-to-controller-request-response":
        errors.append(f"allowed operation {operation_id!r} has an unsupported direction")
    request_hex = operation["request_hex"]
    if not isinstance(request_hex, str) or HEX_BYTES.fullmatch(request_hex) is None:
        errors.append(f"allowed operation {operation_id!r} lacks exact request bytes")
    if not isinstance(operation["expected_response"], str) or not operation[
        "expected_response"
    ].strip():
        errors.append(f"allowed operation {operation_id!r} lacks response constraints")
    if type(operation["timeout_ms"]) is not int or not 1 <= operation["timeout_ms"] <= 5000:
        errors.append(f"allowed operation {operation_id!r} has an invalid timeout")
    if type(operation["maximum_attempts"]) is not int or operation["maximum_attempts"] != 1:
        errors.append(f"allowed operation {operation_id!r} permits retry")
    if operation["state_change_expected"] is not False:
        errors.append(f"allowed operation {operation_id!r} expects a state change")
    return errors


def validate(path: Path) -> dict:
    plan = json.loads(path.resolve().read_text(encoding="utf-8-sig"))
    errors = []
    incomplete = []

    if not isinstance(plan, dict):
        return {
            "status": "invalid",
            "errors": ["protocol plan must be a JSON object"],
            "incomplete": [],
            "validated_operations": 0,
            "hardware_access_authorized": False,
            "separate_human_approval_required": True,
        }

    if plan.get("schema_version") != 1:
        errors.append("unsupported protocol schema")
    if plan.get("protocol") != PROTOCOL_NAME:
        errors.append("unexpected protocol identity")
    if plan.get("protocol_status") != "draft":
        errors.append("public protocol plan must remain draft")
    if plan.get("target") != EXPECTED_TARGET:
        errors.append("target does not match the sanitized machine profile")

    scope = plan.get("scope", {})
    if not isinstance(scope, dict):
        errors.append("scope must be an object")
        scope = {}
    if scope.get("milestone") != "M3":
        errors.append("protocol is outside M3")
    prohibited = scope.get("prohibited_capabilities", [])
    if not isinstance(prohibited, list) or set(prohibited) != PROHIBITED_CAPABILITIES:
        errors.append("prohibited capability set does not match the safety boundary")
    abort_conditions = plan.get("abort_conditions", [])
    if not isinstance(abort_conditions, list) or set(abort_conditions) != ABORT_CONDITIONS:
        errors.append("abort-condition set does not match the safety boundary")

    roles = plan.get("roles", {})
    if not isinstance(roles, dict):
        errors.append("roles must be an object")
        roles = {}
    assigned_roles = []
    for key in ("operator", "safety_observer", "protocol_reviewer"):
        if not isinstance(roles.get(key), str) or not roles.get(key, "").strip():
            incomplete.append(f"role not assigned: {key}")
        else:
            assigned_roles.append(roles[key].strip().casefold())
    if len(assigned_roles) == 3 and len(set(assigned_roles)) != 3:
        errors.append("operator, safety observer and protocol reviewer must be distinct")

    physical = plan.get("physical_controls", {})
    if not isinstance(physical, dict):
        errors.append("physical_controls must be an object")
        physical = {}
    for key in PHYSICAL_CHECKS:
        if physical.get(key) is not True:
            incomplete.append(f"physical control not confirmed: {key}")
    if not isinstance(physical.get("emission_inhibition_method"), str) or not physical.get(
        "emission_inhibition_method", ""
    ).strip():
        incomplete.append("emission inhibition method is not recorded")

    software = plan.get("software_controls", {})
    if not isinstance(software, dict):
        errors.append("software_controls must be an object")
        software = {}
    if software.get("production_backend_absent") is not True:
        errors.append("production controller backend must remain absent")
    if software.get("unknown_responses_not_replayed") is not True:
        errors.append("unknown responses must never be replayed")
    if software.get("maximum_attempts_per_operation") != 1:
        errors.append("automatic operation retry is prohibited")
    for key in ("operation_allowlist_enforced", "reversible_driver_plan_reviewed"):
        if software.get(key) is not True:
            incomplete.append(f"software control not confirmed: {key}")

    operations = plan.get("allowed_operations", [])
    if not isinstance(operations, list):
        errors.append("allowed_operations must be a list")
        operations = []
    if not operations:
        incomplete.append("no evidence-backed USB operation is allowlisted")
    seen = set()
    for operation in operations:
        if not isinstance(operation, dict):
            errors.append("allowed operation must be an object")
        else:
            errors.extend(_validate_operation(operation, seen))

    recovery = plan.get("recovery", {})
    if not isinstance(recovery, dict):
        errors.append("recovery must be an object")
        recovery = {}
    if recovery.get("no_automatic_retry_after_abort") is not True:
        errors.append("automatic retry after abort is prohibited")
    for key in (
        "power_down_procedure_reviewed",
        "driver_rollback_procedure_reviewed",
        "incident_record_destination_prepared",
    ):
        if recovery.get(key) is not True:
            incomplete.append(f"recovery control not confirmed: {key}")

    evidence = plan.get("evidence_handling", {})
    expected_evidence = {
        "raw_capture_classification": "private-sensitive",
        "raw_capture_destination": "ThePirateRay-PrivateStash",
        "public_output": "sanitized-derived-notes-only",
        "sha256_manifest_required": True,
        "private_identifiers_redacted_publicly": True,
    }
    if evidence != expected_evidence:
        errors.append("evidence handling does not match the public/private boundary")

    session = plan.get("session", {})
    if not isinstance(session, dict):
        errors.append("session must be an object")
        session = {}
    if not isinstance(session.get("machine_location"), str) or not session.get(
        "machine_location", ""
    ).strip():
        incomplete.append("machine location is not recorded")
    starts_at = _timestamp_with_timezone(session.get("planned_at"))
    ends_at = _timestamp_with_timezone(session.get("ends_at"))
    if starts_at is None:
        incomplete.append("planned_at is not an ISO-8601 timestamp with timezone")
    if ends_at is None:
        incomplete.append("ends_at is not an ISO-8601 timestamp with timezone")
    if starts_at is not None and ends_at is not None and ends_at <= starts_at:
        errors.append("session end must be later than session start")

    status = "invalid" if errors else "ready_for_review" if not incomplete else "incomplete"
    return {
        "status": status,
        "errors": errors,
        "incomplete": incomplete,
        "validated_operations": len(operations) if not errors else 0,
        "hardware_access_authorized": False,
        "separate_human_approval_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.plan)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if result["status"] == "ready_for_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
