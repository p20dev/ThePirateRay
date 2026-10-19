# Rayforge JCZ offline cancellation and recovery spike

- Date: 2026-10-19
- Rayforge commit: `c28918c87f8273dd1d244f5a057addc192807fa5`
- Scope: asynchronous no-device driver lifecycle; no transport

## Result

The external JCZ addon now exercises Rayforge's asynchronous `run`,
`set_hold` and `cancel` driver seam with an in-memory state machine. A
synthetic 260-line job produced two 3072-byte list buffers, entered running,
hold and resumed states, then cancelled. Cancellation cleared all 6144 buffered
bytes and moved to a terminal `cancelled` state.

Restart without an explicit recovery transition was rejected. After recovery
returned the session to idle, a separately encoded two-line job completed.
The complete event sequence is checked in
`tests/fixtures/rayforge-jcz-cancel-recovery.json`.

Two runs produced identical output with SHA-256
`943cb35432f58524c32fcf3bffb146ce1b57f6c6573870429158dd6e6550728a`.

## Evidence and safety boundary

The logical sequence follows the pinned BalorMK distinction between
pause/resume and abort/reset, but it does not encode or issue BalorMK's
`StopList`, `RestartList`, `StopExecute`, `ResetList`, port or source-control
commands. Those are hardware behaviors and remain outside this offline spike.

The mock records no hardware commands and has no discovery, USB, serial or
socket transport. Windows asyncio internally requires a local event-loop
wakeup socket pair, so this test may need to run outside the filesystem/network
sandbox; that implementation detail is not reachable from the addon and does
not contact a remote endpoint.

## Remaining gap

This proves the Rayforge cancellation contract and local buffer invalidation,
not physical controller cancellation or recovery. A future M3 protocol must
separately authorize and verify every real stop/reset/output-off command and
its order before a transport implementation exists.

No USB enumeration, controller command, motion, framing or emission occurred.
