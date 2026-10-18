"""Compare a synthetic Rayforge Ops stream with the BalorMK golden trace."""

from __future__ import annotations

import argparse
import importlib.util
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


def _load_encoder(addon: Path):
    worker = addon / "pirate_ray_jcz" / "worker.py"
    spec = importlib.util.spec_from_file_location("tpr_jcz_worker", worker)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load JCZ spike encoder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OfflineJCZEncoder


def run(source: Path, addon: Path, balor_fixture: Path) -> dict[str, object]:
    commit = _commit_of(source)
    if commit != RAYFORGE_COMMIT:
        raise RuntimeError(f"expected Rayforge {RAYFORGE_COMMIT}, found {commit}")
    sys.path.insert(0, str(source))

    from raygeo.ops import Ops

    Encoder = _load_encoder(addon)
    to_mm = lambda word: word * Encoder.FIELD_MM / 65535.0

    ops = Ops()
    ops.job_start()
    ops.set_power(0.5)
    ops.set_feed_rate(250.0 * 60.0)
    ops.set_rapid_rate(2000.0 * 60.0)
    ops.set_frequency(40_000)
    ops.set_pulse_width(200)
    ops.move_to(to_mm(0x7000), to_mm(0x7000), 0.0)
    ops.line_to(to_mm(0x7100), to_mm(0x7000), 0.0)
    ops.line_to(to_mm(0x7100), to_mm(0x7100), 0.0)
    ops.line_to(to_mm(0x7000), to_mm(0x7100), 0.0)
    ops.line_to(to_mm(0x7000), to_mm(0x7000), 0.0)
    ops.dwell(1.0)
    ops.job_end()

    encoded = Encoder().encode(ops)
    semantic = encoded.driver_data["semantic_trace"]
    by_command: dict[str, list[dict]] = {}
    for item in semantic:
        by_command.setdefault(item["command"], []).append(item)

    balor = json.loads(balor_fixture.read_text(encoding="utf-8"))
    balor_trace = "\n".join(balor["trace"])
    checks = {
        "power_50_percent": (
            by_command["power"][0]["balor_word"] == 0x0800
            and "8012:0800" in balor_trace
        ),
        "speed_250_mm_s": (
            by_command["mark_speed"][0]["balor_word"] == 0x0094
            and "800c:0094" in balor_trace
        ),
        "frequency_40_khz": (
            by_command["frequency"][0]["balor_qswitch_period"] == 0x01F4
            and "801b:01f4" in balor_trace
        ),
        "pulse_width_200_ns": (
            by_command["pulse_width"][0]["nanoseconds"] == 200
            and "8026:00c8" in balor_trace
        ),
        "square_coordinates": (
            [(item["x"], item["y"]) for item in by_command["mark"]]
            == [
                (0x7100, 0x7000),
                (0x7100, 0x7100),
                (0x7000, 0x7100),
                (0x7000, 0x7000),
            ]
            and balor_trace.count("listMarkTo") == 4
        ),
        "dwell_1_ms": (
            by_command["laser_on_point"][0]["balor_10us_units"] == 100
            and "8003:0064" in balor_trace
        ),
    }
    if not all(checks.values()):
        raise AssertionError(f"semantic mismatch: {checks}")

    return {
        "rayforge_commit": commit,
        "balormk_commit": balor["commit"],
        "transport": None,
        "synthetic_field_mm": Encoder.FIELD_MM,
        "rayforge_ops_count": ops.len(),
        "semantic_trace": semantic,
        "command_records_hex": encoded.driver_data["command_records_hex"],
        "balormk_equivalence": checks,
        "limitations": [
            "12-byte command records only; no list buffering or transport",
            "record ordering follows the Rayforge Ops stream",
            "synthetic field mapping; no lens correction",
            "pulse width treated as nanoseconds from LaserStep UI contract",
        ],
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
        "--balor-fixture",
        type=Path,
        default=root / "tests" / "fixtures" / "meerk40t-mock-mopa-trace.json",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(
        args.source.resolve(),
        args.addon.resolve(),
        args.balor_fixture.resolve(),
    )
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
