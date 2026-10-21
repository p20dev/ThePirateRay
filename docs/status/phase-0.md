# Phase 0 status

Last updated: 2026-10-21

## Completed

- Both repositories use `main` and have pushed, reviewable histories.
- PrivateStash uses Git LFS and preserves `raw/**` without line-ending or text
  normalization.
- The existing installer-stick source was read without modifying Google Drive.
- Private evidence snapshot `b6edf29` contains 307 files totaling 79,386,307
  bytes; 135 new LFS objects were uploaded in that import.
- Private manifest commit `50e589c` contains 307 SHA-256 entries, 307 matching
  Drive-file provenance entries, and 29 folder provenance entries.
- Public configuration analysis is linked to nine sanitized evidence entries.
- A private 340-token deny-list checks known Drive and machine identifiers
  without storing those identifiers publicly.
- A fresh clone of both remotes passed `git fsck`; the private clone additionally
  passed `git lfs fsck` and reproduced the expected file and byte counts.
- The public test suite and leak guard pass against the fresh private deny-list.
- Passive Windows enumeration of the connected controller confirmed device
  description `USBLMCV4`, USB VID/PID `9588:9899`, vendor-specific class, and
  USB revision descriptor `0005`. No compatible function driver is installed
  on the development computer; no endpoint was opened.
- Four LightBurn exports are preserved privately with SHA-256 manifests and
  Git LFS. Their public evidence records contain no private source locators.
- All three bundle manifests identify LightBurn `2.1.03`.
- The JPT export confirms a `JCZFiber`/`LibUSB` device profile, 110 x 110 mm
  work area, enabled Q-pulse-width control, `QPulseWidth` cut-list fields and
  a require-frame-before-start setting.
- The Eduard export confirms a Ruida/Serial profile with a 1500 x 1000 mm work
  area. A separate 500 x 300 mm Ruida profile remains physically unassigned.
- No vendor executable, plugin, DLL, or driver was run. No USB capture, framing,
  machine command, or laser output was performed.

## Pending external acquisition

These items remain pending from the actual control machine:

- closed-application preferences-folder archive;
- Device Settings screenshots;
- known-working `.lbrn2` examples;
- safe exterior hardware/label photographs and startup/interlock notes;
- stock-driver identity and version from the actual LightBurn control computer.

An About screenshot is useful corroboration, but the imported bundle manifests
already establish version `2.1.03`.

Collect them directly into a dated directory under PrivateStash by following
the [LightBurn checklist](../collection/lightburn.md). Do not use Google Drive
as an intermediate project workspace and do not generate Support Data.

Phase 0 remains open until the safety- and interoperability-relevant remainder
is hashed, committed, pushed, and represented by sanitized public evidence.

The work that does not depend on this acquisition can proceed in parallel.
The [product and research roadmap](../roadmap.md) defines the offline application
core, configuration analysis, protocol research, gated hardware experiments,
and workshop release as separate milestones.

## Offline M1 status

The Rayforge/MeerK40t reuse track has now produced public, transport-free
evidence for:

- deterministic MeerK40t BalorMK mock MOPA encoding, hatch planning and mock
  spooling;
- an external Rayforge no-device addon with profile import, fixed-size list
  buffering, safe state ordering, cancellation and explicit recovery;
- semantic and 12-byte-record agreement between a Rayforge `Ops` stream and
  the pinned BalorMK mock values;
- fail-closed profile and encoder negative cases;
- Rayforge workflow-model serialization and preview behavior for power,
  frequency and pulse width;
- independent layer visibility/output state and ordered serialization;
- material-recipe matching plus a fail-closed PirateRay provenance and exact
  machine/source/lens/correction compatibility gate;
- one consolidated no-device acceptance report that reruns the complete
  public test suite and leak guard, then hashes the regression evidence;
- a non-executing Windows artifact verifier that checks portable paths,
  archive safety, sizes, hashes, the pinned Rayforge revision and every
  packaged addon source while retaining the manual GUI gate;
- a versioned manual desktop-acceptance template and validator that cannot
  pass missing steps, connected hardware, changed evidence, stop conditions or
  an absent/malformed human review record;
- a deterministic acceptance-kit generator that copies only four allowlisted
  public template/input sources, hashes the three immutable inputs, refuses to
  overwrite an existing run directory, and binds the report to the exact kit,
  repository commit and artifact-verification report;
- pinned Rayforge and MeerK40t license/source contracts with drift tests, plus
  checkpoint schema 2 requiring the Rayforge MIT notice in the portable ZIP
  and beside the installer manifest;
- a single fail-closed Rayforge API-23 compatibility adapter around the
  internal driver registry, with collision, drift and symmetric-cleanup tests.
- a written M3 hardware-research protocol, intentionally incomplete public
  plan template and standard-library validator that requires exact
  evidence-backed request bytes, distinct safety roles, physical controls and
  recovery planning while always denying hardware authorization.
- a deterministic M3 review-packet generator that accepts only a
  `ready_for_review` plan, freezes its exact bytes and session window, records
  SHA-256 bindings, refuses overwrite and emits an untouched, non-authorizing
  human approval-record template.

The remaining M1 gates are deliberately explicit:

- a private known-working `.lbrn2` project is still required before mapping
  project-level `QPulseWidth` into workflow settings;
- packaged Windows/GTK interaction is blocked until a reviewed Rayforge
  runtime with PyGObject and MSYS2/UCRT64 is available; the repository build
  entry point fetches pinned source but never installs that runtime;
- graphical workflow, import, lens correction and controller protocol
  behavior remain unproven at the physical boundary;
- ADR 0002 remains **Proposed** until those gaps are resolved or rejected by
  evidence.

No item in this section authorizes USB access, controller commands or laser
output.

The M3 protocol can currently report only `incomplete`. It has no allowlisted
controller operation, reviewed driver/rollback plan, assigned people or
confirmed physical controls. Even a future `ready_for_review` result requires
separate human approval before hardware access.
