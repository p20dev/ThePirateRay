"""Hardware-free Rayforge binary driver registration proof.

This is deliberately not a controller implementation.  It has no discovery
specification, transport, USB import, or machine I/O.
"""

import json
import math
import struct
from typing import Any

from rayforge.core.hooks import hookimpl
from rayforge.machine import driver as driver_registry
from rayforge.machine.driver import NoDeviceDriver
from rayforge.pipeline.encoder.base import (
    EncodedOutput,
    MachineCodeOpMap,
    OpsEncoder,
)


class OfflineJCZEncoder(OpsEncoder):
    """Encode Rayforge Ops to a deterministic, transport-free JCZ trace."""

    FIELD_MM = 110.0
    SYNTHETIC_PROFILE_ID = "synthetic-jpt-mopa-110-v1"

    OPCODES = {
        "jump": 0x8001,
        "end_of_list": 0x8002,
        "laser_on_point": 0x8003,
        "mark": 0x8005,
        "jump_speed": 0x8006,
        "frequency": 0x801B,
        "power": 0x8012,
        "mark_speed": 0x800C,
        "pulse_width": 0x8026,
    }

    def __init__(
        self,
        profile_id: str = SYNTHETIC_PROFILE_ID,
        expected_profile_id: str = SYNTHETIC_PROFILE_ID,
    ) -> None:
        self.profile_id = profile_id
        self.expected_profile_id = expected_profile_id

    def _validate_profile(self) -> None:
        if self.profile_id != self.expected_profile_id:
            raise ValueError(
                "profile mismatch: encoder refuses to produce a JCZ trace"
            )

    @staticmethod
    def _record(command: int, *values: int) -> bytes:
        words = (command, *values, 0, 0, 0, 0, 0)[:6]
        if any(not 0 <= value <= 0xFFFF for value in words):
            raise ValueError("JCZ command word is outside the unsigned 16-bit range")
        return struct.pack("<6H", *words)

    def _encode_records(self, trace: list[dict[str, Any]]) -> list[bytes]:
        records = []
        last_x = 0x8000
        last_y = 0x8000
        for item in trace:
            command = item["command"]
            if command == "job_start":
                continue
            if command == "job_end":
                records.append(self._record(self.OPCODES["end_of_list"]))
            elif command == "pulse_width":
                records.append(
                    self._record(
                        self.OPCODES[command], round(item["nanoseconds"])
                    )
                )
            elif command == "frequency":
                records.append(
                    self._record(
                        self.OPCODES[command], item["balor_qswitch_period"]
                    )
                )
            elif command in ("power", "mark_speed", "jump_speed"):
                records.append(
                    self._record(self.OPCODES[command], item["balor_word"])
                )
            elif command in ("jump", "mark"):
                x = item["x"]
                y = item["y"]
                distance = min(0xFFFF, int(math.hypot(x - last_x, y - last_y)))
                records.append(self._record(self.OPCODES[command], x, y, 0, distance))
                last_x, last_y = x, y
            elif command == "laser_on_point":
                records.append(
                    self._record(self.OPCODES[command], item["balor_10us_units"])
                )
            elif command == "offline_probe":
                continue
            else:
                raise ValueError(f"cannot packetize semantic command: {command}")
        return records

    @classmethod
    def _coordinate(cls, value_mm: float) -> int:
        if not 0.0 <= value_mm <= cls.FIELD_MM:
            raise ValueError("coordinate is outside the synthetic 110 mm field")
        return round(value_mm * 65535.0 / cls.FIELD_MM)

    def encode(self, ops: Any, *args, **kwargs) -> EncodedOutput:
        del args, kwargs
        self._validate_profile()
        if ops is None:
            trace = [{"command": "offline_probe"}]
            op_count = 0
        else:
            trace = []
            for command in ops.to_dict()["commands"]:
                kind = command["type"]
                if kind in ("JOB_START", "JOB_END"):
                    trace.append({"command": kind.lower()})
                elif kind == "SET_POWER":
                    fraction = float(command["power"])
                    if not 0.0 <= fraction <= 1.0:
                        raise ValueError("power must be between 0 and 1")
                    trace.append(
                        {
                            "command": "power",
                            "fraction": fraction,
                            "balor_word": round(fraction * 0xFFF),
                        }
                    )
                elif kind in ("SET_FEED_RATE", "SET_RAPID_RATE"):
                    speed_mm_s = float(command["speed"]) / 60.0
                    trace.append(
                        {
                            "command": (
                                "mark_speed"
                                if kind == "SET_FEED_RATE"
                                else "jump_speed"
                            ),
                            "mm_per_s": speed_mm_s,
                            "balor_word": int(
                                speed_mm_s * (65535.0 / self.FIELD_MM) / 1000.0
                            ),
                        }
                    )
                elif kind == "SET_FREQUENCY":
                    frequency_hz = float(command["frequency"])
                    if frequency_hz <= 0:
                        raise ValueError("frequency must be positive")
                    trace.append(
                        {
                            "command": "frequency",
                            "hz": frequency_hz,
                            "balor_qswitch_period": round(
                                20_000_000.0 / frequency_hz
                            ),
                        }
                    )
                elif kind == "SET_PULSE_WIDTH":
                    width_ns = float(command["pulse_width"])
                    if width_ns <= 0:
                        raise ValueError("pulse width must be positive")
                    trace.append(
                        {"command": "pulse_width", "nanoseconds": width_ns}
                    )
                elif kind in ("MOVE_TO", "LINE_TO"):
                    x, y, _z = command["end"]
                    trace.append(
                        {
                            "command": "jump" if kind == "MOVE_TO" else "mark",
                            "x": self._coordinate(float(x)),
                            "y": self._coordinate(float(y)),
                        }
                    )
                elif kind == "DWELL":
                    duration_ms = float(command["duration_ms"])
                    trace.append(
                        {
                            "command": "laser_on_point",
                            "duration_ms": duration_ms,
                            "balor_10us_units": round(duration_ms * 100.0),
                        }
                    )
                else:
                    raise ValueError(f"unsupported Ops command: {kind}")
            op_count = len(trace)

        records = self._encode_records(trace)
        payload = b"".join(records)
        if ops is None:
            payload = json.dumps(
                trace, sort_keys=True, separators=(",", ":")
            ).encode("ascii")
        return EncodedOutput(
            text=payload.hex(),
            op_map=MachineCodeOpMap.from_lists(
                [(index, 1) for index in range(op_count)],
                list(range(op_count)),
            ),
            driver_data={
                "binary": payload,
                "command_records_hex": [record.hex() for record in records],
                "semantic_trace": trace,
                "transport": None,
            },
        )


class PirateRayJCZNoDeviceDriver(NoDeviceDriver):
    label = "The Pirate Ray JCZ (offline)"
    subtitle = "No discovery or hardware transport"
    uses_gcode = False
    DISCOVERY = None

    @classmethod
    def create_encoder(cls, machine) -> OpsEncoder:
        del machine
        return OfflineJCZEncoder()


def _register() -> None:
    name = PirateRayJCZNoDeviceDriver.__name__
    if name not in driver_registry.driver_by_classname:
        driver_registry.register_driver(PirateRayJCZNoDeviceDriver)


def _unregister() -> None:
    name = PirateRayJCZNoDeviceDriver.__name__
    registered = driver_registry.driver_by_classname.get(name)
    if registered is PirateRayJCZNoDeviceDriver:
        del driver_registry.driver_by_classname[name]
    driver_registry.drivers[:] = [
        item for item in driver_registry.drivers if item is not registered
    ]


# Rayforge currently has no driver registry in call_registration_hooks().
# Registration therefore has to happen when the worker entry point is loaded.
_register()


@hookimpl
def on_unload() -> None:
    _unregister()
