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

Two independent runs produced identical output with SHA-256
`b3d34600daac7060c3d3b28edf1627813d3bc518b1a64be11367f8e2106a51c6`.
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

- Records are emitted in Rayforge operation order. A production adapter must
  define controller-safe state ordering from evidence.
- List framing, fixed-size buffers, padding, upload, status, cancellation and
  recovery are absent.
- The 110 mm coordinate mapping is synthetic and has no lens correction.
- Machine-specific bounds and the pulse-width unit contract still require
  authoritative evidence; they are not guessed here.
- No hardware compatibility or safe marking behavior is established.

## Decision impact

The result advances the Rayforge addon route beyond semantic JSON traces: the
same operation model can produce deterministic controller-shaped records at a
narrow encoder boundary. ADR 0002 remains proposed because stock application
workflow coverage, complete packet/list behavior, packaging in a full Windows
build and the remaining safety proof obligations are still open.
