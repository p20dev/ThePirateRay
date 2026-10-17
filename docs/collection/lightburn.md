# LightBurn collection checklist

Collect directly into a dated directory under
`ThePirateRay-PrivateStash/raw/lightburn/`. Do not use Google Drive as an
intermediate workspace.

## Before collection

- Confirm no marking job is active.
- Do not enable debug logging or generate Support Data.
- Record which lens is installed and whether LightBurn currently connects.

## Required evidence

| Directory | Evidence |
| --- | --- |
| `00-version/` | Screenshot of Help → About with exact version/build |
| `01-exports/` | Full `.lbzip` bundle and exported `.lbprefs` |
| `02-prefs/` | ZIP of `%LOCALAPPDATA%\LightBurn`, copied only after LightBurn is fully closed |
| `03-device-settings/` | Device list and every Device Settings tab for the JPT device |
| `04-projects/` | Two or three known-working `.lbrn2` files, including vector and MOPA/hatch examples when available |
| `05-hardware/` | Machine, source, controller, and active-lens labels; never open an energized enclosure |
| `06-context/` | Mounted lens, connection status, and normal startup/interlock notes |

## Export procedure

1. Use File → Bundles → Export Bundle and include every available component.
2. Use File → Preferences → Export Prefs.
3. Capture the UI screenshots and save existing example projects.
4. Exit LightBurn completely.
5. Copy `%LOCALAPPDATA%\LightBurn` into an archive without editing its contents.
6. Run the private manifest tool and review the staged files before committing.

LightBurn documents bundles as containing settings, device profiles, hotkeys,
presets, and libraries. Since LightBurn 2.0, device export is also represented
as a bundle: <https://docs.lightburnsoftware.com/latest/Guides/Migration/>.

LightBurn explicitly warns not to publish generated Support Data:
<https://docs.lightburnsoftware.com/latest/Reference/Hidden/GenerateSupportData/>.
