# EZCAD2 110 mm / 300 mm configuration comparison

- Date: 2026-10-17
- Method: offline byte comparison and parsing of text configuration only
- Private evidence snapshot: commit `50e589c`

No executable, DLL, plugin, driver, or machine command was run.

## Result

Each lens tree contains 101 files. Ninety-five files are byte-identical and six
differ: `AUTOSAVE.ezd`, `cfglog.txt`, `Custom.ini`, `EZCAD.CFG`, `Usb.log`, and
`plug/markcfg7`. There are no files missing from either tree.

| Artifact | 110 mm | 300 mm | Observation |
| --- | ---: | ---: | --- |
| `markcfg7` | 10,423 bytes; `sha256-4bc09e50d3d0de8652df` | 10,425 bytes; `sha256-f5a88d31a882a56bcfd9` | Opaque binary profiles; only 49 leading bytes and 4,522 trailing bytes are shared. Treat each as an indivisible lens-specific profile. |
| `CoeFile.cfg` | 68,608 bytes; `sha256-05d2e8982a2dc64d6778` | Same content and hash | This correction file is shared by both supplied profiles. |
| `EZCAD.CFG` | `sha256-93bdf1d8da34312e57f4` | `sha256-eaf64932c2bee2cbc470` | Workspace is centered at ±55 mm versus ±150 mm. The remaining semantic differences are lens-tree plugin paths, which are redacted here. |
| `Usb.log` | 7,728 bytes; `sha256-e01aff572dcd39b51e6d` | 7,774 bytes; `sha256-b57cf786d2bbe29841b0` | The 110 mm file is an exact prefix of the 300 mm file; the extra 46 bytes look like appended log state, not a lens parameter. |

The differences in autosave, configuration log, and custom-state files are
likely session history rather than authoritative hardware configuration. This
is an inference from their role and filenames, not yet a decoded format claim.

## Controller metadata

The supplied Windows driver metadata identifies the controller family as a JCZ
USB laser-marking controller using the `Lmcv2u` driver family. It declares USB
VID `9588` and PID `9899`. This is installer evidence only and remains pending
verification against the connected machine in Windows Device Manager.

Evidence: `sha256-ebfe631958b9522533ff` and
`sha256-17ac4330cec7bc49b672`.

## Safety consequence

Do not synthesize a new profile by editing offsets inside `markcfg7`, and do not
assume the shared correction file makes the two profiles interchangeable. The
first implementation must parse and report before it can write or transmit any
configuration.
