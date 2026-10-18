"""Inspect a synthetic LightBurn MOPA layer through pinned Rayforge.

This script performs no discovery or device I/O.  It records which observed
LightBurn values survive Rayforge's importer boundary without inventing a
pulse-width field that is absent from the inspected fixture evidence.
"""

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


def run(source: Path, fixture: Path) -> dict[str, object]:
    commit = _commit_of(source)
    if commit != RAYFORGE_COMMIT:
        raise RuntimeError(f"expected Rayforge {RAYFORGE_COMMIT}, found {commit}")
    sys.path.insert(0, str(source))

    from rayforge.core.vectorization_spec import (
        LayerImportMode,
        PassthroughSpec,
    )
    from rayforge.image.lightburn.importer import LightBurnImporter

    data = fixture.read_bytes()
    importer = LightBurnImporter(data, source_file=fixture)
    manifest = importer.scan()
    parsed = importer.parse()
    if parsed is None:
        raise AssertionError("synthetic LightBurn fixture did not parse")
    vectorized = importer.vectorize(
        parsed,
        PassthroughSpec(layer_import_mode=LayerImportMode.NEW_LAYERS),
    )
    source_asset = importer.create_source_asset(parsed)

    raw = source_asset.metadata["lightburn_cut_settings"][
        "Synthetic MOPA layer"
    ]
    mapped = vectorized.layer_settings["0"]
    geometry = vectorized.geometries_by_layer["0"]
    bounds = [round(value, 6) for value in geometry.rect()]

    expected_raw = {
        "maxPower": 50,
        "speed": 250,
        "frequency": 40000,
        "overrideFrequency": 1,
    }
    if any(raw.get(key) != value for key, value in expected_raw.items()):
        raise AssertionError("raw LightBurn values changed during import")
    if mapped.get("power") != 0.5 or mapped.get("cut_speed") != 15000:
        raise AssertionError("power or speed mapping changed")
    if "frequency" in mapped or "pulse_width" in mapped:
        raise AssertionError("MOPA mapping changed; re-evaluate this spike")

    return {
        "rayforge_commit": commit,
        "transport": None,
        "fixture": fixture.name,
        "fixture_provenance": "synthetic public data",
        "manifest": {
            "title": manifest.title,
            "layers": [
                {
                    "id": layer.id,
                    "name": layer.name,
                    "feature_count": layer.feature_count,
                }
                for layer in manifest.layers
            ],
            "errors": [str(error) for error in manifest.errors],
        },
        "geometry_bounds_mm": bounds,
        "raw_cut_setting": {
            key: raw[key]
            for key in (
                "maxPower",
                "speed",
                "frequency",
                "overrideFrequency",
                "numPasses",
            )
        },
        "mapped_layer_settings": mapped,
        "mopa_survival": {
            "frequency_preserved_in_source_metadata": raw["frequency"] == 40000,
            "frequency_mapped_to_workflow": "frequency" in mapped,
            "pulse_width_source_field_observed": False,
            "pulse_width_mapped_to_workflow": "pulse_width" in mapped,
            "safe_for_jcz_encoding": False,
        },
        "conclusion": (
            "geometry, power, speed and passes survive; frequency remains only "
            "in source metadata and no evidence-backed pulse-width field is mapped"
        ),
    }


def main() -> None:
    root = Path(__file__).parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="pinned Rayforge checkout")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=root / "tests" / "fixtures" / "synthetic-mopa-import.lbrn2",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.source.resolve(), args.fixture.resolve())
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
