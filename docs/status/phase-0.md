# Phase 0 status

Last updated: 2026-10-17

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
- No vendor executable, plugin, DLL, or driver was run. No USB capture, framing,
  machine command, or laser output was performed.

## Pending external acquisition

The current development computer is not the LightBurn control computer: no
LightBurn executable or local LightBurn preferences directory was present.
Consequently, these items remain pending from the actual control machine:

- Help → About screenshot;
- full `.lbzip` bundle and `.lbprefs` export;
- closed-application preferences-folder archive;
- Device Settings screenshots;
- known-working `.lbrn2` examples;
- safe exterior hardware/label photographs and startup/interlock notes;
- live Windows Device Manager confirmation of USB VID/PID and driver.

Collect them directly into a dated directory under PrivateStash by following
the [LightBurn checklist](../collection/lightburn.md). Do not use Google Drive
as an intermediate project workspace and do not generate Support Data.

Phase 0 remains open until these control-machine artifacts are hashed,
committed, pushed, and represented by sanitized public evidence.
