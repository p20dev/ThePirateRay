"""Fail-closed LightBurn JCZ profile seam with no hardware capability."""

from __future__ import annotations

from typing import Any


DRIVER_NAME = "PirateRayJCZNoDeviceDriver"
SYNTHETIC_PROFILE_ID = "synthetic-jpt-mopa-110-v1"


class JCZProfileImportError(ValueError):
    """Raised when a LightBurn profile cannot be recognized safely."""


def _is_positive_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value > 0
    )


def import_lightburn_jcz_profile(document: dict[str, Any]) -> dict[str, Any]:
    """Recognize the public synthetic profile without enabling encoding.

    The returned process values remain serialized raw observations.  This
    function does not infer LightBurn project fields, units, machine limits,
    lens correction, controller transport, or hardware compatibility.
    """

    if document.get("FixtureProvenance") != (
        "synthetic public data; not a machine export"
    ):
        raise JCZProfileImportError("profile provenance is absent or unsupported")
    if document.get("SyntheticProfileId") != SYNTHETIC_PROFILE_ID:
        raise JCZProfileImportError("synthetic profile identity mismatch")

    devices = document.get("DeviceList")
    if not isinstance(devices, list) or len(devices) != 1:
        raise JCZProfileImportError("exactly one LightBurn device is required")
    device = devices[0]
    if not isinstance(device, dict) or device.get("Type") != "JCZFiber":
        raise JCZProfileImportError("LightBurn device is not JCZFiber")

    width = device.get("Width")
    height = device.get("Height")
    if not all(_is_positive_number(value) for value in (width, height)):
        raise JCZProfileImportError("positive work-area dimensions are required")

    settings = device.get("Settings")
    if not isinstance(settings, dict) or settings.get(
        "RequireFrameBeforeStart"
    ) is not True:
        raise JCZProfileImportError("RequireFrameBeforeStart must be explicitly true")

    cut_list = device.get("CutList")
    if not isinstance(cut_list, list) or not cut_list:
        raise JCZProfileImportError("at least one observed cut-list entry is required")

    preserved_entries = []
    for entry in cut_list:
        if not isinstance(entry, dict):
            raise JCZProfileImportError("cut-list entry must be an object")
        frequency = entry.get("frequency")
        pulse_width = entry.get("QPulseWidth")
        if not all(
            _is_positive_number(value) for value in (frequency, pulse_width)
        ):
            raise JCZProfileImportError(
                "frequency and QPulseWidth must be positive raw values"
            )
        preserved_entries.append(
            {
                "name": entry.get("Name", ""),
                "frequency": {
                    "raw_value": frequency,
                    "unit_status": "serialized-unit-conversion-unverified",
                },
                "q_pulse_width": {
                    "raw_value": pulse_width,
                    "ui_unit_contract": "nanoseconds",
                    "serialized_unit_conversion": "unverified",
                },
            }
        )

    return {
        "profile_id": SYNTHETIC_PROFILE_ID,
        "driver": DRIVER_NAME,
        "transport": None,
        "source": {
            "format": "LightBurn synthetic .lbdev",
            "provenance": document["FixtureProvenance"],
            "backend": "JCZFiber",
        },
        "work_area_mm": [float(width), float(height)],
        "safety": {"require_frame_before_start": True},
        "process_metadata": {
            "status": "preserved-raw-not-mapped",
            "cut_list": preserved_entries,
        },
        "encoding_allowed": False,
        "blockers": [
            "synthetic profile is not physical machine identity",
            "lens and correction profile are unverified",
            "LightBurn project QPulseWidth serialization is unverified",
            "machine-specific parameter limits are unverified",
        ],
    }
