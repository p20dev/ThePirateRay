"""Exercise Rayforge-style async cancellation on the offline JCZ driver."""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock


RAYFORGE_COMMIT = "c28918c87f8273dd1d244f5a057addc192807fa5"


def _commit_of(source: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _ops(Ops, line_count: int):
    ops = Ops()
    ops.job_start()
    ops.set_power(0.5)
    ops.set_feed_rate(15_000)
    ops.set_rapid_rate(120_000)
    ops.set_frequency(40_000)
    ops.set_pulse_width(200)
    ops.move_to(50, 50, 0)
    for index in range(line_count):
        ops.line_to(51 + index % 2, 50 + index % 2, 0)
    ops.job_end()
    return ops


async def _exercise(Driver, Ops) -> dict[str, object]:
    machine = MagicMock()
    machine.coordinate_systems = {}
    driver = Driver(MagicMock(), machine)
    encoder = driver.create_encoder(machine)

    long_ops = _ops(Ops, 260)
    encoded = encoder.encode(long_ops)
    buffered_before_cancel = sum(
        len(packet) for packet in encoded.driver_data["list_buffers"]
    )
    run_task = asyncio.create_task(driver.run(encoded, None, long_ops))
    await asyncio.sleep(0)
    await driver.set_hold(True)
    held_state = driver.offline_session.state.value
    await driver.set_hold(False)
    resumed_state = driver.offline_session.state.value
    await driver.cancel()
    await asyncio.wait_for(run_task, timeout=2)

    cancelled_state = driver.offline_session.state.value
    buffered_after_cancel = driver.offline_session.buffered_bytes
    restart_rejected = False
    try:
        driver.offline_session.start()
    except RuntimeError:
        restart_rejected = True

    driver.offline_session.recover()
    recovered_state = driver.offline_session.state.value

    recovery_ops = _ops(Ops, 2)
    recovery_encoded = encoder.encode(recovery_ops)
    await asyncio.wait_for(
        driver.run(recovery_encoded, None, recovery_ops), timeout=2
    )

    return {
        "transport": None,
        "long_job_buffer_count": len(encoded.driver_data["list_buffers"]),
        "buffered_bytes_before_cancel": buffered_before_cancel,
        "held_state": held_state,
        "resumed_state": resumed_state,
        "cancelled_state": cancelled_state,
        "buffered_bytes_after_cancel": buffered_after_cancel,
        "restart_without_recovery_rejected": restart_rejected,
        "recovered_state": recovered_state,
        "second_job_state": driver.offline_session.state.value,
        "events": driver.offline_session.events,
        "hardware_commands": [],
    }


def run(source: Path, addon: Path) -> dict[str, object]:
    commit = _commit_of(source)
    if commit != RAYFORGE_COMMIT:
        raise RuntimeError(f"expected Rayforge {RAYFORGE_COMMIT}, found {commit}")
    sys.path.insert(0, str(source))
    sys.path.insert(0, str(addon))

    from pirate_ray_jcz.worker import PirateRayJCZNoDeviceDriver
    from raygeo.ops import Ops

    result = asyncio.run(_exercise(PirateRayJCZNoDeviceDriver, Ops))
    result["rayforge_commit"] = commit
    return result


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
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
