<p align="center">
  <img src="assets/branding/the-pirate-ray-logo.png" alt="The Pirate Ray logo" width="320">
</p>

<h1 align="center">The Pirate Ray</h1>

The Pirate Ray is Makerspace Næstved's clean-room effort to build an
open-source, safe desktop workflow for its laser equipment. The first target
is the **JPT 100 W E2/M7 MOPA fiber laser** with a JCZ/EZCAD2-compatible
controller and the currently assumed 110 x 110 mm lens.

The destination is the useful core of a LightBurn-like workflow: import or
create geometry, assign operations and MOPA parameters, preview and validate
the job, and eventually run it through independently auditable machine
backends. The project is not trying to evade LightBurn licensing or copy its
proprietary code or assets.

## Where we are now

Phase 0 has established a reproducible evidence and research baseline:

- the original installer material is preserved privately with SHA-256
  manifests and Git LFS;
- sanitized analysis covers the EZCAD2 installation, 110/300 configurations,
  correction data, material libraries, and relevant configuration files;
- the physical controller has been passively identified by Windows as
  `USBLMCV4`, USB `9588:9899`, with device revision descriptor `0005`;
- LightBurn `2.1.03` exports now confirm the JPT `JCZFiber`/`LibUSB` profile,
  110 x 110 mm work area, Q-pulse-width support, and the exact serialized
  setting name `QPulseWidth`;
- the Eduard X1550 export confirms a Ruida/Serial profile and 1500 x 1000 mm
  work area;
- the development computer has no compatible controller driver installed;
- no USB endpoint has been opened and no controller command, galvo movement,
  framing, marking, or laser output has occurred;
- the public tests, provenance checks, leak guard, and clean-clone validation
  pass.

Phase 0 remains open while we collect known-working LightBurn projects, device
screenshots, the closed-application preferences folder, machine photos, and
operator notes directly from the actual control computer. The bundle and
exported preferences are already preserved and analyzed.

## The important discovery

We do not need to begin with a blank-sheet LightBurn clone:

- [MeerK40t](https://github.com/meerk40t/meerk40t) already includes BalorMK,
  an MIT-licensed JCZ/EZCAD2 galvo implementation with MOPA pulse width,
  frequency control, status/abort behavior, and a mock USB connection. Its
  source targets the same `9588:9899` USB identity observed on our controller.
- [Rayforge](https://github.com/barebaric/rayforge) already supplies most of
  the modern desktop product: editor, projects, geometry, LightBurn import,
  material recipes, simulation, pre-flight checks, packaging, and an addon
  architecture. Its job model already represents frequency and pulse width.

The leading route is therefore either to use and improve MeerK40t directly or
to build a Rayforge JCZ/Balor addon using the narrowest practical layer from
BalorMK. This remains a proposed decision until the offline proofs in
[ADR 0002](docs/adr/0002-reuse-rayforge-and-balormk.md) have passed.

## Next steps

The initial offline architecture spikes have passed. The next work remains
hardware-free:

1. collect known-working `.lbrn2` projects and the remaining screenshots,
   photos, preferences folder and operator notes;
2. extend the synthetic import tests with the now-observed `QPulseWidth`
   evidence, without assuming its `.lbrn2` representation;
3. define the minimum Rayforge JCZ device-profile/import extension and finish
   controller-list buffering and safe state ordering offline;
4. accept, revise, or reject the proposed reuse architecture from evidence;
5. write and review a separate hardware protocol before any live controller
   communication.

An independent desktop application is the fallback only if both existing
platforms fail concrete, documented requirements.

## Repository boundary

This public repository contains source code, plans, decisions, tests, tools,
and sanitized research. Raw machine data, serial numbers, LightBurn exports,
and third-party material with unclear redistribution rights live in the
separate private `ThePirateRay-PrivateStash` repository. Google Drive is not a
project workspace or development destination.

## Project map

- [Project charter](docs/project-charter.md)
- [Product and research roadmap](docs/roadmap.md)
- [Current Phase 0 status](docs/status/phase-0.md)
- [Open-source reuse landscape](docs/research/open-source-landscape.md)
- [Proposed Rayforge/BalorMK reuse decision](docs/adr/0002-reuse-rayforge-and-balormk.md)
- [Live USB enumeration](docs/research/live-usb-enumeration-2026-10-17.md)
- [LightBurn device-export analysis](docs/research/lightburn-device-exports-2026-10-19.md)
- [Sanitized machine profile](docs/research/machine-profile.yaml)
- [110/300 configuration comparison](docs/research/config-comparison.md)
- [Data handling policy](docs/data-handling.md)
- [LightBurn collection checklist](docs/collection/lightburn.md)
- [Repository boundary decision](docs/adr/0001-public-private-repository-boundary.md)

## Validation

The repository uses only Python's standard library for Phase 0 tooling:

```powershell
python -m unittest discover -s tests -v
python scripts/check_public_repo.py .
```

The checks verify manifest integrity, public/private evidence contracts,
disallowed binary types, private identifiers, local user paths, and other
likely data leaks. They do not certify hardware safety.

## Safety boundary

- Simulation precedes equivalent hardware behavior.
- Read-only precedes state change; state change precedes motion; motion
  precedes emission.
- Machine, source, lens, correction profile, units, and parameter ranges must
  match before a job can be armed.
- Unknown configuration or protocol fields are never guessed or replayed.
- Vendor executables, DLLs, and drivers from the evidence snapshot are never
  run as part of analysis.

No project license has been selected yet. Until that decision is recorded,
the contents are not offered under an open-source license.
