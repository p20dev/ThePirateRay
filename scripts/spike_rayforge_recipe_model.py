"""Characterize Rayforge recipe matching and metadata extension seams."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


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


class SyntheticLaserStep:
    power = 0.5
    frequency = 30000
    pulse_width = 200

    @classmethod
    def recipe_keys(cls) -> tuple[str, ...]:
        return ("power", "frequency", "pulse_width")


def characterize(root: Path) -> dict:
    commit = checkout_commit(root)
    if commit != RAYFORGE_COMMIT:
        raise RuntimeError(
            f"Expected Rayforge {RAYFORGE_COMMIT}, found {commit}"
        )

    sys.path.insert(0, str(root))
    from rayforge.core.recipe import Recipe

    recipe = Recipe.from_dict(
        {
            "uid": "synthetic-jpt-marking",
            "name": "Synthetic JPT marking",
            "description": "Public model fixture; not machine settings",
            "target_step_types": ["SyntheticLaserStep"],
            "target_machine_id": "synthetic-jpt-profile",
            "material_uid": "synthetic-stainless-steel",
            "min_thickness_mm": 0.5,
            "max_thickness_mm": 2.0,
            "setting_dicts": [
                {"name": "power", "value": 0.5, "recipe_apply": True},
                {
                    "name": "frequency",
                    "value": 30000,
                    "recipe_apply": True,
                },
                {
                    "name": "pulse_width",
                    "value": 200,
                    "recipe_apply": True,
                },
                {
                    "name": "unsupported_private_field",
                    "value": "ignored",
                    "recipe_apply": True,
                },
                {
                    "name": "air_assist",
                    "value": True,
                    "recipe_apply": False,
                },
            ],
            "pirateray_provenance": {
                "status": "synthetic-unverified",
                "source": "public-model-fixture",
            },
        }
    )

    matching_stock = SimpleNamespace(
        material_uid="synthetic-stainless-steel", thickness=1.0
    )
    wrong_stock = SimpleNamespace(
        material_uid="synthetic-aluminum", thickness=1.0
    )
    machine = SimpleNamespace(id="synthetic-jpt-profile", heads=[])
    roundtrip = Recipe.from_dict(recipe.to_dict())
    allowed_settings = recipe.get_settings_for_step(SyntheticLaserStep())

    recipe_source = (root / "rayforge" / "core" / "recipe.py").read_text(
        encoding="utf-8"
    )
    manager_source = (
        root / "rayforge" / "core" / "recipe_manager.py"
    ).read_text(encoding="utf-8")
    laser_source = (
        root
        / "rayforge"
        / "builtin_addons"
        / "rayforge-addon-laser"
        / "laser_essentials"
        / "steps"
        / "laser_step.py"
    ).read_text(encoding="utf-8")

    return {
        "rayforge_commit": commit,
        "hardware_access": False,
        "model": {
            "applied_settings": recipe.get_applied_settings(),
            "step_allowlisted_settings": allowed_settings,
            "unknown_setting_rejected_by_step": (
                "unsupported_private_field" not in allowed_settings
            ),
            "disabled_setting_left_unchanged": (
                "air_assist" not in recipe.get_applied_settings()
            ),
            "matches_complete_context": recipe.matches(
                [matching_stock], machine, "SyntheticLaserStep"
            ),
            "rejects_wrong_material": not recipe.matches(
                [wrong_stock], machine, "SyntheticLaserStep"
            ),
            "rejects_missing_stock_context": not recipe.matches(
                [], machine, "SyntheticLaserStep"
            ),
            "extra_metadata_roundtrip": roundtrip.extra,
        },
        "source_contract": {
            "machine_match": "target_machine_id" in recipe_source,
            "head_match": "selected_head_uid" in recipe_source,
            "material_match": "material_uid" in recipe_source,
            "thickness_match": all(
                key in recipe_source
                for key in ("min_thickness_mm", "max_thickness_mm")
            ),
            "step_type_match": "target_step_types" in recipe_source,
            "file_per_recipe_yaml": (
                'f"{recipe_id}.yaml"' in manager_source
            ),
            "forward_compatible_extra_metadata": (
                "result.update(self.extra)" in recipe_source
            ),
            "frequency_hz": "Laser pulse frequency in Hz" in laser_source,
            "pulse_width_ns": "Laser pulse width in ns" in laser_source,
            "native_approval_status": "approval_status" in recipe_source,
            "native_provenance": "provenance" in recipe_source,
            "native_lens_match": "lens" in recipe_source,
            "native_correction_match": "correction" in recipe_source,
            "native_named_collections": "collection" in manager_source,
        },
        "conclusion": (
            "Reuse Rayforge recipes and their matching/allowlist behavior. "
            "Add PirateRay provenance, approval, lens and correction metadata "
            "through a narrow validated extension before adding new UI."
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
