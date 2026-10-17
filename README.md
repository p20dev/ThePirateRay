# The Pirate Ray

The Pirate Ray is Makerspace Næstved's clean-room project for learning how to
interoperate with its laser equipment and, over time, building a safe desktop
control application.

Phase 0 focuses on the **JPT 100 W E2/M7 MOPA** fiber laser with a JCZ/EZCAD2
controller. It is deliberately limited to documentation and offline analysis:
no USB capture, framing, machine commands, or laser output.

## Repository boundary

This public repository contains source code, plans, decisions, tests, tools,
and sanitized research. Raw machine data, serial numbers, LightBurn exports,
and third-party material with unclear redistribution rights live in the
separate private `ThePirateRay-PrivateStash` repository.

Start with:

- [Project charter](docs/project-charter.md)
- [Product and research roadmap](docs/roadmap.md)
- [Data handling policy](docs/data-handling.md)
- [LightBurn collection checklist](docs/collection/lightburn.md)
- [Sanitized machine profile](docs/research/machine-profile.yaml)
- [110/300 configuration comparison](docs/research/config-comparison.md)
- [Repository boundary decision](docs/adr/0001-public-private-repository-boundary.md)
- [Current Phase 0 status](docs/status/phase-0.md)

## Validation

The repository uses only Python's standard library for Phase 0 tooling:

```powershell
python -m unittest discover -s tests -v
python scripts/check_public_repo.py .
```

`scripts/materialize_private_drive_files.ps1` is the bounded transport used by
the acquisition workflow. It accepts authenticated download references over
standard input, rejects path traversal, and verifies byte sizes before files
enter PrivateStash. It never prints download credentials.

For non-interactive orchestration it also accepts one UTF-8 JSON request as a
Base64 parameter. This prevents shell metacharacters in signed references from
being interpreted as commands.

No project license has been selected yet. Until that decision is recorded,
the contents are not offered under an open-source license.
