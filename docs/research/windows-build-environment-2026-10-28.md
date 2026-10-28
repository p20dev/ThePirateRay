# Windows build environment, 2026-10-28

## Scope

The operator explicitly authorized installing the Windows build environment.
MSYS2 was installed at `C:\msys64` through the `MSYS2.MSYS2` winget package
(installer version 20260927). The MSYS2 base was updated, including restarting
the shell after the core runtime update. No controller interaction or packaged
desktop acceptance was performed as part of this setup.

The source was fetched with `scripts/prepare_rayforge_build.ps1` and verified
against Rayforge commit `c28918c87f8273dd1d244f5a057addc192807fa5`.
The pinned upstream `scripts/win/win_setup.sh` was reviewed and explicitly run
in a UCRT64 shell. Repository scripts still do not install a toolchain
implicitly.

## Installed runtime

- Python 3.14.9
- GTK 4.24.1 and Libadwaita 1.10.0
- GCC 16.2.0 and Rust 1.99.1
- PyInstaller 6.22.3 and NSIS 3.13
- Raygeo 1.66.0 and Raydriver 0.3.0, compiled locally
- Cairo 1.18.4-4, selected by the pinned upstream setup script

The setup installs the upstream system-package set and its Python dependencies.
Run shell-based setup and build commands with `MSYSTEM=UCRT64` and
`CHERE_INVOKING=1`; run them from the repository root to preserve the working
directory. Source and outputs remain in the ignored `.build` cache.

## Observations and validation

- The 152 repository unit tests and public-repository guard passed before
  installation using a writable temporary directory.
- The consolidated `run_m1_no_device_acceptance.py` report passed using the
  newly installed UCRT64 Python and the pinned Rayforge checkout.
- Direct imports succeeded for GTK4, Libadwaita, Raygeo, Raydriver, Vtracer,
  Zeroconf, OpenCV, NumPy, SciPy, PyMuPDF and PyVips. This is an import check,
  not a successful desktop interaction test.
- `pip check` exited with status 1, reporting that the Raygeo and Raydriver
  distributions are not supported on this platform. Both locally compiled
  modules imported successfully; the metadata/platform warning remains
  unresolved and must not be represented as a clean dependency check.
- VIPS warned that its HEIF and ImageMagick modules could not load. Coverage
  of these image formats has not been established.
- PyInstaller warned about missing `scipy.special._cdflib`; successful bundle
  creation alone does not establish coverage of that module.

The first package download hit a connection reset and succeeded on retry.
The first Python wheel-build batch ran out of disk space while building
Zeroconf. Temporary build cleanup allowed the automatic retry to complete.
The new installation's downloaded pacman package cache was subsequently
removed; installed packages were retained. Allow substantial temporary disk
headroom beyond the roughly 5 GiB system-package installed-size estimate.

## Produced checkpoint

`scripts/build_rayforge_windows_checkpoint.ps1` completed successfully using
the pinned source and staged no-device addon. Outputs under `.build/artifacts/`:

- `rayforge-vpirateray-c28918c87f82.zip`: 354,161,221 bytes,
  SHA-256 `8640244f54aebe5d043f33db2949842fa9cb5e14e74dd75ec91af4f6873f274c`
- `rayforge-vpirateray-c28918c87f82-installer.exe`: 258,711,163 bytes,
  SHA-256 `a74620b3869803c755a9ffc20c35772e57ea2fef62bcf323ac971ae4a2aa8d5a`
- `Rayforge-LICENSE.txt` and `rayforge-windows-checkpoint.json`

The non-executing checkpoint verifier passed, including the exact 12-file
addon set, ZIP path checks, license notices and artifact hashes. Its local
report is `rayforge-windows-verification.json`. Binaries and local reports
remain outside version control. No packaged application was launched.

## Next gate

Prepare the checksummed acceptance kit from the passing verification report
and checkpoint manifest, then complete the isolated no-device desktop checklist described
in `m1-no-device-acceptance.md`. Neither setup nor automated acceptance closes
the manual packaged-app gate or authorizes hardware access.
