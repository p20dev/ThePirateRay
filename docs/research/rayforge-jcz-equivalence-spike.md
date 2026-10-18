# Rayforge-to-JCZ semantic equivalence spike

- Date: 2026-10-18
- Rayforge commit: `c28918c87f8273dd1d244f5a057addc192807fa5`
- MeerK40t commit: `d511944e08788e88077727f682957759884ff5ca`
- Scope: deterministic semantic encoding with no transport

## Result

A real Rayforge `raygeo.ops.Ops` stream was constructed with job boundaries,
50 percent power, 250 mm/s feed, 40 kHz frequency, 200 ns pulse width, a
synthetic square, a one millisecond dwell and job end. The external addon
encoded it into a deterministic semantic trace without discovery or transport.

The encoded values matched the pinned BalorMK mock golden trace for all six
checked semantics:

| Concept | Rayforge input | JCZ/Balor semantic value |
| --- | ---: | ---: |
| Power | `0.5` fraction | `0x0800` |
| Mark speed | `15000` mm/min | `0x0094` for synthetic 110 mm field |
| Frequency | `40000` Hz | Q-switch period `0x01f4` |
| Pulse width | `200` ns | `0x00c8` |
| Geometry | four marks | matching `0x7000`/`0x7100` coordinates |
| Dwell | `1` ms | `0x0064` ten-microsecond units |

Two runs produced identical results with SHA-256
`6507c887b624a28820a79cf92a49b12b518a47aca7612a17af1f4ba5302b1e8d`.
The checked result is `tests/fixtures/rayforge-jcz-equivalence.json`.

## Unit finding

Rayforge's laser-step UI contract labels pulse width as nanoseconds, matching
BalorMK's MOPA UI. However, the current Ruida RPA encoder docstring calls the
same `Ops.pulse_width` value microseconds. The spike follows the laser-step
contract and records this disagreement as an upstream unit-clarity gap. A
production adapter must not infer the unit from a driver-specific comment.

## What this proves

- Rayforge `Ops` carries the required frequency and pulse-width state into an
  external binary encoder.
- The selected values can map deterministically to the same controller-level
  semantics emitted by the pinned BalorMK mock implementation.
- Coordinate, speed and dwell conversions can remain inside a small encoder
  boundary with no USB dependency.

## What this does not prove

- The semantic trace is now accompanied by separately documented 12-byte
  command records; neither artifact is a complete production command list.
- The 110 mm field is synthetic and applies no lens correction.
- No machine/source/lens profile validation is implemented.
- Unsupported Ops, cancellation, status, list buffering and error recovery
  still need explicit behavior and negative tests.
- No USB enumeration, controller command, motion or emission was attempted.

## Decision impact

Spike C passes at the semantic boundary. The result supports a Rayforge JCZ
addon architecture. A follow-up spike now covers transport-free 12-byte
command records, but ADR 0002 remains proposed until complete list behavior,
addon packaging in a complete Windows build, and the remaining stock
MeerK40t workflow assessment are addressed.
