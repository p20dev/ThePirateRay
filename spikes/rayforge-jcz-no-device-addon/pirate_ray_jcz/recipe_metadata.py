"""Fail-closed PirateRay metadata for Rayforge recipes."""

from __future__ import annotations

from typing import Any, Mapping


METADATA_KEY = "pirateray"
SCHEMA_VERSION = 1
SUPPORTED_STATUS = "unverified"
COMPATIBILITY_KEYS = (
    "machine_profile_id",
    "source_type",
    "lens_profile_id",
    "correction_profile_sha256",
)


class RecipeMetadataError(ValueError):
    """Raised when recipe evidence or compatibility is incomplete."""


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RecipeMetadataError(f"{label} must be an object")
    return value


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RecipeMetadataError(f"{label} must be non-empty text")
    return value


def validate_recipe_metadata(
    metadata: Mapping[str, Any],
    active_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate evidence and exact compatibility without enabling hardware.

    Only ``unverified`` recipes are representable until an approval policy is
    reviewed. Compatibility identifiers are opaque evidence-backed values;
    this function does not infer or normalize machine configuration.
    """

    metadata = _require_mapping(metadata, METADATA_KEY)
    if metadata.get("schema_version") != SCHEMA_VERSION:
        raise RecipeMetadataError("unsupported PirateRay recipe schema")
    if metadata.get("status") != SUPPORTED_STATUS:
        raise RecipeMetadataError(
            "recipe status is unsupported until approval policy is reviewed"
        )

    provenance = _require_mapping(
        metadata.get("provenance"), "provenance"
    )
    provenance_kind = _require_text(
        provenance.get("kind"), "provenance.kind"
    )
    provenance_reference = _require_text(
        provenance.get("reference"), "provenance.reference"
    )

    compatibility = _require_mapping(
        metadata.get("compatibility"), "compatibility"
    )
    active_context = _require_mapping(active_context, "active_context")
    normalized_compatibility = {}
    for key in COMPATIBILITY_KEYS:
        expected = _require_text(
            compatibility.get(key), f"compatibility.{key}"
        )
        actual = _require_text(active_context.get(key), f"active_context.{key}")
        if actual != expected:
            raise RecipeMetadataError(f"recipe {key} does not match")
        normalized_compatibility[key] = expected

    return {
        "schema_version": SCHEMA_VERSION,
        "status": SUPPORTED_STATUS,
        "provenance": {
            "kind": provenance_kind,
            "reference": provenance_reference,
        },
        "compatibility": normalized_compatibility,
        "encoding_allowed": False,
        "hardware_use_allowed": False,
    }


def validate_rayforge_recipe(recipe: Any, active_context: Mapping[str, Any]):
    """Read the namespaced block from ``Recipe.extra`` and validate it."""

    extra = getattr(recipe, "extra", None)
    if not isinstance(extra, Mapping) or METADATA_KEY not in extra:
        raise RecipeMetadataError("PirateRay recipe metadata is missing")
    return validate_recipe_metadata(extra[METADATA_KEY], active_context)
