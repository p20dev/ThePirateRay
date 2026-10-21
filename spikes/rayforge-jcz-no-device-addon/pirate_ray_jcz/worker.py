"""Hardware-free Rayforge binary driver registration proof.

This is deliberately not a controller implementation.  It has no discovery
specification, transport, USB import, or machine I/O.
"""

import hashlib
import asyncio
import json
import math
import struct
from typing import Any

from rayforge.core.hooks import hookimpl
from rayforge.machine.driver import NoDeviceDriver
from rayforge.pipeline.encoder.base import (
    EncodedOutput,
    MachineCodeOpMap,
    OpsEncoder,
)

from .offline_session import (
    OfflineJCZSession,
    OfflineSessionState,
)
from .rayforge_compat import register_driver, unregister_driver


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
        "ready": 0x8051,
    }

    LIST_RECORD_SIZE = 12
    LIST_BUFFER_SIZE = 0xC00
    LIST_RECORD_CAPACITY = LIST_BUFFER_SIZE // LIST_RECORD_SIZE
    STATE_ORDER = (
        "pulse_width",
        "jump_speed",
        "frequency",
        "power",
        "mark_speed",
    )

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
            if command == "ready":
                records.append(self._record(self.OPCODES[command]))
            elif command == "job_end":
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

    def _controller_list_trace(
        self, trace: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if not trace or trace[0]["command"] != "job_start":
            raise ValueError("JCZ list must start with job_start")
        if trace[-1]["command"] != "job_end":
            raise ValueError("JCZ list must end with job_end")

        states: dict[str, dict[str, Any]] = {}
        body: list[dict[str, Any]] = []
        motion_seen = False
        for item in trace[1:-1]:
            command = item["command"]
            if command in self.STATE_ORDER:
                if motion_seen:
                    raise ValueError(
                        "JCZ state change after motion is not supported"
                    )
                if command in states:
                    raise ValueError(f"duplicate JCZ state command: {command}")
                states[command] = item
            else:
                motion_seen = True
                body.append(item)

        missing = [name for name in self.STATE_ORDER if name not in states]
        if missing:
            raise ValueError(f"missing required JCZ state: {', '.join(missing)}")
        return (
            [{"command": "ready"}]
            + [states[name] for name in self.STATE_ORDER]
            + body
            + [trace[-1]]
        )

    def _pack_list_buffers(self, records: list[bytes]) -> list[bytes]:
        if not records:
            return []
        end_record = self._record(self.OPCODES["end_of_list"])
        buffers = []
        for offset in range(0, len(records), self.LIST_RECORD_CAPACITY):
            chunk = records[offset : offset + self.LIST_RECORD_CAPACITY]
            if len(chunk) < self.LIST_RECORD_CAPACITY:
                chunk = chunk + [end_record] * (
                    self.LIST_RECORD_CAPACITY - len(chunk)
                )
            packet = b"".join(chunk)
            if len(packet) != self.LIST_BUFFER_SIZE:
                raise AssertionError("JCZ list buffer is not exactly 0xC00 bytes")
            buffers.append(packet)
        return buffers

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

        controller_trace = [] if ops is None else self._controller_list_trace(trace)
        records = self._encode_records(controller_trace)
        list_buffers = self._pack_list_buffers(records)
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
                "controller_list_trace": controller_trace,
                "list_buffers": list_buffers,
                "list_buffer_sha256": [
                    hashlib.sha256(packet).hexdigest()
                    for packet in list_buffers
                ],
                "list_record_capacity": self.LIST_RECORD_CAPACITY,
                "list_buffer_size": self.LIST_BUFFER_SIZE,
                "list_meaningful_record_count": len(records),
                "list_padding_record_count": (
                    len(list_buffers) * self.LIST_RECORD_CAPACITY - len(records)
                ),
                "transport": None,
            },
        )


class PirateRayJCZNoDeviceDriver(NoDeviceDriver):
    label = "The Pirate Ray JCZ (offline)"
    subtitle = "No discovery or hardware transport"
    uses_gcode = False
    DISCOVERY = None

    def __init__(self, context, machine) -> None:
        super().__init__(context, machine)
        self.offline_session = OfflineJCZSession()

    @classmethod
    def create_encoder(cls, machine) -> OpsEncoder:
        del machine
        return OfflineJCZEncoder()

    async def run(
        self, encoded, doc, ops, on_command_done=None
    ) -> None:
        del doc, ops
        self.offline_session.prepare(encoded)
        self.offline_session.start()
        op_count = encoded.op_map.op_count if encoded.op_map else 0
        for op_index in range(op_count):
            await asyncio.sleep(0)
            while self.offline_session.state is OfflineSessionState.HOLD:
                await asyncio.sleep(0)
            if self.offline_session.state is OfflineSessionState.CANCELLED:
                return
            if on_command_done is not None:
                result = on_command_done(op_index)
                if hasattr(result, "__await__"):
                    await result
        self.offline_session.complete()
        self.job_finished.send(self)

    async def set_hold(self, hold: bool = True) -> None:
        if hold:
            self.offline_session.hold()
        else:
            self.offline_session.resume()

    async def cancel(self, emergency: bool = False) -> None:
        del emergency
        self.offline_session.cancel()


def _register() -> None:
    register_driver(PirateRayJCZNoDeviceDriver)


def _unregister() -> None:
    unregister_driver(PirateRayJCZNoDeviceDriver)


# Rayforge currently has no driver registry in call_registration_hooks().
# Registration therefore has to happen when the worker entry point is loaded.
_register()


@hookimpl
def on_unload() -> None:
    _unregister()
