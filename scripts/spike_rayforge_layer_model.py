"""Characterize Rayforge layer visibility, output, order, and persistence."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path


RAYFORGE_COMMIT = "c28918c87f8273dd1d244f5a057addc192807fa5"


def checkout_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def characterize(root: Path) -> dict:
    commit = checkout_commit(root)
    if commit != RAYFORGE_COMMIT:
        raise RuntimeError(
            f"Expected Rayforge {RAYFORGE_COMMIT}, found {commit}"
        )

    sys.path.insert(0, str(root))
    from rayforge.core.doc import Doc
    from rayforge.core.layer import Layer
    from rayforge.core.step import Step
    from rayforge.pipeline.intent_builder import IntentBuilder

    layer = Layer("Engraving")
    layer.set_color("#123456")
    workflow = layer.workflow
    if workflow is None:
        raise RuntimeError("Test layer has no workflow")
    step = Step("Contour", "Mark outline")
    workflow.add_step(step)

    layer.set_visible(False)
    step.set_visible(True)
    restored = Layer.from_dict(layer.to_dict())
    restored_step = restored.workflow.steps[0] if restored.workflow else None

    first = Layer("First")
    second = Layer("Second")
    doc = Doc()
    doc.set_layers([second, first])
    serialized_order = [
        child["name"]
        for child in doc.to_dict()["children"]
        if child.get("type") == "layer"
    ]

    build_source = inspect.getsource(IntentBuilder.build)
    render_source = inspect.getsource(Layer.get_renderable_items)
    layer_ui = (
        root / "rayforge" / "ui_gtk" / "doceditor" / "layer_column.py"
    ).read_text(encoding="utf-8")
    step_ui = (
        root / "rayforge" / "ui_gtk" / "doceditor" / "step_box.py"
    ).read_text(encoding="utf-8")

    return {
        "rayforge_commit": commit,
        "hardware_access": False,
        "model": {
            "layer_visible": layer.visible,
            "step_visible": step.visible,
            "states_are_independent": (
                layer.visible is False and step.visible is True
            ),
            "roundtrip": {
                "layer_name": restored.name,
                "layer_color": restored.color,
                "layer_visible": restored.visible,
                "step_name": restored_step.name if restored_step else None,
                "step_visible": (
                    restored_step.visible if restored_step else None
                ),
            },
            "serialized_layer_order": serialized_order,
        },
        "source_contract": {
            "canvas_checks_layer_visibility": (
                "if not self.visible" in render_source
            ),
            "job_pipeline_checks_step_visibility": (
                "if not step.visible" in build_source
            ),
            "job_pipeline_checks_layer_visibility": (
                "layer.visible" in build_source
            ),
            "layer_visibility_control": (
                "Toggle layer visibility" in layer_ui
            ),
            "step_visibility_control": "Toggle step visibility" in step_ui,
        },
        "conclusion": (
            "Rayforge separates canvas visibility at layer level from output "
            "participation at workflow-step level; a LightBurn-style layer "
            "Output control can be an aggregate UI over existing step states."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rayforge_checkout", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = characterize(args.rayforge_checkout.resolve())
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    print(f"sha256={hashlib.sha256(payload.encode()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
