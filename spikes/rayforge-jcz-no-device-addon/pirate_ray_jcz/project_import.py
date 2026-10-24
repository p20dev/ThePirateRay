"""Transport-free LightBurn MOPA import seam; never authorizes encoding."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import xml.etree.ElementTree as ET


UNIT_CONTRACT = "frequency=Hz;QPulseWidth=ns"


class ProjectImportError(ValueError):
    """Ambiguous or malformed process metadata."""


def _number(element: ET.Element, field: str) -> str | None:
    children = element.findall(field)
    if not children:
        return None
    if len(children) != 1 or set(children[0].attrib) != {"Value"}:
        raise ProjectImportError(f"ambiguous {field}")
    raw = children[0].get("Value", "")
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise ProjectImportError(f"invalid {field}") from exc
    if not value.is_finite() or value <= 0 or value > Decimal("1e12"):
        raise ProjectImportError(f"invalid {field}")
    return raw


def _layer_id(element: ET.Element) -> str | None:
    children = element.findall("index")
    if not children:
        return None
    if len(children) != 1 or set(children[0].attrib) != {"Value"}:
        raise ProjectImportError("ambiguous layer index")
    raw = children[0].get("Value", "")
    if not raw.isdecimal():
        raise ProjectImportError("invalid layer index")
    return str(int(raw))


def import_project_mopa(data: bytes, *, unit_contract: str | None = None) -> dict:
    """Preserve observed XML fields and optionally normalize declared units.

    The caller must supply an independently established serialized-unit contract.
    No unit is inferred from magnitude. Missing pulse width is never defaulted.
    Results are offline metadata, not executable Rayforge workflow settings.
    """
    if unit_contract not in (None, UNIT_CONTRACT):
        raise ProjectImportError("unsupported serialized-unit contract")
    if len(data) > 64 * 1024 * 1024:
        raise ProjectImportError("project exceeds offline import size limit")
    # Reject declarations, including UTF-16/32 encodings, before XML parsing.
    probe = data.replace(b"\x00", b"").upper()
    if b"<!DOCTYPE" in probe or b"<!ENTITY" in probe:
        raise ProjectImportError("XML declarations are unsupported")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ProjectImportError("invalid project XML") from exc
    if root.tag != "LightBurnProject" or root.get("FormatVersion") != "1":
        raise ProjectImportError("unsupported project format")
    layers = []
    layer_ids: set[str] = set()
    for setting in root:
        if setting.tag not in ("CutSetting", "CutSetting_Img"):
            continue
        kind = setting.get("type")
        expected = ("Image",) if setting.tag == "CutSetting_Img" else ("Cut", "Scan")
        if kind not in expected:
            raise ProjectImportError("unsupported layer type")
        layer_id = _layer_id(setting)
        if layer_id is not None and layer_id in layer_ids:
            raise ProjectImportError("duplicate layer index")
        if layer_id is not None:
            layer_ids.add(layer_id)
        raw = {key: _number(setting, key) for key in ("frequency", "QPulseWidth")}
        blockers = []
        if unit_contract is None:
            blockers.append("serialized units unresolved")
        for key, value in raw.items():
            if value is None:
                blockers.append(f"{key} absent; explicit resolution required")
        if kind == "Image":
            blockers.append("image processing equivalence unverified")
        modes = setting.findall("ditherMode")
        if len(modes) > 1 or (modes and set(modes[0].attrib) != {"Value"}):
            raise ProjectImportError("ambiguous image mode")
        image_mode = modes[0].get("Value") if modes else None
        normalized = None
        if unit_contract and all(value is not None for value in raw.values()):
            normalized = {
                "frequency_hz": float(Decimal(raw["frequency"])),
                "frequency_khz": float(Decimal(raw["frequency"]) / 1000),
                "pulse_width_ns": float(Decimal(raw["QPulseWidth"])),
            }
        layers.append({"element": setting.tag, "type": kind,
                       "source_layer_id": layer_id, "raw": raw,
                       "image_mode": image_mode,
                       "normalized": normalized, "blockers": blockers})
    if not layers:
        raise ProjectImportError("project has no process settings")
    return {"layers": layers, "unit_contract": unit_contract, "transport": None,
            "encoding_allowed": False, "hardware_use_allowed": False,
            "blockers": ["machine identity, correction and limits unverified",
                         "offline import seam is not wired to host workflow"]}
