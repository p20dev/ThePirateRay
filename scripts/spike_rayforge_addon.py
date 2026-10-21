"""Exercise the external Rayforge addon and binary-driver lifecycle."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock


PINNED_COMMIT = "c28918c87f8273dd1d244f5a057addc192807fa5"
ADDON_NAME = "the_pirate_ray_jcz"
DRIVER_NAME = "PirateRayJCZNoDeviceDriver"


def _commit_of(source: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def run(source: Path, addon_path: Path) -> dict[str, object]:
    commit = _commit_of(source)
    if commit != PINNED_COMMIT:
        raise RuntimeError(f"expected Rayforge {PINNED_COMMIT}, found {commit}")

    sys.path.insert(0, str(source))
    from rayforge.addon_mgr.addon import Addon
    from rayforge.addon_mgr.addon_manager import AddonManager
    from rayforge.core.addon_config import AddonConfig
    from rayforge.core.hooks import RayforgeSpecs
    from rayforge.machine import driver as driver_registry
    import pluggy

    parsed = Addon.load_from_directory(addon_path, version="0.1.0")
    parsed.validate()

    scratch = Path.cwd() / "reports"
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="tpr-rayforge-addon-", dir=scratch
    ) as temp:
        root = Path(temp)
        config = AddonConfig(root / "config")
        plugin_mgr = pluggy.PluginManager("rayforge")
        plugin_mgr.add_hookspecs(RayforgeSpecs)
        manager = AddonManager(
            [addon_path.parent],
            addon_path.parent,
            plugin_mgr,
            MagicMock(),
            addon_config=config,
            registries={},
        )

        manager.load_addon(addon_path, worker_only=True, version="0.1.0")
        driver = driver_registry.get_driver_cls(DRIVER_NAME)
        if driver.__name__ != DRIVER_NAME or driver.uses_gcode:
            raise AssertionError("external binary driver was not registered")
        encoded = driver.create_encoder(None).encode(None)
        if not encoded.driver_data.get("binary"):
            raise AssertionError("binary encoder payload missing")
        if encoded.driver_data.get("transport") is not None:
            raise AssertionError("offline encoder unexpectedly has transport")

        if not manager.disable_addon(ADDON_NAME):
            raise AssertionError("addon did not disable cleanly")
        if DRIVER_NAME in driver_registry.driver_by_classname:
            raise AssertionError("driver remained registered after disable")

        if not manager.enable_addon(ADDON_NAME):
            raise AssertionError("addon did not re-enable cleanly")
        if driver_registry.get_driver_cls(DRIVER_NAME).__name__ != DRIVER_NAME:
            raise AssertionError("driver did not re-register after enable")

        if not manager.reload_addon(ADDON_NAME):
            raise AssertionError("addon did not reload cleanly")
        matches = [
            cls for cls in driver_registry.drivers if cls.__name__ == DRIVER_NAME
        ]
        if len(matches) != 1:
            raise AssertionError("driver registry duplicated on reload")

        package = root / "the_pirate_ray_jcz-0.1.0.zip"
        with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(addon_path.rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts:
                    archive.write(path, path.relative_to(addon_path))
        with zipfile.ZipFile(package) as archive:
            packaged_files = sorted(archive.namelist())

        manager.disable_addon(ADDON_NAME)

    return {
        "upstream": "barebaric/rayforge",
        "commit": commit,
        "rayforge_api_version": parsed.metadata.api_version,
        "addon": ADDON_NAME,
        "driver": DRIVER_NAME,
        "uses_gcode": False,
        "discovery": None,
        "transport": None,
        "binary_payload_hex": (
            b'[{"command":"offline_probe"}]'.hex()
        ),
        "lifecycle": ["load", "disable", "enable", "reload", "disable"],
        "packaged_files": packaged_files,
        "registration_seam": (
            "fail-closed API 23 compatibility adapter + on_unload cleanup"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="pinned Rayforge checkout")
    parser.add_argument(
        "--addon",
        type=Path,
        default=(
            Path(__file__).parents[1]
            / "spikes"
            / "rayforge-jcz-no-device-addon"
        ),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.source.resolve(), args.addon.resolve())
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
