# Codex continuation brief

- Updated: 2026-10-24
- Current focus: produce and accept the packaged Windows M1 checkpoint
- Hardware access: prohibited
- Automatic toolchain installation: prohibited

## Verified checkpoint

The complete public unit-test suite and public-repository guard pass at this
checkpoint. The offline Rayforge/MeerK40t evidence covers addon lifecycle, MOPA
settings and units, layer and recipe semantics, JCZ record/list encoding,
negative cases, cancellation/recovery and synthetic LightBurn imports.

The repository now provides:

- an on-demand source/build entry point that never installs the Windows
  toolchain, rejects modified upstream source and replaces only the validated
  addon staging directory;
- a non-executing verifier for externally produced Windows artifacts;
  it requires an exact repository-to-manifest-to-ZIP addon file set and
  rejects unsafe, colliding, encrypted or linked archive entries;
- a checksummed acceptance-kit generator containing only allowlisted public
  synthetic inputs, with provenance binding to the repository commit and
  non-executing artifact-verification report, including the Rayforge pin and
  bundle, installer, addon-verification and source checkpoint-manifest fields;
- a fail-closed manual desktop-acceptance report and validator;
  complete operator evidence is only ready for review until a named,
  timezone-stamped human review is recorded;
- pinned upstream contract/license manifests and a drift checker;
- a fail-closed API-23 adapter isolating Rayforge's internal driver registry;
- a proposed MIT project-license decision in ADR 0003; Kaz has not accepted
  it, so the repository remains unlicensed;
- a fail-closed M3 hardware-research protocol, incomplete public plan template
  and validator; validation can reach only `ready_for_review` and never
  authorizes hardware access.
- a deterministic M3 review-packet generator that freezes only a
  `ready_for_review` plan and creates a hash-bound, explicitly unreviewed
  record without granting hardware access.
- a separate M3 approval-record validator that rejects changed packet files,
  reviewer/window drift, late review, incomplete safety statements and any
  claim of automatic hardware authorization.

Run the ordinary checkpoint with the bundled Codex Python or another supported
Python interpreter and a writable `TEMP`/`TMP`:

```powershell
python -m unittest discover -s tests -v
python scripts/check_public_repo.py .
```

## External gates

The closed-application local settings directory is now preserved and hashed in
PrivateStash; see `docs/research/lightburn-local-settings-2026-10-24.md`.
The operator confirmed a 110 mm installed lens. General local project candidates
remain excluded as unverified. The operator subsequently selected three specific
successful projects; their verified private copies establish project-level
`frequency` and `QPulseWidth` serialization. See
`docs/research/lightburn-verified-projects-2026-10-24.md`. One Scan setting and
two `CutSetting_Img` image settings omit `QPulseWidth`; its effective default
remains unresolved. Both image settings record `ditherMode="3dslice"`.

The running control-machine application was also inspected while the laser was
physically disconnected. LightBurn Pro 2.1.03 showed the JPT profile as
`Disconnected`, the 110 mm material library, and explicit `Frequency (kHz)` /
`Q-Pulse (ns)` UI labels. The live preferences, newest native backup, all five
general Settings tabs and all three JPT Device Settings tabs are hashed in
PrivateStash. Exterior hardware photographs and startup/interlock notes are
deferred to M3 hardware readiness and do not block the offline product
checkpoint; see
`docs/research/lightburn-control-machine-observation-2026-10-24.md`.

M1 is not yet a packaged desktop checkpoint. Only these two result-oriented
gates remain:

1. A Windows artifact for the pinned Rayforge revision must be produced on a
   reviewed build runner, verified without execution, and pass the manual
   no-device desktop checklist.
2. The known-working private JPT `.lbrn2` serialization and unit-contract gates
   are met for LightBurn 2.1.03 vector settings. Promotion still requires
   explicit resolution of absent pulse width, image equivalence and complete
   machine-context validation.

Raw projects, screenshots containing identifiers, machine data and build
binaries stay out of the public repository.

## Suggested first task

An offline project MOPA seam, disabled-output Rayforge workflow bridge and
synthetic tests now exist; see
`docs/research/lightburn-project-mopa-import.md`. It preserves both process
element types and applies the evidence-bound Hz/ns contract only to LightBurn
2.1.03. The bridge binds source layer IDs, uses the host MOPA setters,
serializes exact unit provenance and disables every staged step. Document
preflight presents the remaining blockers and the offline driver rejects them
before buffer preparation. The packaged frontend now exposes that report as a
read-only Tools-menu dialog with stable blocker codes. It never authorizes
encoding. Packaged interaction evidence, absent pulse width and image
equivalence remain blockers.

If a Windows artifact is available, keep the machine disconnected and run, in
order:

1. `scripts/verify_rayforge_windows_checkpoint.py`;
2. `scripts/prepare_m1_acceptance_kit.py`;
3. the manual checklist in
   `docs/research/m1-no-device-acceptance.md`;
4. `scripts/validate_m1_manual_acceptance.py`.

If no artifact is available, send the external-builder handoff in
`docs/research/m1-no-device-acceptance.md`; do not start another research
branch or install a build environment here. The evidence-backed vector MOPA
import mapping and synthetic tests are complete; Kaz's explicit decision on
ADR 0003 is also outstanding.
The M3 protocol can also be reviewed offline, but its
operation allowlist must stay empty until exact read-only request evidence is
available. ADR 0002 is accepted for the offline architecture. Until the
external gates and separate hardware approval arrive, no controller backend,
USB endpoint access, physical framing, galvo motion or laser output is
authorized.
