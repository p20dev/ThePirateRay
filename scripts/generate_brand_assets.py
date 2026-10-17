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
SOURCE_SHA256 = "afcd7e457b5bf9cf92a7222b3ab8a2850d75c05bc2c37d242c959cd7569e6fa4"
PNG_SIZES = (16, 20, 24, 32, 40, 48, 64, 72, 96, 128, 144, 152, 180, 192, 256, 384, 512, 1024)
APP_SIZES = (16, 32, 48, 64, 128, 256, 512, 1024)


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
        json.dumps(contents, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
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
    (anydpi / "ic_launcher.xml").write_text(adaptive_xml, encoding="utf-8")
    (anydpi / "ic_launcher_round.xml").write_text(adaptive_xml, encoding="utf-8")
    values = OUTPUT / "android" / "values"
    values.mkdir(parents=True, exist_ok=True)
    (values / "ic_launcher_background.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#000000</color>
</resources>
""",
        encoding="utf-8",
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
        json.dumps(webmanifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
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
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    generate()
