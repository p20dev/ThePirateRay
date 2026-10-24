"""Fail-closed LightBurn JCZ profile seam with no hardware capability."""

from __future__ import annotations

from typing import Any


DRIVER_NAME = "PirateRayJCZNoDeviceDriver"
SYNTHETIC_PROFILE_ID = "synthetic-jpt-mopa-110-v1"
EVIDENCE_APP_VERSION = "2.1.03"
EVIDENCE_WORK_AREA_MM = (110, 110)
EVIDENCE_FIBER_TYPE_RAW = 3
EVIDENCE_FIBER_TYPE_UI_LABEL = "IPG_YLPM"
FREQUENCY_HZ_PER_KHZ = 1000


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

    The returned process values use the independently observed LightBurn
    2.1.03 Hz/ns serialization contract. This function does not infer physical
    machine identity, safe operating limits, lens correction, controller
    transport, or hardware compatibility.
    """

    if document.get("FixtureProvenance") != (
        "synthetic public data; not a machine export"
    ):
        raise JCZProfileImportError("profile provenance is absent or unsupported")
    if document.get("SyntheticProfileId") != SYNTHETIC_PROFILE_ID:
        raise JCZProfileImportError("synthetic profile identity mismatch")
    if document.get("AppVersion") != EVIDENCE_APP_VERSION:
        raise JCZProfileImportError("unsupported LightBurn AppVersion")

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
    if (width, height) != EVIDENCE_WORK_AREA_MM:
        raise JCZProfileImportError("synthetic JPT profile must use 110 x 110 mm")

    settings = device.get("Settings")
    if not isinstance(settings, dict) or settings.get(
        "RequireFrameBeforeStart"
    ) is not True:
        raise JCZProfileImportError("RequireFrameBeforeStart must be explicitly true")
    if settings.get("Laser_QPulseWidthEnabled") is not True:
        raise JCZProfileImportError("Q-pulse-width control must be explicitly enabled")
    if settings.get("Laser_FiberType") != EVIDENCE_FIBER_TYPE_RAW:
        raise JCZProfileImportError("observed fiber-type code mismatch")
    min_frequency = settings.get("Laser_MinFreq")
    max_frequency = settings.get("Laser_MaxFreq")
    if not all(
        _is_positive_number(value) for value in (min_frequency, max_frequency)
    ) or min_frequency > max_frequency:
        raise JCZProfileImportError("valid observed frequency range is required")

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
        frequency_khz = frequency / FREQUENCY_HZ_PER_KHZ
        if not min_frequency <= frequency_khz <= max_frequency:
            raise JCZProfileImportError(
                "cut-list frequency is outside the observed profile range"
            )
        preserved_entries.append(
            {
                "name": entry.get("Name", ""),
                "frequency": {
                    "raw_value": frequency,
                    "serialized_unit": "Hz",
                    "value_hz": frequency,
                    "value_khz": frequency_khz,
                },
                "q_pulse_width": {
                    "raw_value": pulse_width,
                    "serialized_unit": "ns",
                    "value_ns": pulse_width,
                },
            }
        )

    return {
        "profile_id": SYNTHETIC_PROFILE_ID,
        "driver": DRIVER_NAME,
        "transport": None,
        "source": {
            "format": "LightBurn synthetic .lbdev",
            "app_version": document["AppVersion"],
            "provenance": document["FixtureProvenance"],
            "backend": "JCZFiber",
        },
        "work_area_mm": [float(width), float(height)],
        "safety": {"require_frame_before_start": True},
        "observed_device_contract": {
            "q_pulse_width_enabled": True,
            "frequency_ui_range_khz": [min_frequency, max_frequency],
            "frequency_serialized_unit": "Hz",
            "q_pulse_width_serialized_unit": "ns",
            "fiber_type_raw": EVIDENCE_FIBER_TYPE_RAW,
            "fiber_type_ui_label": EVIDENCE_FIBER_TYPE_UI_LABEL,
            "fiber_type_identity_status": "label-is-not-manufacturer-identity",
        },
        "process_metadata": {
            "status": "normalized-offline-not-authorized",
            "cut_list": preserved_entries,
        },
        "encoding_allowed": False,
        "blockers": [
            "synthetic profile is not physical machine identity",
            "lens and correction profile are unverified",
            "IPG_YLPM UI label is not manufacturer identity",
            "observed profile ranges are not certified safe machine limits",
            "image settings with absent QPulseWidth remain unresolved",
        ],
    }
