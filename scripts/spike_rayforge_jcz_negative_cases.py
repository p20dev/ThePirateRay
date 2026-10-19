"""Run fail-closed cases against the transport-free Rayforge JCZ encoder."""

from __future__ import annotations

import argparse
import importlib
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
    sys.path.insert(0, str(addon))
    module = importlib.import_module("pirate_ray_jcz.worker")
    return module.OfflineJCZEncoder


def run(source: Path, addon: Path) -> dict[str, object]:
    commit = _commit_of(source)
    if commit != RAYFORGE_COMMIT:
        raise RuntimeError(f"expected Rayforge {RAYFORGE_COMMIT}, found {commit}")
    sys.path.insert(0, str(source))
    from raygeo.ops import Ops

    Encoder = _load_encoder(addon)

    cases = []

    def expect_rejection(name, encoder, ops, expected_message):
        try:
            encoder.encode(ops)
        except ValueError as error:
            message = str(error)
            if expected_message not in message:
                raise AssertionError(
                    f"{name} rejected for unexpected reason: {message}"
                ) from error
            cases.append(
                {"case": name, "result": "rejected", "reason": message}
            )
            return
        raise AssertionError(f"{name} was not rejected")

    empty = Ops()
    expect_rejection(
        "profile_mismatch",
        Encoder(profile_id="synthetic-wrong-profile"),
        empty,
        "profile mismatch",
    )

    outside = Ops()
    outside.move_to(Encoder.FIELD_MM + 0.001, 0.0, 0.0)
    expect_rejection(
        "out_of_field_geometry", Encoder(), outside, "outside"
    )

    power = Ops()
    power.set_power(1.001)
    expect_rejection("power_above_one", Encoder(), power, "power")

    frequency = Ops()
    frequency.set_frequency(0)
    expect_rejection(
        "non_positive_frequency", Encoder(), frequency, "frequency"
    )

    pulse = Ops()
    pulse.set_pulse_width(0)
    expect_rejection(
        "non_positive_pulse_width", Encoder(), pulse, "pulse width"
    )

    unsupported = Ops()
    unsupported.custom("synthetic-unsupported-command")
    expect_rejection(
        "unsupported_ops_command", Encoder(), unsupported, "unsupported"
    )

    incomplete_state = Ops()
    incomplete_state.job_start()
    incomplete_state.set_power(0.5)
    incomplete_state.job_end()
    expect_rejection(
        "missing_required_state",
        Encoder(),
        incomplete_state,
        "missing required JCZ state",
    )

    late_state = Ops()
    late_state.job_start()
    late_state.set_power(0.5)
    late_state.set_feed_rate(15_000)
    late_state.set_rapid_rate(120_000)
    late_state.set_frequency(40_000)
    late_state.set_pulse_width(200)
    late_state.move_to(55, 55, 0)
    late_state.set_frequency(50_000)
    late_state.job_end()
    expect_rejection(
        "state_change_after_motion",
        Encoder(),
        late_state,
        "state change after motion",
    )

    return {
        "rayforge_commit": commit,
        "profile": Encoder.SYNTHETIC_PROFILE_ID,
        "transport": None,
        "cases": cases,
        "all_failed_closed": len(cases) == 8,
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
