<p align="center">
  <img src="assets/branding/the-pirate-ray-logo.png" alt="The Pirate Ray logo" width="320">
</p>

<h1 align="center">The Pirate Ray</h1>

The Pirate Ray is Makerspace Næstved's clean-room effort to build an
open-source, safe desktop workflow for its laser equipment. The first target
is the **JPT 100 W E2/M7 MOPA fiber laser** with a JCZ/EZCAD2-compatible
controller and the operator-confirmed 110 x 110 mm lens.

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

Phase 0 is complete as an evidence baseline. The settings and device screenshots, bundle,
exported preferences, closed-application local settings and three explicitly
operator-verified projects are preserved and analyzed. The operator confirmed a
110 mm lens; other local test projects remain unverified. See the
[local settings acquisition](docs/research/lightburn-local-settings-2026-10-24.md)
and [control-machine observation](docs/research/lightburn-control-machine-observation-2026-10-24.md).

Three operator-verified projects now establish project-level `frequency` and
`QPulseWidth` serialization. Correlation with the running LightBurn 2.1.03 UI
establishes raw Hz to displayed kHz and direct ns pulse width; see the
[verified-project analysis](docs/research/lightburn-verified-projects-2026-10-24.md).
Missing pulse width still requires explicit resolution before executable import.

The offline M1 reuse proofs now pass as one consolidated acceptance checkpoint:
the Rayforge/MeerK40t path has deterministic mock encoding, fail-closed JCZ
profile and parameter gates, list buffering, cancellation/recovery, layer and
recipe semantics, and a transport-free workflow preview. A reviewed Windows GTK
runtime and the packaged no-device workflow test remain outstanding. See the
[Phase 0 status](docs/status/phase-0.md) and
[Rayforge GUI preflight](docs/research/rayforge-windows-gui-preflight.md).

The first M3 deliverable is also available as a deliberately non-executable
[hardware-research protocol](docs/research/m3-hardware-research-protocol.md).
Its public template and validator can establish only `ready_for_review`; they
never authorize USB access or controller commands.

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

The accepted route is a Rayforge JCZ addon with BalorMK retained as the pinned
behavioral oracle and reference boundary. Packaged interaction remains an M1
release gate, not an architecture-decision gate; see
[ADR 0002](docs/adr/0002-reuse-rayforge-and-balormk.md).

## Next steps

The initial offline architecture spikes have passed. The next work remains
hardware-free:

1. obtain or produce a reviewed Windows Rayforge build artifact without
   installing a toolchain through this repository;
2. run and record the packaged no-device desktop interaction checklist;
3. promote only evidence-backed vector MOPA imports through the existing
   fail-closed review boundary;
4. complete and independently review the M3 hardware-protocol template before
   seeking separate approval for any live controller communication.

An independent desktop application is the fallback only if both existing
platforms fail concrete, documented requirements.

## Repository boundary

This public repository contains source code, plans, decisions, tests, tools,
and sanitized research. Raw machine data, serial numbers, LightBurn exports,
and third-party material with unclear redistribution rights live in the
separate private `ThePirateRay-PrivateStash` repository. Google Drive is not a
project workspace or development destination.

## Project map

- [Current continuation brief](docs/CODEX_HANDOFF.md)
- [Project charter](docs/project-charter.md)
- [Product and research roadmap](docs/roadmap.md)
- [MOPA workbench UX requirements](docs/design/mopa-workbench-ux.md)
- [Current Phase 0 status](docs/status/phase-0.md)
- [Open-source reuse landscape](docs/research/open-source-landscape.md)
- [LightBurn-to-Rayforge UX capability map](docs/research/lightburn-rayforge-ux-capability-map.md)
- [Rayforge layer visibility and output spike](docs/research/rayforge-layer-model-spike.md)
- [Rayforge material-recipe model spike](docs/research/rayforge-recipe-model-spike.md)
- [M1 no-device build and acceptance checkpoint](docs/research/m1-no-device-acceptance.md)
- [Proposed Rayforge/BalorMK reuse decision](docs/adr/0002-reuse-rayforge-and-balormk.md)
- [Proposed project license and upstream boundary](docs/adr/0003-project-license-and-upstream-boundary.md)
- [Upstream contract and license audit](docs/research/upstream-contract-and-license-audit.md)
- [Live USB enumeration](docs/research/live-usb-enumeration-2026-10-17.md)
- [LightBurn device-export analysis](docs/research/lightburn-device-exports-2026-10-19.md)
- [LightBurn control-machine observation](docs/research/lightburn-control-machine-observation-2026-10-24.md)
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

Rayforge source and its Windows build stack are not vendored or downloaded by
these checks. The exact upstream revision is recorded in
`upstreams/rayforge.json`; run `scripts/prepare_rayforge_build.ps1` explicitly
to populate the ignored build cache. The repository does not install the
Windows toolchain; bundle creation requires an already reviewed runtime.

## Safety boundary

- Simulation precedes equivalent hardware behavior.
- Read-only precedes state change; state change precedes motion; motion
  precedes emission.
- Machine, source, lens, correction profile, units, and parameter ranges must
  match before a job can be armed.
- Unknown configuration or protocol fields are never guessed or replayed.
- Vendor executables, DLLs, and drivers from the evidence snapshot are never
  run as part of analysis.

The Pirate Ray's original code and documentation are available under the
[MIT License](LICENSE). Bundled or referenced third-party material retains its
own license and attribution requirements; see `third_party/licenses/` and
[ADR 0003](docs/adr/0003-project-license-and-upstream-boundary.md).
