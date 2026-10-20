"""Consolidate the transport-free M1 regression evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PINNED_COMMIT = "c28918c87f8273dd1d244f5a057addc192807fa5"

EVIDENCE = {
    "addon_lifecycle": "rayforge-addon-spike.json",
    "graphical_workflow_model": "rayforge-graphical-workflow.json",
    "layer_model": "rayforge-layer-model.json",
    "recipe_model": "rayforge-recipe-model.json",
    "jcz_equivalence": "rayforge-jcz-equivalence.json",
    "jcz_negative_cases": "rayforge-jcz-negative-cases.json",
    "cancel_recovery": "rayforge-jcz-cancel-recovery.json",
    "lightburn_mopa_import": "rayforge-lightburn-mopa-import.json",
    "lightburn_device_import": "rayforge-lightburn-device-import.json",
}


def _commit_of(source: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _run_check(command: list[str], environment: dict[str, str]) -> dict:
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
        env=environment,
    )
    combined = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise RuntimeError(combined or f"check failed: {command}")
    return {
        "status": "passed",
        "command": command,
        "output_tail": combined.splitlines()[-4:],
    }


def _load_evidence() -> dict[str, dict]:
    fixture_dir = ROOT / "tests" / "fixtures"
    results = {}
    for name, filename in EVIDENCE.items():
        path = fixture_dir / filename
        results[name] = {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "report": json.loads(path.read_text(encoding="utf-8")),
        }
    return results


def run(source: Path) -> dict:
    commit = _commit_of(source)
    if commit != PINNED_COMMIT:
        raise RuntimeError(f"expected Rayforge {PINNED_COMMIT}, found {commit}")

    temp_dir = ROOT / ".build" / "acceptance-temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["TEMP"] = str(temp_dir)
    environment["TMP"] = str(temp_dir)

    repository_checks = {
        "unit_tests": _run_check(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            environment,
        ),
        "public_repo_guard": _run_check(
            [sys.executable, "scripts/check_public_repo.py", "."],
            environment,
        ),
    }
    evidence = _load_evidence()

    graphical = evidence["graphical_workflow_model"]["report"]
    negative = evidence["jcz_negative_cases"]["report"]
    cancellation = evidence["cancel_recovery"]["report"]
    device_import = evidence["lightburn_device_import"]["report"]
    transport_free = all(
        item["report"].get("transport") is None
        for item in evidence.values()
        if "transport" in item["report"]
    )
    controller_unreachable = (
        graphical["controller_backend_reachable"] is False
    )
    checks = {
        "repository_checks_passed": all(
            item["status"] == "passed" for item in repository_checks.values()
        ),
        "transport_free": transport_free,
        "controller_backend_unreachable": controller_unreachable,
        "negative_cases_fail_closed": negative["all_failed_closed"],
        "cancel_requires_recovery": cancellation[
            "restart_without_recovery_rejected"
        ],
        "incomplete_import_blocks_encoding": not device_import[
            "addon_profile_seam"
        ]["encoding_allowed"],
    }
    passed = all(checks.values())
    return {
        "checkpoint": "M1 no-device acceptance",
        "status": "passed" if passed else "failed",
        "rayforge_commit": commit,
        "hardware_access": False,
        "controller_backend_reachable": not controller_unreachable,
        "checks": checks,
        "repository_checks": repository_checks,
        "evidence": evidence,
        "remaining_manual_gates": [
            "packaged Windows GUI interaction",
            "known-working private LightBurn project import",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rayforge_checkout", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    (ROOT / ".build").mkdir(exist_ok=True)
    result = run(args.rayforge_checkout.resolve())
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"status={result['status']}")
    print(f"sha256={hashlib.sha256(rendered.encode()).hexdigest()}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
