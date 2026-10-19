"""Transport-free JCZ job lifecycle used by the offline driver spike."""

from __future__ import annotations

from enum import Enum
from typing import Any


class OfflineSessionState(str, Enum):
    IDLE = "idle"
    PREPARED = "prepared"
    RUNNING = "running"
    HOLD = "hold"
    CANCELLED = "cancelled"
    COMPLETE = "complete"


class OfflineSessionError(RuntimeError):
    """Raised when an invalid lifecycle transition is requested."""


class OfflineJCZSession:
    """Keep encoded buffers in memory and require explicit recovery."""

    def __init__(self) -> None:
        self.state = OfflineSessionState.IDLE
        self._buffers: list[bytes] = []
        self.events: list[str] = []

    @property
    def buffered_bytes(self) -> int:
        return sum(len(packet) for packet in self._buffers)

    def prepare(self, encoded: Any) -> None:
        if self.state not in (
            OfflineSessionState.IDLE,
            OfflineSessionState.COMPLETE,
        ):
            raise OfflineSessionError(
                f"cannot prepare from state {self.state.value}"
            )
        data = encoded.driver_data
        if data.get("transport") is not None:
            raise OfflineSessionError("offline session rejects transport")
        buffers = data.get("list_buffers")
        if not buffers or any(len(packet) != 0xC00 for packet in buffers):
            raise OfflineSessionError("valid 0xC00 list buffers are required")
        self._buffers = list(buffers)
        self.state = OfflineSessionState.PREPARED
        self.events.append("prepared")

    def start(self) -> None:
        if self.state is not OfflineSessionState.PREPARED:
            raise OfflineSessionError(
                f"cannot start from state {self.state.value}"
            )
        self.state = OfflineSessionState.RUNNING
        self.events.append("started-offline")

    def hold(self) -> None:
        if self.state is not OfflineSessionState.RUNNING:
            raise OfflineSessionError(
                f"cannot hold from state {self.state.value}"
            )
        self.state = OfflineSessionState.HOLD
        self.events.append("held-offline")

    def resume(self) -> None:
        if self.state is not OfflineSessionState.HOLD:
            raise OfflineSessionError(
                f"cannot resume from state {self.state.value}"
            )
        self.state = OfflineSessionState.RUNNING
        self.events.append("resumed-offline")

    def cancel(self) -> None:
        if self.state not in (
            OfflineSessionState.PREPARED,
            OfflineSessionState.RUNNING,
            OfflineSessionState.HOLD,
        ):
            raise OfflineSessionError(
                f"cannot cancel from state {self.state.value}"
            )
        self._buffers.clear()
        self.state = OfflineSessionState.CANCELLED
        self.events.extend(
            (
                "cancel-requested-offline",
                "pending-buffers-cleared",
                "recovery-required",
            )
        )

    def recover(self) -> None:
        if self.state is not OfflineSessionState.CANCELLED:
            raise OfflineSessionError(
                f"cannot recover from state {self.state.value}"
            )
        if self._buffers:
            raise OfflineSessionError("recovery requires empty buffers")
        self.state = OfflineSessionState.IDLE
        self.events.append("recovered-to-idle")

    def complete(self) -> None:
        if self.state is not OfflineSessionState.RUNNING:
            raise OfflineSessionError(
                f"cannot complete from state {self.state.value}"
            )
        self._buffers.clear()
        self.state = OfflineSessionState.COMPLETE
        self.events.extend(("completed-offline", "pending-buffers-cleared"))
