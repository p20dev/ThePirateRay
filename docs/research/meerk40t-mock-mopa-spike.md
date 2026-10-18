# MeerK40t mock-controller MOPA spike

- Date: 2026-10-18
- Upstream: `meerk40t/meerk40t`
- Commit: `d511944e08788e88077727f682957759884ff5ca`
- Scope: offline command-list encoding only

## Result

The pinned BalorMK controller selected its `MockConnection` and encoded a
synthetic square with explicit power, speed, 40 kHz frequency and 200 ns MOPA
pulse width. Two consecutive runs produced identical parsed command traces.
The harness supplies a synthetic 110 mm field solely for BalorMK's conversion
from mm/s to galvo units; it is not evidence that the physical lens is 110 mm.

The trace contains:

- `listQSwitchPeriod` value `0x01f4` (500), matching BalorMK's internal
  fiber-source conversion `20000 / 40 kHz`;
- `listFiberYLPMPulseWidth` value `0x00c8` (200);
- jump and mark commands for the synthetic square; and
- a one millisecond `listLaserOnPoint` dwell represented as 100 ten-microsecond
  controller units; and
- an explicit end-of-list command.

The harness replaces PyUSB with a trap before BalorMK is imported. Any call to
USB discovery or resource disposal fails the run. The controller is also
constructed with `force_mock=True`. No USB enumeration or hardware access was
attempted.

## Reproduce

Check out the pinned MeerK40t commit outside this repository, then run:

```powershell
python scripts/spike_meerk40t_mock_mopa.py C:\path\to\meerk40t
```

The script refuses to run against any other commit. Its JSON output includes
the upstream revision, inputs, selected transport, USB status and parsed trace.
The checked result is stored as
`tests/fixtures/meerk40t-mock-mopa-trace.json` for later golden comparisons.

## What this proves

- BalorMK's mock path can be forced without controller discovery.
- Operation settings preserve frequency in kHz and pulse width as the integer
  value emitted by `listFiberYLPMPulseWidth` through command-list encoding.
- The tested square produces a deterministic mock trace.

## What this does not prove

- It does not validate the units or safe range expected by the makerspace's
  specific JPT E2/M7 source.
- It does not exercise MeerK40t's graphical UI, hatch planner, correction file,
  job spooler, framing, cancellation or status behavior.
- It does not establish compatibility with the physical controller, mounted
  lens or correction profile.
- It does not authorize USB access, galvo motion or laser output.

## Decision impact

This is positive evidence for the BalorMK command encoder and mock transport,
but it is not enough to select stock MeerK40t as the workshop application.
The next useful extension of Spike A is a full cut-plan/spooler test containing
synthetic hatch geometry. Spike B, the external Rayforge no-device driver
registration proof, can proceed independently.
