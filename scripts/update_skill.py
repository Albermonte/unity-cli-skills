#!/usr/bin/env python3
"""Run the deterministic snapshot-to-reference update pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from scripts.collect_help import PLATFORM_NAMES, collect, write_json_atomic
from scripts.generate_references import generate
from scripts.merge_platforms import MergeError, merge_trees
from scripts.parse_help import parse_snapshot
from scripts.semantic_diff import render_markdown, semantic_diff

PLATFORMS = ("linux", "macos", "windows")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(snapshot_paths: dict[str, Path], tree: dict[str, Any]) -> dict[str, Any]:
    snapshots = {
        platform_name: json.loads(path.read_text(encoding="utf-8"))
        for platform_name, path in snapshot_paths.items()
    }
    return {
        "schema_version": 1,
        "cli_version": tree["cli_version"],
        "canonical_source": "installed Unity CLI help output",
        "generated_without_ai": True,
        "snapshots": [
            {
                "platform": platform_name,
                "architecture": snapshots[platform_name]["architecture"],
                "source": "live_help",
                "path": str(path),
                "sha256": _hash(path),
            }
            for platform_name, path in sorted(snapshot_paths.items())
        ],
    }


def update(
    root: Path,
    snapshot_paths: dict[str, Path],
    *,
    allow_partial: bool = False,
) -> dict[str, Any]:
    if not allow_partial and set(snapshot_paths) != set(PLATFORMS):
        raise MergeError("all three platform snapshots are required")
    snapshots = {
        platform_name: json.loads(path.read_text(encoding="utf-8"))
        for platform_name, path in snapshot_paths.items()
    }
    for platform_name, snapshot in snapshots.items():
        if snapshot["platform"] != platform_name:
            raise MergeError(f"snapshot platform mismatch: {platform_name}")
    trees = [parse_snapshot(snapshot) for snapshot in snapshots.values()]
    merged = merge_trees(trees, require_all=not allow_partial)
    old_path = root / "data" / "command-tree.json"
    old = json.loads(old_path.read_text(encoding="utf-8")) if old_path.exists() else merged
    diff = semantic_diff(old, merged)

    with tempfile.TemporaryDirectory() as directory:
        stage = Path(directory)
        stage_tree = stage / "command-tree.json"
        stage_tree.write_text(
            json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        generate(merged, stage / "references")
        (root / "data").mkdir(parents=True, exist_ok=True)
        shutil.copy2(stage_tree, old_path)
        generate(merged, root / "references")
    (root / "data" / "source-manifest.json").write_text(
        json.dumps(_manifest(snapshot_paths, merged), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (root / "semantic-diff.json").write_text(json.dumps(diff, indent=2) + "\n", encoding="utf-8")
    (root / "semantic-diff.md").write_text(render_markdown(diff), encoding="utf-8")
    return diff


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--snapshot", action="append", default=[], metavar="PLATFORM=PATH")
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--unity", default="unity")
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    paths: dict[str, Path] = {}
    for item in args.snapshot:
        platform_name, separator, raw_path = item.partition("=")
        if not separator or platform_name not in PLATFORMS:
            parser.error(f"invalid --snapshot value: {item}")
        paths[platform_name] = Path(raw_path)
    if args.collect:
        platform_name = PLATFORM_NAMES.get(platform.system())
        if platform_name is None:
            parser.error("unsupported local platform")
        path = root / "snapshots" / platform_name / "help.json"
        write_json_atomic(collect(args.unity, platform_name=platform_name, progress=True), path)
        paths[platform_name] = path
    try:
        diff = update(root, paths, allow_partial=args.allow_partial)
    except (OSError, ValueError, KeyError, MergeError) as exc:
        print(f"update failed: {exc}", file=sys.stderr)
        return 1
    print("semantic changes" if diff["changed"] else "no semantic changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
