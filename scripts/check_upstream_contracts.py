"""Verify pinned upstream licenses, source hashes, and required API symbols."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text_sha256_lf(path: Path) -> str:
    normalized = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _git_commit(path: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    symbols: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(node.name)
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.add(f"{node.name}.{child.name}")
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    symbols.add(target.id)
    return symbols


def inspect_tree(manifest: dict, checkout: Path, observed_commit: str) -> dict:
    failures = []
    if observed_commit != manifest["commit"]:
        failures.append(
            f"commit mismatch: expected {manifest['commit']}, found {observed_commit}"
        )

    license_record = manifest["license_file"]
    license_path = checkout / license_record["path"]
    if not license_path.is_file():
        failures.append(f"missing license file: {license_record['path']}")
    elif _text_sha256_lf(license_path) != license_record["sha256_lf"]:
        failures.append(f"license hash mismatch: {license_record['path']}")

    contracts = []
    for record in manifest["contract_files"]:
        path = checkout / record["path"]
        missing_symbols = []
        if not path.is_file():
            failures.append(f"missing contract file: {record['path']}")
        else:
            if _sha256(path) != record["sha256"]:
                failures.append(f"contract hash mismatch: {record['path']}")
            available = _symbols(path)
            missing_symbols = sorted(set(record["required_symbols"]) - available)
            if missing_symbols:
                failures.append(
                    f"missing symbols in {record['path']}: {', '.join(missing_symbols)}"
                )
        contracts.append({
            "path": record["path"],
            "stability": record["stability"],
            "required_symbols": record["required_symbols"],
            "missing_symbols": missing_symbols,
        })

    return {
        "name": manifest["name"],
        "repository": manifest["repository"],
        "commit": observed_commit,
        "license": manifest["license"],
        "license_sha256_lf": license_record["sha256_lf"],
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "contracts": contracts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rayforge", type=Path, required=True)
    parser.add_argument("--meerk40t", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    results = []
    for name, checkout in (("rayforge", args.rayforge), ("meerk40t", args.meerk40t)):
        manifest = json.loads(
            (ROOT / "upstreams" / f"{name}.json").read_text(encoding="utf-8")
        )
        resolved = checkout.resolve()
        results.append(inspect_tree(manifest, resolved, _git_commit(resolved)))
    report = {
        "status": "passed" if all(item["status"] == "passed" for item in results) else "failed",
        "hardware_access": False,
        "upstreams": results,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"status={report['status']}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
