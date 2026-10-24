# M1 no-device build and acceptance checkpoint

- Date: 2026-10-20
- Rayforge commit: `c28918c87f8273dd1d244f5a057addc192807fa5`
- Scope: packaged Windows desktop and consolidated offline acceptance
- Hardware access: prohibited

## Goal

Close the remaining software-controlled part of M1 with one reproducible
checkpoint rather than treating isolated spikes as a finished desktop flow.
The checkpoint has two outputs:

1. a pinned Windows Rayforge bundle containing the external PirateRay
   no-device addon;
2. one machine-readable acceptance report covering all current transport-free
   evidence.

Neither output authorizes USB discovery, controller commands, galvo movement,
physical framing, arming or laser output.

## On-demand build

Run the build only when a Windows artifact is required:

```powershell
scripts/build_rayforge_windows_checkpoint.ps1
```

The script fetches the exact revision from `upstreams/rayforge.json`, stages
the no-device addon into the ignored build checkout, invokes Rayforge's
upstream MSYS2 build and creates a portable ZIP plus installer hashes under
`.build/artifacts/`. Normal clone, documentation and test workflows do not
download or install the build stack.

The checkpoint script never installs the Windows toolchain. If the reviewed
runtime is unavailable, it stops and reports the missing prerequisite. Any
toolchain preparation remains a separate, explicitly invoked upstream action
or should happen on a dedicated build runner.

### External builder handoff

The external builder needs only a clean checkout of this repository, Windows,
and a reviewed Rayforge-compatible MSYS2/UCRT64 runtime. No laser or controller
may be connected. Run `scripts/build_rayforge_windows_checkpoint.ps1` from the
repository root with a clean checkout and an absent or empty artifact path. A
successful run leaves one transferable directory,
`.build/artifacts/`, containing exactly the portable ZIP, installer, Rayforge
license sidecar and `rayforge-windows-checkpoint.json`. Transfer that directory
as a unit; the receiving side verifies it before executing either binary.

Before staging, the script rejects transport imports in the addon. The build
entry point also rejects tracked Rayforge modifications and any unexpected
untracked source. It removes and recreates only the validated addon staging
directory, preventing stale files from a previous run from entering the
bundle. The build manifest records the exact upstream commit and hashes every
addon source file, the portable archive and installer. It does not claim the
GUI has been tested.

Copy the ZIP, installer and JSON manifest together, then verify an externally
produced checkpoint without launching either binary:

```powershell
python scripts/verify_rayforge_windows_checkpoint.py `
  .build/artifacts/rayforge-windows-checkpoint.json `
  --output .build/artifacts/rayforge-windows-verification.json
```

The verifier requires checkpoint schema 2 and portable artifact names, checks
sizes and SHA-256 digests, rejects unsafe ZIP paths, confirms the pinned
Rayforge commit, requires the manifest and bundle to contain exactly the
versioned repository addon file set with matching digests, and requires the
pinned Rayforge license both inside the ZIP and as a sidecar. Missing, changed
or additional addon files fail verification. Archive entries also fail on
duplicate or case-colliding Windows paths, backslashes, drive-like paths,
encryption or symbolic links.
The schema-1 verification output records the exact checkpoint-manifest name
and SHA-256 plus the fixed checkpoint and addon identities, so later manual
acceptance can retain the complete artifact provenance chain.
It never executes the application or installer, and a passing result retains
the manual GUI interaction gate. The installer, manifest and license sidecar
form one distribution set.

## Automated acceptance

Run with the isolated Rayforge Python environment:

```powershell
python scripts/run_m1_no_device_acceptance.py <rayforge-checkout> `
  --output .build/artifacts/m1-no-device-acceptance.json
```

The runner executes the complete repository test suite and public-repository
guard, then collects and hashes the regression-verified golden reports for the
addon lifecycle, graphical workflow model, layer model, recipe model, JCZ
equivalence, negative cases, cancellation/recovery and both LightBurn import
spikes. It passes only when the repository checks pass, transport remains
absent, the controller backend remains unreachable, negative cases fail
closed, cancellation requires recovery and incomplete LightBurn import still
blocks encoding.

## Manual packaged-app checklist

Use only the isolated no-device profile and an empty work area. Do not connect
or configure a controller.

Prepare a fresh, checksummed kit containing only the public synthetic inputs
and a new report template. Bind the passing non-executing artifact-verification
report into the kit at creation time:

```powershell
python scripts/prepare_m1_acceptance_kit.py `
  --artifact-verification .build/artifacts/rayforge-windows-verification.json `
  --checkpoint-manifest .build/artifacts/rayforge-windows-checkpoint.json
```

The default output is `.build/acceptance-kit/`. The generator uses a fixed
public allowlist, records the repository commit and refuses to overwrite a
non-empty directory. It does not include the application bundle, private
LightBurn evidence or any machine data. Acceptance-kit schema 2 binds the
generated manual report to the kit manifest, repository commit and copied
artifact-verification report by SHA-256. Editing, replacing or referring to an
external provenance report therefore fails validation. The copied report must
also name the pinned Rayforge commit, contain valid bundle and installer
SHA-256 values, and confirm that the exact current addon file count was
verified. Its own schema, checkpoint identity and addon identity are fixed, and
its recorded checkpoint-manifest hash must match the copied schema-2 manifest.

1. Pass the non-executing artifact verifier above.
2. Launch the portable build with a fresh application-data directory.
3. Confirm the UI identifies the state as offline/no-device.
4. Open synthetic geometry and inspect the 110 × 110 mm synthetic field.
5. Name, color, select and reorder layers.
6. Verify canvas visibility and output participation are independent.
7. Edit power, speed, frequency and pulse width and confirm Hz/ns labels.
8. Apply the synthetic unverified recipe; confirm mismatched compatibility is
   blocked and no approved label appears.
9. Preview enabled geometry, ordering, hatch and out-of-field diagnostics.
10. Save and reopen; confirm geometry, order and supported settings survive.
11. Start simulation, hold, resume, cancel and explicitly recover.
12. Exit and preserve only the sanitized acceptance report and screenshots.

Any device discovery prompt, physical-device status, transport attempt or
unlabelled framing action is a stop condition and fails the checkpoint.

Record the run in the generated `manual-report.json` and place sanitized
evidence below the report directory. Then validate it without launching the
application:

```powershell
python scripts/validate_m1_manual_acceptance.py `
  .build/acceptance-kit/manual-report.json `
  --output .build/acceptance-kit/manual-validation.json
```

The validator verifies the kit manifest, repository commit, artifact report,
evidence hashes and relative paths. It reports `incomplete` for any unrun or
blocked scenario, `ready_for_review` when every operator step passes but the
review record is still empty, and `failed` for a failed step, connected
hardware, non-isolated app data, changed evidence, malformed review or any
stop condition. Final `passed` requires a non-empty reviewer name and an
ISO-8601 review timestamp with timezone. No status authorizes hardware access.

## Remaining release gates

- The known-working project gate and LightBurn 2.1.03 Hz/ns serialization
  contract are complete. Missing pulse width and image equivalence remain
  explicit blockers.
- Human interaction results from the packaged build must be recorded before
  M1 can be called a packaged desktop checkpoint.
- The three known-working private projects establish serialized MOPA fields.
  Promotion from disabled staging still requires an absent-pulse-width policy,
  image equivalence and exact machine-context validation already enforced by
  preflight.
- Physical controller behavior remains outside M1.
