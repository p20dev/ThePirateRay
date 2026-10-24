"""Present and enforce unresolved PirateRay workflow import blockers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .workflow_import import METADATA_KEY


class ImportPreflightError(RuntimeError):
    """A staged import is not eligible for job execution."""


def _walk(items: Iterable[Any]):
    for item in items:
        yield item
        children = getattr(item, "children", ())
        if children:
            yield from _walk(children)


def inspect_imported_workflow(doc: Any) -> dict[str, Any]:
    """Return stable, UI-ready errors for every staged import in a document."""
    issues = []
    items = getattr(doc, "children", None)
    if items is None:
        issues.append({
            "code": "IMPORT_DOCUMENT_INVALID",
            "severity": "error",
            "message": "Document tree is unavailable for PirateRay preflight.",
        })
        return {"ready": False, "issues": issues}

    for step in _walk(items):
        extra = getattr(step, "extra", None)
        if not isinstance(extra, Mapping) or METADATA_KEY not in extra:
            continue
        record = extra[METADATA_KEY]
        name = getattr(step, "name", "Imported workflow step")
        if not isinstance(record, Mapping):
            issues.append({
                "code": "IMPORT_METADATA_INVALID", "severity": "error",
                "step": name,
                "message": "PirateRay import review data is malformed.",
            })
            continue
        layer_id = record.get("source_layer_id")
        if getattr(step, "visible", False):
            issues.append({
                "code": "IMPORT_OUTPUT_REENABLED", "severity": "error",
                "step": name, "source_layer_id": layer_id,
                "message": "Imported output was re-enabled before review completed.",
            })
        blockers = record.get("blockers")
        if not isinstance(blockers, list) or not blockers or not all(
            isinstance(value, str) and value for value in blockers
        ):
            issues.append({
                "code": "IMPORT_METADATA_INVALID", "severity": "error",
                "step": name, "source_layer_id": layer_id,
                "message": "PirateRay import blockers are missing or malformed.",
            })
            continue
        issues.append({
            "code": "IMPORT_REVIEW_REQUIRED", "severity": "error",
            "step": name, "source_layer_id": layer_id,
            "message": "Imported MOPA settings require review: " + "; ".join(blockers),
            "blockers": list(blockers),
        })
    return {"ready": not issues, "issues": issues}


def assert_no_unresolved_imports(doc: Any) -> None:
    """Fail before an encoded job reaches even the offline session."""
    report = inspect_imported_workflow(doc)
    if not report["ready"]:
        codes = ", ".join(issue["code"] for issue in report["issues"])
        raise ImportPreflightError(f"PirateRay import preflight failed: {codes}")
