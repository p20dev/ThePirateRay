"""Validate a manual M1 desktop acceptance report without running the app."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
STEP_IDS = (
    "artifact_verified",
    "isolated_portable_launch",
    "offline_state_visible",
    "synthetic_geometry_and_field",
    "layer_editing_and_order",
    "visibility_output_independent",
    "mopa_values_and_units",
    "recipe_compatibility_gate",
    "preview_and_preflight",
    "save_reopen_round_trip",
    "simulation_cancel_recovery",
    "theme_and_disclosure_stability",
)
STOP_CONDITIONS = (
    "device_discovery_prompt",
    "physical_device_status",
    "transport_attempt",
    "unlabelled_physical_framing",
)
STEP_STATUSES = {"passed", "failed", "blocked", "not_run"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_COMMIT = re.compile(r"^[0-9a-f]{40}$")


def _validate_evidence(report_root: Path, records: list[dict]) -> list[str]:
    errors = []
    seen = set()
    for record in records:
        value = record.get("path", "")
        relative = PurePosixPath(value)
        if not value or relative.is_absolute() or ".." in relative.parts:
            errors.append(f"unsafe evidence path: {value!r}")
            continue
        if value in seen:
            errors.append(f"duplicate evidence path: {value}")
            continue
        seen.add(value)
        path = report_root.joinpath(*relative.parts)
        if not path.is_file():
            errors.append(f"evidence file is missing: {value}")
            continue
        digest = record.get("sha256", "")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if not SHA256.fullmatch(digest) or digest != actual:
            errors.append(f"evidence SHA-256 mismatch: {value}")
    return errors


def _bound_json(report_root: Path, binding: dict, label: str) -> tuple[dict | None, list[str]]:
    value = binding.get("report_path") or binding.get("manifest_path") or ""
    relative = PurePosixPath(value)
    if not value or relative.is_absolute() or ".." in relative.parts:
        return None, [f"unsafe {label} path: {value!r}"]
    path = report_root.joinpath(*relative.parts)
    if not path.is_file():
        return None, [f"{label} is missing: {value}"]
    digest = binding.get("report_sha256") or binding.get("manifest_sha256") or ""
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if not SHA256.fullmatch(digest) or digest != actual:
        return None, [f"{label} SHA-256 mismatch: {value}"]
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")), []
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, [f"{label} is not valid JSON: {value}"]


def _validate_kit(report_root: Path, binding: dict) -> list[str]:
    manifest, errors = _bound_json(report_root, binding, "acceptance-kit manifest")
    if errors:
        return errors
    if manifest.get("schema_version") != 2:
        errors.append("unsupported acceptance-kit schema")
    if manifest.get("kit") != "M1 packaged no-device desktop acceptance":
        errors.append("unexpected acceptance-kit name")
    commit = binding.get("repository_commit", "")
    if not GIT_COMMIT.fullmatch(commit) or manifest.get("repository_commit") != commit:
        errors.append("acceptance-kit repository commit mismatch")
    if manifest.get("hardware_access_authorized") is not False:
        errors.append("acceptance kit does not preserve the hardware gate")
    if manifest.get("contains_private_evidence") is not False:
        errors.append("acceptance kit contains private evidence")
    for record in manifest.get("files", []):
        errors.extend(_validate_evidence(report_root, [record]))
    return errors


def _validate_artifact_report(report_root: Path, binding: dict) -> list[str]:
    verification, errors = _bound_json(
        report_root, binding, "artifact-verification report"
    )
    if errors:
        return errors
    if verification.get("status") != "passed":
        errors.append("artifact verification did not pass")
    if verification.get("hardware_access") is not False:
        errors.append("artifact verification does not preserve the hardware gate")
    if verification.get("executed_binaries") is not False:
        errors.append("artifact verification executed binaries")
    if verification.get("manual_interaction_required") is not True:
        errors.append("artifact verification dropped the manual interaction gate")
    return errors


def validate(report_path: Path) -> dict:
    report_path = report_path.resolve()
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    errors = []
    if report.get("schema_version") != 2:
        errors.append("unsupported report schema")
    if report.get("checkpoint") != "M1 packaged no-device desktop acceptance":
        errors.append("unexpected checkpoint name")

    steps = report.get("steps", [])
    step_ids = [step.get("id") for step in steps]
    if step_ids != list(STEP_IDS):
        errors.append("acceptance steps are missing, duplicated or out of order")
    for step in steps:
        if step.get("status") not in STEP_STATUSES:
            errors.append(f"invalid step status: {step.get('id')}")

    stop_conditions = report.get("stop_conditions", {})
    if set(stop_conditions) != set(STOP_CONDITIONS):
        errors.append("stop-condition set does not match the contract")
    elif any(value not in (True, False, None) for value in stop_conditions.values()):
        errors.append("stop conditions must be true, false or null")

    environment = report.get("environment", {})
    artifact = report.get("artifact_verification", {})
    kit = report.get("acceptance_kit", {})
    errors.extend(_validate_kit(report_path.parent, kit))
    artifact_errors = _validate_artifact_report(report_path.parent, artifact)
    errors.extend(artifact_errors)
    errors.extend(_validate_evidence(report_path.parent, report.get("evidence", [])))

    explicit_failure = (
        any(step.get("status") == "failed" for step in steps)
        or any(value is True for value in stop_conditions.values())
        or environment.get("hardware_disconnected") is False
        or environment.get("fresh_app_data") is False
        or artifact.get("status") == "failed"
    )
    complete = (
        not errors
        and step_ids == list(STEP_IDS)
        and all(step.get("status") == "passed" for step in steps)
        and all(value is False for value in stop_conditions.values())
        and environment.get("hardware_disconnected") is True
        and environment.get("fresh_app_data") is True
        and bool(environment.get("windows_version"))
        and artifact.get("status") == "passed"
        and not artifact_errors
    )
    status = "failed" if explicit_failure or errors else "passed" if complete else "incomplete"
    return {
        "status": status,
        "schema_valid": not errors,
        "errors": errors,
        "passed_steps": sum(step.get("status") == "passed" for step in steps),
        "required_steps": len(STEP_IDS),
        "hardware_access_authorized": False,
        "manual_review_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.report)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
