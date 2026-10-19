"""Characterize Rayforge's graphical MOPA workflow without opening hardware."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


RAYFORGE_COMMIT = "c28918c87f8273dd1d244f5a057addc192807fa5"


def _commit_of(source: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def run(source: Path) -> dict[str, object]:
    commit = _commit_of(source)
    if commit != RAYFORGE_COMMIT:
        raise RuntimeError(f"expected Rayforge {RAYFORGE_COMMIT}, found {commit}")

    sys.path.insert(0, str(source))
    sys.path.insert(
        0,
        str(source / "rayforge" / "builtin_addons" / "rayforge-addon-laser"),
    )
    sys.path.insert(
        0,
        str(source / "rayforge" / "builtin_addons" / "rayforge-addon-post"),
    )

    from post_processors.worker import register_transformers
    from rayforge.pipeline.transformer.registry import transformer_registry

    register_transformers(transformer_registry)

    from laser_essentials.steps.contour_step import ContourStep
    from rayforge.pipeline.artifact.job import JobArtifact
    from raygeo.ops import Ops

    step = ContourStep(name="Synthetic MOPA contour")
    step.power = 0.42
    step.cut_speed = 750
    step.frequency = 40000
    step.pulse_width = 100
    serialized = step.to_dict()
    restored = ContourStep.from_dict(serialized)

    vars_by_key = {var.key: var for var in step.recipe_varset()}
    ui_source = (
        source
        / "rayforge"
        / "builtin_addons"
        / "rayforge-addon-laser"
        / "laser_essentials"
        / "widgets"
        / "laser_step_page.py"
    ).read_text(encoding="utf-8")

    ops = Ops()
    ops.set_power(step.power)
    ops.set_feed_rate(step.cut_speed)
    ops.set_frequency(step.frequency)
    ops.set_pulse_width(step.pulse_width)
    ops.move_to(10, 10)
    ops.line_to(20, 10)
    ops.line_to(20, 20)
    ops.line_to(10, 20)
    ops.line_to(10, 10)
    artifact = JobArtifact(
        ops=ops,
        distance=40.0,
        generation_id=1,
        time_estimate=0.053,
    )
    preview = artifact.preview_ops
    if preview is None:
        raise AssertionError("Rayforge produced no preview operation stream")

    required = ("power", "cut_speed", "frequency", "pulse_width")
    missing = [key for key in required if key not in vars_by_key]
    if missing:
        raise AssertionError(f"workflow variables missing: {missing}")

    return {
        "rayforge_commit": commit,
        "transport": None,
        "controller_backend_reachable": False,
        "assessment_scope": "headless model, UI contract, and preview artifact",
        "workflow_controls": {
            key: {
                "label": vars_by_key[key].label,
                "unit_contract": (
                    "Hz" if key == "frequency" else "ns" if key == "pulse_width" else None
                ),
            }
            for key in required
        },
        "ui_contract": {
            "machine_section_keys": ["frequency", "pulse_width"],
            "varset_generated_rows": "add_varset_section" in ui_source,
            "machine_section_is_capability_gated": "get_pwm_params" in ui_source,
        },
        "serialized_step": {
            "type": serialized["step_type"],
            "power": serialized["power"],
            "cut_speed": serialized["cut_speed"],
            "frequency": serialized["frequency"],
            "pulse_width": serialized["pulse_width"],
        },
        "round_trip_preserved": {
            "power": restored.power == step.power,
            "cut_speed": restored.cut_speed == step.cut_speed,
            "frequency": restored.frequency == step.frequency,
            "pulse_width": restored.pulse_width == step.pulse_width,
        },
        "preview": {
            "available": True,
            "operation_count": len(preview.to_dict()["commands"]),
            "distance_mm": artifact.distance,
            "time_estimate_s": artifact.time_estimate,
            "machine_code": artifact.machine_code,
        },
        "remaining_manual_evidence": [
            "launch the packaged Windows application with the external addon",
            "confirm the Machine section is visible for a synthetic JCZ-capable head",
            "exercise open, edit, preview, save, reload, cancel, and recovery by user input",
        ],
        "conclusion": (
            "Rayforge's existing workflow model and generated settings UI expose "
            "frequency and pulse width, preserve them in project-step serialization, "
            "and provide a preview operation stream without transport; packaged GTK "
            "interaction remains a manual evidence gap"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="pinned Rayforge checkout")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.source.resolve())
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
