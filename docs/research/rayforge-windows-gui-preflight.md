# Rayforge Windows GUI preflight

- Date: 2026-10-19
- Scope: isolated no-device launch prerequisite check
- Transport: none
- Installation performed: no

## Result

The pinned Rayforge source and the external no-device JCZ addon are present,
but the current test environment cannot launch Rayforge's GTK application.
The observed launch failure is:

```text
ModuleNotFoundError: No module named 'gi'
```

Rayforge's Windows development path expects an MSYS2 UCRT64 installation,
`PyGObject`, GTK4 and Libadwaita. Neither `C:\msys64\msys2_shell.cmd` nor the
checkout's generated `.msys2_env` is present. The lightweight Python venv used
for the transport-free encoder spikes therefore cannot substitute for the GUI
runtime.

The deterministic preflight result is stored in
`tests/fixtures/rayforge-windows-gui-preflight.json`. It deliberately reports
the manual GUI checkpoint as blocked rather than treating source/model tests
as a successful application launch.

## Safety and scope

The attempted instance used an isolated configuration directory and contained
only the external no-device addon. The addon has no discovery or transport
implementation. No USB endpoint or controller command was reached.

No dependency or runtime was installed. Installing Rayforge's full Windows
toolchain is a separate, reviewable action: upstream's setup includes MSYS2,
GTK, compiler/build packages and network downloads, so it should not be an
implicit side effect of a workflow test.

## On-demand source and build policy

The public repository records the upstream URL and exact commit in
`upstreams/rayforge.json`. `scripts/prepare_rayforge_build.ps1` fetches that
revision into the ignored `.build/upstreams/` cache only when explicitly
invoked. Its default action prepares source only; it neither installs the
Windows toolchain nor starts a build.

Windows dependencies and bundle creation require separate
`-InstallWindowsDependencies` and `-BuildWindowsBundle` switches. This keeps a
multi-gigabyte MSYS2/UCRT64 toolchain out of normal clone, test and documentation
workflows and makes a CI-produced bundle the preferred interaction-test input.

## Next action

Produce or obtain an artifact for the pinned revision through the explicit
on-demand build path, then rerun the preflight and perform the packaged
no-device interaction checklist from `rayforge-graphical-workflow-spike.md`.
Do not make the Windows build toolchain an implicit project dependency.
