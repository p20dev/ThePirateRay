"""Build a UI-neutral presentation of PirateRay import preflight results."""

from __future__ import annotations

from collections.abc import Mapping
from gettext import gettext as _
from typing import Any


def _invalid_report() -> dict[str, str]:
    return {
        "status": "blocked",
        "heading": _("Import preflight blocked"),
        "body": _(
            "The preflight report is malformed. Output remains disabled."
        ),
    }


def format_preflight_report(report: Any) -> dict[str, str]:
    """Return localized heading and body text for the packaged GTK dialog."""
    if not isinstance(report, Mapping):
        return _invalid_report()
    ready = report.get("ready")
    issues = report.get("issues")
    if not isinstance(ready, bool) or not isinstance(issues, list):
        return _invalid_report()
    if ready:
        if issues:
            return _invalid_report()
        return {
            "status": "ready",
            "heading": _("Import preflight ready"),
            "body": _("No unresolved PirateRay import blockers were found."),
        }
    if not issues:
        return _invalid_report()

    lines = []
    for issue in issues:
        if not isinstance(issue, Mapping):
            return _invalid_report()
        code = issue.get("code")
        message = issue.get("message")
        if not isinstance(code, str) or not code:
            return _invalid_report()
        if not isinstance(message, str) or not message:
            return _invalid_report()
        lines.append(f"{code}: {message}")

    prefix = _(
        "Resolve every issue before enabling output. Output remains disabled."
    )
    return {
        "status": "blocked",
        "heading": _("Import preflight blocked"),
        "body": prefix + "\n\n" + "\n".join(lines),
    }
