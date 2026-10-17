# The Pirate Ray branding

The official project name is **The Pirate Ray**.

`the-pirate-ray-logo.png` is the original transparent project logo supplied by
the project owner for use by this project. It is stored without resizing,
re-encoding, or other modification.

- Dimensions: 1254 x 1254 pixels
- Format: 32-bit ARGB PNG
- SHA-256: `afcd7e457b5bf9cf92a7222b3ab8a2850d75c05bc2c37d242c959cd7569e6fa4`

Use the transparent original by default. If a derivative needs an opaque
background, the background must be black. Do not use another background
color.

## Generated derivatives

`generated/` contains reproducible derivatives for common application and
distribution targets. The canonical source above remains the only master
artwork.

- `png/transparent/`: full-bleed transparent PNGs from 16 to 1024 pixels
- `png/on-black/`: opaque black-background PNGs
- `png/safe-zone/`: transparent icons with padding for UI and app chrome
- `png/monochrome-{black,white}/`: single-color notification/tray variants
- `web/`: favicons, Apple touch icon, PWA icons, and maskable PWA icons
- `windows/`: multi-resolution ICO and Microsoft Store square assets
- `macos/`: ICNS and an Xcode-compatible `AppIcon.iconset`
- `ios/`: a ready-to-copy `AppIcon.appiconset` with `Contents.json`
- `android/`: legacy launcher and adaptive foreground assets by density
- `linux/`: freedesktop `hicolor` application icon hierarchy
- `social/`: square profile and 1200 x 630 Open Graph images

Use the safe-zone or maskable versions anywhere the operating system may crop
an icon to a circle, squircle, or other shape. Android adaptive foreground
assets are transparent and are intended for a black (`#000000`) adaptive-icon
background.

`generated/manifest.json` records every derivative's dimensions and SHA-256.
Regenerate the complete set from the repository root with:

```powershell
uv run --with pillow python scripts/generate_brand_assets.py
```

The repository does not yet have a project license. This directory records
the asset's provenance and approved presentation; it does not independently
grant broader rights or select a license.
