"""Characterize a synthetic JCZ LightBurn device import in pinned Rayforge.

The fixture contains only public, synthetic values.  This spike performs no
device discovery or transport and deliberately does not add a JCZ driver.
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


def run(source: Path, fixture: Path, addon: Path) -> dict[str, object]:
    commit = _commit_of(source)
    if commit != RAYFORGE_COMMIT:
        raise RuntimeError(f"expected Rayforge {RAYFORGE_COMMIT}, found {commit}")
    sys.path.insert(0, str(source))

    from rayforge.machine.device.lightburn_importer import (
        convert_to_profile,
        parse_lbdev,
    )

    raw = parse_lbdev(fixture)
    profile, summary = convert_to_profile(fixture)
    document = json.loads(fixture.read_text(encoding="utf-8"))
    sys.path.insert(0, str(addon))
    from pirate_ray_jcz.profile_import import import_lightburn_jcz_profile

    seam = import_lightburn_jcz_profile(document)
    settings = raw["Settings"]
    cut_entry = raw["CutList"][0]

    if raw["Type"] != "JCZFiber":
        raise AssertionError("synthetic fixture is not a JCZFiber profile")
    if profile.machine_config.axis_extents != (110.0, 110.0):
        raise AssertionError("work area did not survive import")
    if profile.machine_config.driver is not None or summary.driver is not None:
        raise AssertionError("pinned Rayforge unexpectedly mapped a JCZ driver")

    return {
        "rayforge_commit": commit,
        "transport": None,
        "fixture": fixture.name,
        "fixture_provenance": "synthetic public data",
        "raw_profile": {
            "name": raw["DisplayName"],
            "type": raw["Type"],
            "work_area_mm": [raw["Width"], raw["Height"]],
            "require_frame_before_start": settings[
                "RequireFrameBeforeStart"
            ],
            "cut_entry": {
                "frequency": cut_entry["frequency"],
                "QPulseWidth": cut_entry["QPulseWidth"],
            },
        },
        "mapped_profile": {
            "name": profile.meta.name,
            "driver": profile.machine_config.driver,
            "work_area_mm": list(profile.machine_config.axis_extents),
            "home_on_start": profile.machine_config.home_on_start,
        },
        "addon_profile_seam": seam,
        "gap_matrix": {
            "jczfiber_driver_mapped": profile.machine_config.driver is not None,
            "require_frame_before_start_mapped": False,
            "cut_list_mapped": False,
            "frequency_mapped": False,
            "q_pulse_width_mapped": False,
            "safe_for_jcz_use": False,
        },
        "conclusion": (
            "name and work area survive, but JCZFiber has no driver mapping; "
            "RequireFrameBeforeStart, CutList, frequency and QPulseWidth are "
            "not represented in the imported Rayforge profile"
        ),
    }


def main() -> None:
    root = Path(__file__).parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="pinned Rayforge checkout")
    parser.add_argument(
        "--addon",
        type=Path,
        default=root / "spikes" / "rayforge-jcz-no-device-addon",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=root / "tests" / "fixtures" / "synthetic-jcz-device.lbdev",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(
        args.source.resolve(), args.fixture.resolve(), args.addon.resolve()
    )
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
