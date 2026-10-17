#!/usr/bin/env python3
"""Fail when public tracked content resembles private or vendor raw data."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

DISALLOWED_SUFFIXES = {
    ".7z", ".clb", ".dll", ".ezd", ".lbprefs", ".lbzip", ".plg", ".rar", ".zip"
}
SENSITIVE_TEXT = {
    "Google Drive URL": re.compile(
        r"https://drive" r"\.google\.com/(?:drive/folders|file/d)/[A-Za-z0-9_-]+"
    ),
    "Windows user path": re.compile(r"C:\\Users\\[^\\\s]+", re.IGNORECASE),
    "License-key indicator": re.compile(
        r"light" r"burn.{0,30}license.{0,15}key", re.IGNORECASE
    ),
}
TEXT_SUFFIXES = {"", ".json", ".jsonl", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}


def tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True
    )
    return [root / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def check(root: Path, deny_patterns: tuple[str, ...] = ()) -> list[str]:
    failures: list[str] = []
    for path in tracked_files(root):
        relative = path.relative_to(root).as_posix()
        suffix = path.suffix.lower()
        if suffix in DISALLOWED_SUFFIXES:
            failures.append(f"disallowed public artifact: {relative}")
            continue
        if suffix not in TEXT_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            failures.append(f"unexpected binary content in public text file: {relative}")
            continue
        for label, pattern in SENSITIVE_TEXT.items():
            if pattern.search(content):
                failures.append(f"{label} found in {relative}")
        folded = content.casefold()
        for pattern in deny_patterns:
            if pattern.casefold() in folded:
                failures.append(f"private deny-list token found in {relative}")
    return failures


def load_deny_patterns(path: Path | None) -> tuple[str, ...]:
    if path is None:
        return ()
    patterns = []
    for line in path.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if candidate and not candidate.startswith("#"):
            patterns.append(candidate)
    return tuple(patterns)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument(
        "--deny-pattern-file",
        type=Path,
        help="private newline-delimited literal tokens that must not appear publicly",
    )
    args = parser.parse_args()
    failures = check(
        args.root.resolve(), load_deny_patterns(args.deny_pattern_file)
    )
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print("public repository guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
