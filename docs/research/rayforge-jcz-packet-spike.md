# Rayforge-to-JCZ 12-byte record spike

- Date: 2026-10-18
- Rayforge commit: `c28918c87f8273dd1d244f5a057addc192807fa5`
- MeerK40t commit: `d511944e08788e88077727f682957759884ff5ca`
- Scope: deterministic command-record packing with no transport

## Result

The external Rayforge addon now packs the synthetic operation stream into
little-endian JCZ command records of six unsigned 16-bit words (12 bytes).
The opcode and value fields agree with the pinned BalorMK mock trace for power,
mark and jump speed, frequency, MOPA pulse width, the square coordinates and
distances, one millisecond dwell, and end-of-list.

The encoder now places those records into the pinned BalorMK list shape:
exactly 256 records and 3072 bytes per buffer, with unused final-buffer slots
filled by `listEndOfList`. Before packing, it requires one complete state block
ahead of all motion and emits the evidence-backed order `listReadyMark`, pulse
width, jump speed, frequency, power and mark speed, followed by geometry and
end-of-list. State changes after motion and duplicate or missing state fields
fail closed.

Two independent runs produced identical output with SHA-256
`6217c9f8fee0e612872de6c20f5b033a4df885a173a442baa54629465fc5db5b`.
The checked records are in
`tests/fixtures/rayforge-jcz-equivalence.json` and are asserted byte-for-byte by
the standard-library test suite.

## Safety boundary

This is an independently written, transport-free encoder spike. It imports no
USB, serial or socket transport, performs no discovery, and cannot send the
records anywhere. A synthetic profile identity must match before encoding.
Coordinates outside the synthetic 110 mm field and invalid or unsupported
operations continue to fail closed.

## Remaining gaps

- Upload, status, cancellation and recovery are absent.
- Port-state commands are deliberately omitted because their machine-specific
  bit semantics can arm output and have not yet passed the hardware gate.
- The 110 mm coordinate mapping is synthetic and has no lens correction.
- Machine-specific bounds and the pulse-width unit contract still require
  authoritative evidence; they are not guessed here.
- No hardware compatibility or safe marking behavior is established.

## Decision impact

The result advances the Rayforge addon route beyond semantic JSON traces: the
same operation model can produce deterministic controller-shaped records at a
narrow encoder boundary. At this checkpoint, stock application workflow
coverage, complete list behavior and full Windows packaging were still open.
Later offline progress is summarized by the
[M1 no-device acceptance checkpoint](m1-no-device-acceptance.md); ADR 0002
remains proposed because its external gates are still open.
