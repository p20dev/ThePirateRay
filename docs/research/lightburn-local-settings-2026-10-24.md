# Local LightBurn settings acquisition

- Date: 2026-10-24
- Scope: offline acquisition of the closed application's local settings directory
- Hardware access: none; connection status was not tested

## Evidence and integrity

The complete settings directory was archived in PrivateStash. Its 255 files
include 250 preference backups, current and previous settings, two JSON files
and a material-test preset. Archive members were checked against source SHA-256
digests before and after copying; ZIP integrity and the final archive digest
were also checked. The source files were not modified.

The archive SHA-256 is
`d64320d13d8a543820ab1dd25e42791ac9a6faff89b7cb07aadbd707e9a3ca39`.
The current settings member SHA-256 is
`0b1f3496e9838788cd1e8469a2ddae279a7d0dc872767768f77fbeeaff4603e2`.
The public artifact contract is recorded in
[`public-lightburn-local-settings.jsonl`](../../evidence/public-lightburn-local-settings.jsonl).
Raw preferences, backup contents and exact local paths remain private.

## Observations

The current settings file contains JSON despite its INI extension. It has four
device records. Exactly one uses `LibUSB` with a 110 x 110 mm work area. That
profile enables `Laser_QPulseWidthEnabled` and `RequireFrameBeforeStart`.
The global cut list has 60 entries, including 35 with `frequency` and 25 with
`QPulseWidth`. These counts agree with the earlier export analysis; they do
not establish that every profile field is unchanged or that global recipes
belong to a particular machine.

The operator separately confirmed the installed lens as **110 mm**. This is
an operator statement, not an independent verification of the lens label,
calibration or correction profile. A stored connection type does not establish
that a controller is connected or works.

## Excluded project files and remaining gates

The operator stated that the locally discovered project candidates are
unverified test files and instructed us not to use them. Nine temporary copies
were removed from this acquisition before analysis or commit. Their originals
were unchanged; no project content was analyzed or retained as evidence.

This collection closes the missing closed-application settings snapshot. The
gate was subsequently closed by three separately supplied, operator-verified
projects plus the running LightBurn 2.1.03 UI. The excluded candidates remain
unverified and are still not evidence. The resulting vector import mapping
stays disabled and review-gated; it is not executable machine authorization.

The reviewed Windows artifact and manual no-device desktop acceptance also
remain outstanding. No controller, USB endpoint, framing, motion or laser
operation was performed or authorized by this collection.
