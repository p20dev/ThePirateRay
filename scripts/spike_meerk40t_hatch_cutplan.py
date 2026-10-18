"""Run a synthetic MOPA hatch through MeerK40t planning without hardware."""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from spike_meerk40t_mock_mopa import PINNED_COMMIT, _install_usb_trap


def _commit_of(source: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def run(source: Path) -> dict[str, object]:
    commit = _commit_of(source)
    if commit != PINNED_COMMIT:
        raise RuntimeError(f"expected MeerK40t {PINNED_COMMIT}, found {commit}")
    _install_usb_trap()
    sys.path.insert(0, str(source))
    from test import bootstrap
    from meerk40t.balormk.mock_connection import MockConnection

    with tempfile.TemporaryDirectory() as temporary:
        job_path = Path(temporary) / "synthetic-hatch.lmc"
        kernel = bootstrap.bootstrap(profile="ThePirateRay_HATCH")
        try:
            kernel.console("service device start -i balor 0\n")
            device = kernel.device
            device.mock = True
            device.pulse_width_enabled = True
            device.default_pulse_width = 200
            kernel.console("rect 54mm 54mm 2mm 2mm\n")
            kernel.console("operation* delete\n")
            kernel.console("hatch\n")
            operation = list(kernel.elements.ops())[0]
            hatch_effect = operation.children[0]
            if hatch_effect.type != "effect hatch":
                raise AssertionError(
                    f"hatch command created unexpected node: {hatch_effect.type}"
                )
            element = list(kernel.elements.elems())[0]
            hatch_effect.add_reference(element)
            operation.speed = 250.0
            operation.power = 500
            operation.frequency = 40.0
            operation.pulse_width_enabled = True
            operation.pulse_width = 200
            kernel.console(
                f'plan clear copy preprocess validate blob preopt optimize save_job "{job_path}"\n'
            )
            saved = job_path.read_text(encoding="utf-8")

            controller = device.driver.connection
            controller.connect_if_needed()
            if not isinstance(controller.connection, MockConnection):
                raise AssertionError("spooler did not select MockConnection")
            packets: list[str] = []
            controller.connection.send = packets.append
            controller.connection.set_implied_response(
                struct.pack("<4H", 0, 0, 0, 0x20)
            )
            kernel.console("plan spool\n")
            deadline = time.monotonic() + 10.0
            while device.spooler.queue and time.monotonic() < deadline:
                time.sleep(0.02)
            if device.spooler.queue:
                raise TimeoutError("mock spooler did not become idle")
        finally:
            kernel()

    lines = saved.splitlines()
    mark_lines = [line for line in lines if line.startswith("listMarkTo")]
    required = ("listQSwitchPeriod", "listFiberYLPMPulseWidth", "listEndOfList")
    if any(not any(line.startswith(item) for line in lines) for item in required):
        raise AssertionError("planned hatch lost required MOPA/list commands")
    if not mark_lines:
        raise AssertionError(f"planned output contains no mark geometry: {lines}")
    return {
        "upstream": "meerk40t/meerk40t",
        "commit": commit,
        "transport": "MockConnection",
        "usb_access": "trapped; none attempted",
        "input": {
            "geometry": "synthetic 2 mm square with default hatch effect",
            "power_per_mille": 500,
            "speed_mm_per_s": 250.0,
            "frequency_khz": 40.0,
            "pulse_width_ns": 200,
        },
        "cutplan": {
            "command_count": len(lines),
            "mark_count": len(mark_lines),
            "contains_frequency": any("listQSwitchPeriod" in line for line in lines),
            "contains_pulse_width": any("listFiberYLPMPulseWidth" in line for line in lines),
        },
        "spooler": {
            "completed": True,
            "mock_packets_observed": bool(packets),
        },
        "trace": lines,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.source.resolve())
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
