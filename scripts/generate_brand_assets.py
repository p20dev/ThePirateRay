"""Generate platform-ready derivatives of the canonical The Pirate Ray logo.

The source artwork is never modified. Run from the repository root with:

    uv run --with pillow python scripts/generate_brand_assets.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "branding" / "the-pirate-ray-logo.png"
OUTPUT = ROOT / "assets" / "branding" / "generated"
BRANDING_README = ROOT / "assets" / "branding" / "README.md"
SOURCE_SHA256 = "afcd7e457b5bf9cf92a7222b3ab8a2850d75c05bc2c37d242c959cd7569e6fa4"
PNG_SIZES = (16, 20, 24, 32, 40, 48, 64, 72, 96, 128, 144, 152, 180, 192, 256, 384, 512, 1024)
APP_SIZES = (16, 32, 48, 64, 128, 256, 512, 1024)


CATALOG_GROUPS = (
    ("png/transparent/", "PNG — transparent, full-bleed"),
    ("png/on-black/", "PNG — opaque on black"),
    ("png/safe-zone/", "PNG — transparent safe-zone"),
    ("png/monochrome-white/", "PNG — monochrome white"),
    ("png/monochrome-black/", "PNG — monochrome black"),
    ("web/", "Web and PWA"),
    ("windows/", "Windows"),
    ("macos/", "macOS"),
    ("ios/", "iOS and iPadOS"),
    ("android/", "Android"),
    ("linux/", "Linux / freedesktop"),
    ("social/", "Social media"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG", optimize=True)


def fit(source: Image.Image, size: int, coverage: float = 1.0) -> Image.Image:
    content_size = max(1, round(size * coverage))
    content = source.resize((content_size, content_size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = ((size - content_size) // 2, (size - content_size) // 2)
    canvas.alpha_composite(content, offset)
    return canvas


def on_black(source: Image.Image, size: int, coverage: float) -> Image.Image:
    transparent = fit(source, size, coverage)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    canvas.alpha_composite(transparent)
    return canvas


def monochrome(source: Image.Image, size: int, color: tuple[int, int, int]) -> Image.Image:
    alpha = fit(source, size, 0.78).getchannel("A")
    image = Image.new("RGBA", (size, size), (*color, 0))
    image.putalpha(alpha)
    return image


def catalog_background(relative: str) -> str:
    if any(part in relative for part in ("on-black/", "maskable-", "social/", "store/")):
        return "Opaque black"
    if relative.startswith(("ios/", "macos/")) or relative == "windows/app.ico":
        return "Opaque black, padded"
    if "/ic_launcher.png" in relative or "/ic_launcher_round.png" in relative:
        return "Opaque black, padded"
    if "monochrome-white/" in relative:
        return "Transparent; white silhouette"
    if "monochrome-black/" in relative:
        return "Transparent; black silhouette"
    if "safe-zone/" in relative:
        return "Transparent, 11% margin"
    if "foreground" in relative:
        return "Transparent adaptive foreground"
    return "Transparent"


def catalog_usage(relative: str, width: int | None = None) -> str:
    name = Path(relative).name
    if relative.startswith("png/transparent/"):
        if width and width <= 48:
            return "Small UI, browser chrome, or tray use where full artwork may reach the edge."
        if width and width <= 192:
            return "General UI, documentation, avatars, and compact placements on any background."
        return "General high-resolution placement, print/layout source, and manual exports."
    if relative.startswith("png/on-black/"):
        return "Use where transparency is unsupported or a guaranteed black brand background is required."
    if relative.startswith("png/safe-zone/"):
        return "App chrome, launchers, or UI containers that may crop or round the image."
    if "monochrome-white/" in relative:
        return "Dark system bars, notification glyphs, vinyl/stencil work, or one-color output."
    if "monochrome-black/" in relative:
        return "Light system bars, print, engraving masks, or one-color output."
    if relative == "web/favicon.ico":
        return "Multi-resolution legacy browser favicon (16, 32, and 48 px)."
    if name.startswith("favicon-"):
        return f"Browser tab/favicon at {width} px; reference from HTML with rel=icon."
    if name == "apple-touch-icon.png":
        return "iOS/iPadOS home-screen bookmark; reference with rel=apple-touch-icon."
    if name.startswith("maskable-icon-"):
        return "PWA manifest icon with extra safe area; set purpose to maskable."
    if relative.startswith("web/icon-"):
        return "Standard PWA/web-app manifest icon; set purpose to any."
    if relative == "windows/app.ico":
        return "Windows executable, installer, shortcut, and window icon (16–256 px)."
    if name == "BadgeLogo.png":
        return "Windows package badge asset."
    if name == "StoreLogo.png":
        return "Microsoft Store package logo."
    if name == "Wide310x150Logo.png":
        return "Wide Windows Start tile/package visual."
    if relative.startswith("windows/store/"):
        return "Windows package/Start tile asset matching the size encoded in its filename."
    if relative == "macos/AppIcon.icns":
        return "Ready-to-use macOS app-bundle icon containing platform resolutions."
    if relative.startswith("macos/AppIcon.iconset/"):
        return "macOS iconset source; keep the filename unchanged for Xcode or iconutil."
    if relative.startswith("ios/"):
        if name == "icon-1024.png":
            return "App Store marketing icon."
        point_size = name.removeprefix("icon-").split("@")[0]
        role = {"20": "notifications", "29": "Settings", "40": "Spotlight", "60": "iPhone app", "76": "iPad app", "83.5": "iPad Pro app"}.get(point_size, "app")
        return f"iOS/iPadOS {role} icon; use through the included AppIcon asset catalog."
    if "ic_launcher_foreground" in relative:
        return "Android adaptive-icon foreground for the density named in the parent folder."
    if "ic_launcher_round" in relative:
        return "Legacy round Android launcher icon for the named display density."
    if relative.startswith("android/"):
        return "Legacy Android launcher icon for the named display density."
    if relative.startswith("linux/"):
        return "Linux desktop/app-menu icon; install in the matching hicolor size directory."
    if name == "profile-400.png":
        return "Square account, organization, repository, or social profile image."
    if name == "open-graph-1200x630.png":
        return "Open Graph/link-preview image for websites, repositories, and social sharing."
    return "Platform-specific project logo asset."


def write_branding_readme(files: list[dict[str, object]]) -> None:
    image_files = [
        record for record in files
        if Path(str(record["path"])).suffix.lower() in {".png", ".ico", ".icns"}
    ]
    support_files = [record for record in files if record not in image_files]
    lines = [
        "# The Pirate Ray branding",
        "",
        "The official project name is **The Pirate Ray**.",
        "",
        "`the-pirate-ray-logo.png` is the original transparent project logo supplied by",
        "the project owner for use by this project. It is stored without resizing,",
        "re-encoding, or other modification.",
        "",
        "- Dimensions: 1254 x 1254 pixels",
        "- Format: 32-bit ARGB PNG",
        f"- SHA-256: `{SOURCE_SHA256}`",
        "",
        "Use the transparent original by default. If a derivative needs an opaque",
        "background, the background must be black. Do not use another background",
        "color.",
        "",
        "## Quick selection guide",
        "",
        "| Need | Recommended asset |",
        "|---|---|",
        "| General logo with transparency | `generated/png/transparent/` at the nearest suitable size |",
        "| Icon that may be rounded or cropped | `generated/png/safe-zone/` |",
        "| PWA/installable website | `generated/web/site.webmanifest` and `maskable-icon-*` |",
        "| Windows application | `generated/windows/app.ico` |",
        "| macOS application | `generated/macos/AppIcon.icns` |",
        "| iPhone/iPad application | `generated/ios/AppIcon.appiconset/` |",
        "| Android application | `generated/android/` |",
        "| Linux desktop application | `generated/linux/hicolor/` |",
        "| Tray, notification, stencil, or engraving | `generated/png/monochrome-white/` or `monochrome-black/` |",
        "| Social profile or link preview | `generated/social/` |",
        "",
        f"The catalog below lists all {len(image_files)} generated image files individually.",
        "",
        "## Canonical artwork",
        "",
        "| Preview | File | Dimensions | Background / safe area | Recommended use |",
        "|---|---|---:|---|---|",
        '<img src="the-pirate-ray-logo.png" width="64" alt="Original The Pirate Ray logo"> | [`the-pirate-ray-logo.png`](the-pirate-ray-logo.png) | 1254 x 1254 | Transparent, full-bleed | Canonical master. Use for new derivatives and full-resolution layouts; never overwrite or re-encode it. |',
    ]

    for prefix, title in CATALOG_GROUPS:
        records = [record for record in image_files if str(record["path"]).startswith(prefix)]
        records.sort(key=lambda record: (record.get("width", 0), str(record["path"])))
        if not records:
            continue
        lines.extend([
            "",
            f"## {title}",
            "",
            "| Preview | File | Dimensions | Background / safe area | Recommended use |",
            "|---|---|---:|---|---|",
        ])
        for record in records:
            relative = str(record["path"])
            width = record.get("width")
            height = record.get("height")
            if width and height:
                dimensions = f"{width} x {height}"
            elif relative == "windows/app.ico":
                dimensions = "16–256 px"
            elif relative == "web/favicon.ico":
                dimensions = "16–48 px"
            else:
                dimensions = "16–1024 px"
            preview_relative = {
                "web/favicon.ico": "web/favicon-32x32.png",
                "windows/app.ico": "windows/store/Square150x150Logo.png",
                "macos/AppIcon.icns": "macos/AppIcon.iconset/icon_128x128.png",
            }.get(relative, relative)
            preview_style = ""
            if "monochrome-white/" in relative:
                preview_style = ' style="background:#222;padding:4px"'
            elif "monochrome-black/" in relative:
                preview_style = ' style="background:#eee;padding:4px"'
            preview = f'<img src="generated/{preview_relative}" width="48" alt="Preview of {Path(relative).name}"{preview_style}>'
            link = f"[`{relative}`](generated/{relative})"
            lines.append(
                f"{preview} | {link} | {dimensions} | {catalog_background(relative)} | {catalog_usage(relative, width if isinstance(width, int) else None)} |"
            )

    lines.extend([
        "",
        "## Supporting manifests and configuration",
        "",
        "These files are not logos themselves, but make the image sets copy-ready for",
        "their target platforms.",
        "",
        "| File | Purpose |",
        "|---|---|",
        "[`manifest.json`](generated/manifest.json) | Inventory with byte sizes, dimensions, and SHA-256 for every generated file. |",
    ])
    support_usage = {
        "web/site.webmanifest": "Ready-to-adapt PWA manifest with regular and maskable icon declarations.",
        "ios/AppIcon.appiconset/Contents.json": "Xcode asset-catalog mapping for every iOS and iPadOS icon.",
        "android/mipmap-anydpi-v26/ic_launcher.xml": "Android adaptive launcher icon declaration.",
        "android/mipmap-anydpi-v26/ic_launcher_round.xml": "Android adaptive round launcher icon declaration.",
        "android/values/ic_launcher_background.xml": "Required black Android adaptive-icon background color.",
    }
    for record in support_files:
        relative = str(record["path"])
        purpose = support_usage.get(relative, "Platform support/configuration file.")
        lines.append(f"[`{relative}`](generated/{relative}) | {purpose} |")

    lines.extend([
        "",
        "## Regeneration and integrity",
        "",
        "The complete catalog is generated deterministically from the canonical logo.",
        "`generated/manifest.json` records every derivative's dimensions and SHA-256.",
        "Regenerate the assets and this README from the repository root with:",
        "",
        "```powershell",
        "uv run --with pillow python scripts/generate_brand_assets.py",
        "```",
        "",
        "The repository does not yet have a project license. This directory records",
        "the asset's provenance and approved presentation; it does not independently",
        "grant broader rights or select a license.",
        "",
    ])
    BRANDING_README.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def generate_ios(source: Image.Image) -> None:
    directory = OUTPUT / "ios" / "AppIcon.appiconset"
    specs = (
        (20, 2, "iphone"), (20, 3, "iphone"),
        (29, 2, "iphone"), (29, 3, "iphone"),
        (40, 2, "iphone"), (40, 3, "iphone"),
        (60, 2, "iphone"), (60, 3, "iphone"),
        (20, 1, "ipad"), (20, 2, "ipad"),
        (29, 1, "ipad"), (29, 2, "ipad"),
        (40, 1, "ipad"), (40, 2, "ipad"),
        (76, 1, "ipad"), (76, 2, "ipad"),
        (83.5, 2, "ipad"),
    )
    images = []
    for points, scale, idiom in specs:
        pixels = round(points * scale)
        point_label = format(points, "g")
        filename = f"icon-{point_label}@{scale}x.png"
        save_png(on_black(source, pixels, 0.78), directory / filename)
        images.append({
            "filename": filename,
            "idiom": idiom,
            "scale": f"{scale}x",
            "size": f"{points}x{points}",
        })
    save_png(on_black(source, 1024, 0.78), directory / "icon-1024.png")
    images.append({
        "filename": "icon-1024.png",
        "idiom": "ios-marketing",
        "scale": "1x",
        "size": "1024x1024",
    })
    contents = {"images": images, "info": {"author": "xcode", "version": 1}}
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "Contents.json").write_text(
        json.dumps(contents, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def generate_android(source: Image.Image) -> None:
    densities = {
        "mdpi": 48,
        "hdpi": 72,
        "xhdpi": 96,
        "xxhdpi": 144,
        "xxxhdpi": 192,
    }
    adaptive = {
        "mdpi": 108,
        "hdpi": 162,
        "xhdpi": 216,
        "xxhdpi": 324,
        "xxxhdpi": 432,
    }
    for density, size in densities.items():
        save_png(on_black(source, size, 0.78), OUTPUT / "android" / f"mipmap-{density}" / "ic_launcher.png")
        save_png(on_black(source, size, 0.78), OUTPUT / "android" / f"mipmap-{density}" / "ic_launcher_round.png")
    for density, size in adaptive.items():
        save_png(fit(source, size, 0.66), OUTPUT / "android" / f"drawable-{density}" / "ic_launcher_foreground.png")
    adaptive_xml = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
</adaptive-icon>
"""
    anydpi = OUTPUT / "android" / "mipmap-anydpi-v26"
    anydpi.mkdir(parents=True, exist_ok=True)
    (anydpi / "ic_launcher.xml").write_text(
        adaptive_xml, encoding="utf-8", newline="\n"
    )
    (anydpi / "ic_launcher_round.xml").write_text(
        adaptive_xml, encoding="utf-8", newline="\n"
    )
    values = OUTPUT / "android" / "values"
    values.mkdir(parents=True, exist_ok=True)
    (values / "ic_launcher_background.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#000000</color>
</resources>
""",
        encoding="utf-8",
        newline="\n",
    )


def generate_macos(source: Image.Image) -> None:
    directory = OUTPUT / "macos" / "AppIcon.iconset"
    specs = ((16, 1), (16, 2), (32, 1), (32, 2), (128, 1), (128, 2), (256, 1), (256, 2), (512, 1), (512, 2))
    for points, scale in specs:
        pixels = points * scale
        suffix = "" if scale == 1 else "@2x"
        save_png(on_black(source, pixels, 0.78), directory / f"icon_{points}x{points}{suffix}.png")
    icns_source = on_black(source, 1024, 0.78)
    icns_source.save(OUTPUT / "macos" / "AppIcon.icns", format="ICNS")


def generate_windows(source: Image.Image) -> None:
    directory = OUTPUT / "windows"
    directory.mkdir(parents=True, exist_ok=True)
    icon = on_black(source, 256, 0.78)
    icon.save(
        directory / "app.ico",
        format="ICO",
        sizes=[(16, 16), (20, 20), (24, 24), (32, 32), (40, 40), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    for size in (44, 71, 150, 310):
        save_png(on_black(source, size, 0.72), directory / "store" / f"Square{size}x{size}Logo.png")
    save_png(on_black(source, 50, 0.72), directory / "store" / "StoreLogo.png")
    save_png(on_black(source, 24, 0.72), directory / "store" / "BadgeLogo.png")
    wide = Image.new("RGBA", (310, 150), (0, 0, 0, 255))
    wide.alpha_composite(fit(source, 140, 0.78), ((310 - 140) // 2, 5))
    save_png(wide, directory / "store" / "Wide310x150Logo.png")


def generate() -> None:
    if sha256(SOURCE) != SOURCE_SHA256:
        raise SystemExit("Canonical logo hash changed; inspect it before regenerating derivatives.")

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    with Image.open(SOURCE) as opened:
        source = opened.convert("RGBA")

    for size in PNG_SIZES:
        save_png(fit(source, size), OUTPUT / "png" / "transparent" / f"logo-{size}.png")
        save_png(on_black(source, size, 0.82), OUTPUT / "png" / "on-black" / f"logo-{size}.png")

    for size in APP_SIZES:
        save_png(fit(source, size, 0.78), OUTPUT / "png" / "safe-zone" / f"logo-{size}.png")
        save_png(monochrome(source, size, (255, 255, 255)), OUTPUT / "png" / "monochrome-white" / f"logo-{size}.png")
        save_png(monochrome(source, size, (0, 0, 0)), OUTPUT / "png" / "monochrome-black" / f"logo-{size}.png")

    web = OUTPUT / "web"
    save_png(fit(source, 16), web / "favicon-16x16.png")
    save_png(fit(source, 32), web / "favicon-32x32.png")
    save_png(on_black(source, 180, 0.78), web / "apple-touch-icon.png")
    save_png(fit(source, 192, 0.90), web / "icon-192.png")
    save_png(fit(source, 512, 0.90), web / "icon-512.png")
    save_png(on_black(source, 192, 0.66), web / "maskable-icon-192.png")
    save_png(on_black(source, 512, 0.66), web / "maskable-icon-512.png")
    fit(source, 256).save(web / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    webmanifest = {
        "name": "The Pirate Ray",
        "short_name": "Pirate Ray",
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "maskable-icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
            {"src": "maskable-icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
        "theme_color": "#000000",
        "background_color": "#000000",
        "display": "standalone",
    }
    (web / "site.webmanifest").write_text(
        json.dumps(webmanifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    generate_windows(source)
    generate_macos(source)
    generate_ios(source)
    generate_android(source)

    for size in (16, 22, 24, 32, 48, 64, 128, 256, 512):
        save_png(fit(source, size, 0.82), OUTPUT / "linux" / "hicolor" / f"{size}x{size}" / "apps" / "the-pirate-ray.png")

    save_png(on_black(source, 400, 0.82), OUTPUT / "social" / "profile-400.png")
    og = Image.new("RGBA", (1200, 630), (0, 0, 0, 255))
    og.alpha_composite(fit(source, 560, 0.84), ((1200 - 560) // 2, (630 - 560) // 2))
    save_png(og, OUTPUT / "social" / "open-graph-1200x630.png")

    files = []
    for path in sorted(p for p in OUTPUT.rglob("*") if p.is_file()):
        relative = path.relative_to(OUTPUT).as_posix()
        record = {"path": relative, "sha256": sha256(path), "bytes": path.stat().st_size}
        if path.suffix.lower() == ".png":
            with Image.open(path) as image:
                record.update({"width": image.width, "height": image.height, "mode": image.mode})
        files.append(record)
    manifest = {
        "schemaVersion": 1,
        "source": "../the-pirate-ray-logo.png",
        "sourceSha256": SOURCE_SHA256,
        "generation": "uv run --with pillow python scripts/generate_brand_assets.py",
        "files": files,
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_branding_readme(files)


if __name__ == "__main__":
    generate()
