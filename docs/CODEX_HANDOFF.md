# Codex continuation brief

- Updated: 2026-10-21
- Current focus: M1 build, packaging and no-device acceptance
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
  it, so the repository remains unlicensed.
- a fail-closed M3 hardware-research protocol, incomplete public plan template
  and validator; validation can reach only `ready_for_review` and never
  authorizes hardware access.

Run the ordinary checkpoint with the bundled Codex Python or another supported
Python interpreter and a writable `TEMP`/`TMP`:

```powershell
python -m unittest discover -s tests -v
python scripts/check_public_repo.py .
```

## External gates

M1 is not complete. Do not describe the repository as a finished desktop
application until both gates below have real evidence:

1. A Windows artifact for the pinned Rayforge revision must be produced on a
   reviewed build runner, verified without execution, and pass the manual
   no-device desktop checklist.
2. A known-working private JPT `.lbrn2` project must establish how project-level
   frequency and `QPulseWidth` are serialized before those fields are mapped.

Raw projects, screenshots containing identifiers, machine data and build
binaries stay out of the public repository.

## Suggested first task

If a Windows artifact is available, keep the machine disconnected and run, in
order:

1. `scripts/verify_rayforge_windows_checkpoint.py`;
2. `scripts/prepare_m1_acceptance_kit.py`;
3. the manual checklist in
   `docs/research/m1-no-device-acceptance.md`;
4. `scripts/validate_m1_manual_acceptance.py`.

If no artifact is available, do not install a build environment here. The next
useful input is the private known-working `.lbrn2` collection or Kaz's explicit
decision on ADR 0003. The M3 protocol can also be reviewed offline, but its
operation allowlist must stay empty until exact read-only request evidence is
available. Until the external gates and separate hardware approval arrive,
ADR 0002 remains Proposed and no controller backend, USB endpoint access,
physical framing, galvo motion or laser output is authorized.
