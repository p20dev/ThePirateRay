"""Stage MOPA metadata on Rayforge workflow steps with output disabled."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


METADATA_KEY = "pirateray_import"


class WorkflowImportError(ValueError):
    """The imported layer cannot be bound safely to a Rayforge step."""


def _host_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise WorkflowImportError(f"{label} must be numeric")
    result = int(value)
    if result <= 0 or result != value:
        raise WorkflowImportError(f"{label} must be a positive integer")
    return result


def stage_mopa_workflow_steps(
    imported: Mapping[str, Any],
    steps_by_layer_id: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind complete imported MOPA settings while keeping every step disabled.

    The mapping is constructed by the host integration from the source segment's
    ``layer_id`` to the single workflow step created by Rayforge's assembler.
    This seam never enables a step and never removes an existing blocker.
    """
    if imported.get("encoding_allowed") is not False:
        raise WorkflowImportError("import must explicitly prohibit encoding")
    if imported.get("hardware_use_allowed") is not False:
        raise WorkflowImportError("import must explicitly prohibit hardware use")
    layers = imported.get("layers")
    if not isinstance(layers, list):
        raise WorkflowImportError("imported layers are missing")

    by_id: dict[str, Mapping[str, Any]] = {}
    for layer in layers:
        if not isinstance(layer, Mapping):
            raise WorkflowImportError("imported layer must be an object")
        layer_id = layer.get("source_layer_id")
        if layer_id is None:
            continue
        if not isinstance(layer_id, str) or layer_id in by_id:
            raise WorkflowImportError("imported layer identity is ambiguous")
        by_id[layer_id] = layer
    if not steps_by_layer_id:
        raise WorkflowImportError("no Rayforge workflow steps were supplied")

    global_blockers = imported.get("blockers")
    if not isinstance(global_blockers, list) or not all(
        isinstance(item, str) and item for item in global_blockers
    ):
        raise WorkflowImportError("global blockers are missing")

    plans = []
    step_identities: set[int] = set()
    for layer_id, step in steps_by_layer_id.items():
        if not isinstance(layer_id, str):
            raise WorkflowImportError("Rayforge layer ID must be text")
        if id(step) in step_identities:
            raise WorkflowImportError("one Rayforge step cannot represent multiple layers")
        step_identities.add(id(step))
        layer = by_id.get(layer_id)
        if layer is None:
            raise WorkflowImportError(f"no imported settings for layer {layer_id}")
        if not isinstance(getattr(step, "extra", None), dict):
            raise WorkflowImportError("Rayforge step has no serializable extra data")
        if METADATA_KEY in step.extra:
            raise WorkflowImportError("Rayforge step already has PirateRay import data")
        if not hasattr(step, "visible") or not callable(
            getattr(step, "set_visible", None)
        ):
            raise WorkflowImportError("Rayforge step has no output visibility gate")
        normalized = layer.get("normalized")
        layer_blockers = layer.get("blockers")
        if not isinstance(layer_blockers, list):
            raise WorkflowImportError("layer blockers are missing")
        apply_values = normalized is not None and not layer_blockers
        frequency = pulse_width = None
        if apply_values:
            if not callable(getattr(step, "set_frequency", None)) or not callable(
                getattr(step, "set_pulse_width", None)
            ):
                raise WorkflowImportError("Rayforge step has no MOPA setters")
            frequency = _host_integer(normalized.get("frequency_hz"), "frequency")
            pulse_width = _host_integer(
                normalized.get("pulse_width_ns"), "pulse width"
            )
        plans.append((layer_id, step, layer, frequency, pulse_width))

    snapshots = [
        (step, step.visible, deepcopy(step.extra), getattr(step, "frequency", None),
         getattr(step, "pulse_width", None))
        for _layer_id, step, _layer, _frequency, _pulse_width in plans
    ]
    staged = []
    try:
        for layer_id, step, layer, frequency, pulse_width in plans:
            step.set_visible(False)
            blockers = list(global_blockers) + list(layer["blockers"])
            if frequency is not None and pulse_width is not None:
                step.set_frequency(frequency)
                step.set_pulse_width(pulse_width)
            step.extra[METADATA_KEY] = {
                "status": "staged-review-required",
                "source_layer_id": layer_id,
                "raw": deepcopy(layer.get("raw")),
                "normalized": deepcopy(layer.get("normalized")),
                "blockers": blockers,
                "encoding_allowed": False,
                "hardware_use_allowed": False,
            }
            staged.append({
                "source_layer_id": layer_id,
                "parameters_applied": frequency is not None,
                "output_enabled": False,
                "blockers": blockers,
            })
    except Exception:
        for step, visible, extra, frequency, pulse_width in snapshots:
            step.set_visible(visible)
            step.extra.clear()
            step.extra.update(extra)
            if frequency is not None:
                step.frequency = frequency
            if pulse_width is not None:
                step.pulse_width = pulse_width
        raise
    return {"steps": staged, "encoding_allowed": False,
            "hardware_use_allowed": False, "transport": None}
