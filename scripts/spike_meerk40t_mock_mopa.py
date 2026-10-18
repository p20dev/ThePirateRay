"""Run a deterministic, hardware-free BalorMK MOPA command-list spike.

The script imports a separately checked-out MeerK40t tree.  It installs an
in-process USB trap before importing BalorMK, forces the controller's mock
transport, and never enumerates USB devices.
"""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
import types
from pathlib import Path


PINNED_COMMIT = "d511944e08788e88077727f682957759884ff5ca"


class _Channel:
    def __init__(self, name: str, log: list[str]):
        self.name = name
        self.log = log
        self._ = lambda value: value

    def __call__(self, value: str) -> None:
        self.log.append(f"{self.name}: {value}")

    def watch(self, _handler) -> None:
        return None


class _Service:
    safe_label = "offline-mopa-spike"
    source = "fiber"
    pulse_width_enabled = True
    default_pulse_width = 4
    default_rapid_speed = 2000.0
    default_power = 100.0
    default_frequency = 30.0
    default_fpk = 10.0
    default_speed = 100.0
    delay_laser_on = 100
    delay_laser_off = 100
    delay_polygon = 100
    signal_updates = False

    class _SyntheticView:
        """Deterministic 110 mm field used only for speed conversion."""

        @staticmethod
        def position(_x, _y, *, vector=False, margins=True):
            del vector, margins
            galvos_per_mm = 65535.0 / 110.0
            return galvos_per_mm, galvos_per_mm

    def __init__(self) -> None:
        self.log: list[str] = []
        self.channels: dict[str, _Channel] = {}
        self.view = self._SyntheticView()

    def channel(self, name: str, **_kwargs) -> _Channel:
        return self.channels.setdefault(name, _Channel(name, self.log))

    def signal(self, *_args) -> None:
        return None

    def setting(self, _kind, name: str, default):
        return getattr(self, name, default)


def _install_usb_trap() -> None:
    class USBError(Exception):
        backend_error_code = None

    class NoBackendError(USBError):
        pass

    def forbidden(*_args, **_kwargs):
        raise AssertionError("real USB access attempted during mock-only spike")

    usb = types.ModuleType("usb")
    core = types.ModuleType("usb.core")
    util = types.ModuleType("usb.util")
    backend = types.ModuleType("usb.backend")
    libusb1 = types.ModuleType("usb.backend.libusb1")
    core.USBError = USBError
    core.NoBackendError = NoBackendError
    core.find = forbidden
    util.dispose_resources = forbidden
    libusb1.LIBUSB_ERROR_ACCESS = -3
    libusb1.LIBUSB_ERROR_NOT_FOUND = -5
    usb.core = core
    usb.util = util
    sys.modules.update(
        {
            "usb": usb,
            "usb.core": core,
            "usb.util": util,
            "usb.backend": backend,
            "usb.backend.libusb1": libusb1,
        }
    )


def _commit_of(source: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def run(source: Path) -> dict[str, object]:
    commit = _commit_of(source)
    if commit != PINNED_COMMIT:
        raise RuntimeError(f"expected MeerK40t {PINNED_COMMIT}, found {commit}")

    _install_usb_trap()
    sys.path.insert(0, str(source))
    from meerk40t.balormk.controller import GalvoController
    from meerk40t.balormk.mock_connection import MockConnection

    service = _Service()
    controller = GalvoController(service, force_mock=True)
    controller.init_laser = lambda: None
    controller.connect_if_needed()
    if not isinstance(controller.connection, MockConnection):
        raise AssertionError("controller did not select MockConnection")

    parsed_packets: list[str] = []
    controller.connection.send = parsed_packets.append
    controller._list_new()
    controller.set_settings(
        {
            "power": 500,
            "speed": 250.0,
            "frequency": 40.0,
            "pulse_width_enabled": True,
            "pulse_width": 200,
        }
    )
    controller.goto(0x7000, 0x7000)
    controller.mark(0x7100, 0x7000)
    controller.mark(0x7100, 0x7100)
    controller.mark(0x7000, 0x7100)
    controller.mark(0x7000, 0x7000)
    controller.list_laser_on_point(100)  # 1 ms in BalorMK's 10 us units.
    controller.list_end_of_list()
    # Make the mock's status reply deterministic and ready. Without this,
    # upstream MockConnection returns random bytes when no response is implied.
    controller.connection.set_implied_response(struct.pack("<4H", 0, 0, 0, 0x20))
    controller._list_end()

    trace = "\n".join(parsed_packets)
    required = {
        "frequency_40_khz": "801b:01f4:0000:0000:0000:0000 listQSwitchPeriod",
        "pulse_width_200_ns": "8026:00c8:0000:0000:0000:0000 listFiberYLPMPulseWidth",
        "geometry": "listMarkTo",
        "dwell_1_ms": "8003:0064:0000:0000:0000:0000 listLaserOnPoint",
        "end": "listEndOfList",
    }
    for label, marker in required.items():
        if marker not in trace:
            raise AssertionError(f"missing {label}: {marker}\nactual trace:\n{trace}")

    return {
        "upstream": "meerk40t/meerk40t",
        "commit": commit,
        "transport": type(controller.connection).__name__,
        "usb_access": "trapped; none attempted",
        "input": {
            "power_per_mille": 500,
            "speed_mm_per_s": 250.0,
            "frequency_khz": 40.0,
            "pulse_width_ns": 200,
            "geometry": "closed synthetic square in controller coordinates",
        },
        "trace": trace.splitlines(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="pinned MeerK40t checkout")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.source.resolve())
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
