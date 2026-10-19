"""Fail-closed preflight for the pinned Rayforge Windows GUI checkpoint."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def inspect(rayforge: Path, python_env: Path) -> dict[str, object]:
    msys2_shell = Path("C:/msys64/msys2_shell.cmd")
    msys2_env = rayforge / ".msys2_env"
    gi_available = importlib.util.find_spec("gi") is not None
    app_entry = rayforge / "rayforge" / "__main__.py"
    addon_manifest = (
        Path(__file__).parents[1]
        / "spikes"
        / "rayforge-jcz-no-device-addon"
        / "rayforge-addon.yaml"
    )
    checks = {
        "pinned_source_present": (rayforge / ".git").is_dir(),
        "application_entry_present": app_entry.is_file(),
        "no_device_addon_present": addon_manifest.is_file(),
        "python_environment_present": python_env.is_file(),
        "pygobject_gi_available": gi_available,
        "msys2_ucrt64_shell_present": msys2_shell.is_file(),
        "rayforge_msys2_environment_present": msys2_env.is_file(),
    }
    ready = all(checks.values())
    return {
        "transport": None,
        "controller_backend_reachable": False,
        "checks": checks,
        "ready_for_manual_gui_test": ready,
        "status": "ready" if ready else "blocked",
        "missing_requirements": [key for key, passed in checks.items() if not passed],
        "observed_launch_error": None if gi_available else "ModuleNotFoundError: No module named 'gi'",
        "installation_performed": False,
        "next_action": (
            "launch isolated no-device GUI test"
            if ready
            else "provide a reviewed Rayforge Windows GTK runtime or approve its installation"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rayforge", type=Path)
    parser.add_argument("python", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = inspect(args.rayforge.resolve(), args.python.resolve())
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
