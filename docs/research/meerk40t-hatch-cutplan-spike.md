# MeerK40t hatch cut-plan and mock-spooler spike

- Date: 2026-10-18
- MeerK40t commit: `d511944e08788e88077727f682957759884ff5ca`
- Scope: synthetic hatch through stock planning and mock spooling

## Result

A synthetic 2 mm square was assigned MeerK40t's default hatch effect and run
through the stock `copy`, `preprocess`, `validate`, `blob`, `preopt` and
`optimize` stages. The resulting plan contained one hatch mark line for this
small fixture and preserved 50 percent power, 250 mm/s speed, 40 kHz frequency
and 200 ns pulse width in the Balor command list.

The same plan was submitted to the stock spooler. It completed using
`MockConnection`, and mock packets were observed. A PyUSB trap was installed
before MeerK40t imports; any USB discovery or disposal attempt would fail the
run. Two runs produced identical golden output with SHA-256
`52c20ea7ef7221ff0321386e26e200dbec3b13d0223488b9d2e83236fd713f47`.

## What this proves

- Stock MeerK40t can turn a hatch effect into Balor mark geometry.
- MOPA frequency and pulse width survive the cut-plan and LaserJob boundary.
- The stock spooler can complete the synthetic job on forced mock transport.

## Remaining limits

- The fixture uses MeerK40t's default synthetic hatch configuration; it does
  not establish a production hatch recipe or machine-safe parameter range.
- It does not test the graphical workflow, project import, correction files,
  framing, cancellation, status or recovery.
- It establishes no compatibility with physical hardware.

No USB enumeration, controller command, galvo motion or laser emission was
attempted.
