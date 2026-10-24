# Upstream contract and license audit

- Date: 2026-10-21
- Scope: pinned Rayforge and MeerK40t revisions
- Hardware access: none
- Legal status: engineering record, not legal advice

## Result

Both pinned checkouts declare MIT licensing and pass the machine-readable
contract check. Their exact repositories, commits, normalized license hashes,
source-file hashes and required symbols are recorded in
`upstreams/rayforge.json` and `upstreams/meerk40t.json`.

Run the check against separately obtained source trees:

```powershell
python scripts/check_upstream_contracts.py `
  --rayforge <rayforge-checkout> `
  --meerk40t <meerk40t-checkout> `
  --output .build/artifacts/upstream-contracts.json
```

The current pinned trees pass. The command reads source and Git metadata only;
it imports neither project and cannot discover or open hardware.

## License observations

| Project | Pin | Declared license | Notice observation |
| --- | --- | --- | --- |
| Rayforge | `c28918c87f8273dd1d244f5a057addc192807fa5` | MIT | `pyproject.toml` names Samuel Abels as author; the pinned `LICENSE` text contains the MIT grant and warranty disclaimer but no explicit copyright line |
| MeerK40t | `d511944e08788e88077727f682957759884ff5ca` | MIT | The pinned notice states `Copyright (c) 2021 meerk40t` |

Exact notice copies live under `third_party/licenses/`. They are notices, not
a license grant for The Pirate Ray's own code. No upstream source is vendored
by adding them.

MIT permits use, modification and redistribution, but requires the copyright
and permission notice to accompany copies or substantial portions. Therefore:

- every Rayforge-based ZIP and installer distribution set must include the
  pinned Rayforge notice;
- a distribution containing adapted or copied BalorMK/MeerK40t code must also
  include the MeerK40t notice;
- attribution must name the upstream project and exact revision without
  implying endorsement;
- The Pirate Ray still needs its own explicit license before original project
  code is offered under open-source terms.

Checkpoint schema 2 now requires a verified Rayforge license sidecar and the
same notice inside the portable ZIP. The installer must be distributed with
its manifest and sidecar; installer-only publication is not accepted.

## API stability assessment

| Seam | Classification | Assessment |
| --- | --- | --- |
| Rayforge addon API version 23, `hookimpl`, `on_unload` | Documented addon API | Suitable compatibility boundary at the pinned revision |
| `register_machines` hook | Documented but unusable for this driver today | The hook exists, but the supplied manager does not expose driver-class registration |
| `NoDeviceDriver`, `OpsEncoder`, `EncodedOutput`, `MachineCodeOpMap` | Imported host interfaces | Required by the addon; pin and contract-test them before upgrades |
| `register_driver`, `drivers`, `driver_by_classname` | Internal registry | Functional but unsuitable as a permanent public contract; `register_driver` is not exported in `__all__` and no symmetric unregister function exists |
| `Step.extra`, visibility serialization, MOPA setters | Imported host workflow interfaces | Used by the disabled-output import bridge; exact source files and symbols are pinned before host integration |
| Addon-manager registry cleanup | Host lifecycle implementation | Other registries support addon-owned cleanup, but the driver registry is not part of that mechanism |
| BalorMK `GalvoController` and `MockConnection` | Application-internal reference/test seam | Valid as a pinned behavioral oracle; not treated as a stable library API |

The immediate upstream contribution should be a narrow, addon-aware driver
registry contract with symmetric registration and cleanup. Until upstream
accepts such a contract, all internal registry access must remain isolated in
one compatibility adapter and guarded by the hashes/symbol tests. The current
addon now does this: its API-23 adapter rejects version drift, malformed
registries, duplicate entries and foreign class-name collisions, and its
load/disable/enable/reload lifecycle passes against the pinned checkout.

## Code-origin boundary

The current PirateRay addon is a no-device clean-room spike. It imports
Rayforge host interfaces and compares independently generated traces with the
pinned BalorMK mock behavior. It does not vendor Rayforge or MeerK40t source.

Before adapting any BalorMK implementation code:

1. accept a project license compatible with MIT;
2. record the exact source files and revisions used;
3. preserve the MeerK40t notice in source and distributions;
4. keep transport code separate from the independently tested encoder; and
5. review the resulting diff for copied comments, identifiers and substantial
   structure rather than assuming a rewrite has no attribution duty.

## Recommendation requiring owner decision

MIT is the simplest project-license candidate because both principal
upstreams use MIT and the intended addon is meant for upstream contribution.
This audit does not select it. Kaz must explicitly approve the project license
before a root `LICENSE` file is added or upstream implementation code is
adapted.
