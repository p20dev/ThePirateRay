# Rayforge JCZ negative safety cases

- Date: 2026-10-18
- Rayforge commit: `c28918c87f8273dd1d244f5a057addc192807fa5`
- Scope: fail-closed encoder boundary, no discovery or transport

## Result

The transport-free JCZ semantic encoder rejected all eight synthetic negative
cases before producing output:

| Case | Rejection |
| --- | --- |
| Profile mismatch | Encoder profile identity did not match the required identity |
| Out-of-field geometry | Coordinate exceeded the synthetic 110 mm field |
| Power above one | Power was outside the Rayforge `0..1` fraction |
| Zero frequency | Frequency was not positive |
| Zero pulse width | Pulse width was not positive |
| Unsupported command | A synthetic `CUSTOM` Ops command had no explicit mapping |
| Missing required state | A job omitted pulse width, rapid speed, frequency and mark speed |
| State after motion | A frequency change appeared after the first move |

Two runs produced identical results with SHA-256
`1372037e089185365bb7600762d49afa938063ef53f888604f87c68cad829b83`.
The checked result is `tests/fixtures/rayforge-jcz-negative-cases.json`.

## Boundary

The profile identifier and 110 mm field are explicitly synthetic. This test
does not claim the actual machine, lens or correction identity. It proves only
that the encoder boundary can require exact identity and reject mismatches
without guessing values.

The current validations are intentionally narrower than a production policy.
Real minimum/maximum frequency and pulse-width limits require verified source
and machine evidence. Until then, the spike rejects non-positive values but
does not invent an upper limit.

No controller discovery, USB access, motion, framing or emission occurred.
