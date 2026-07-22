#!/usr/bin/env python3
"""Merge platform-specific Unity CLI command trees without losing differences."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PLATFORMS = ("linux", "macos", "windows")
MERGED_FIELDS = (
    "summary",
    "description",
    "usage",
    "arguments",
    "options",
    "subcommands",
    "examples",
    "environment_variables",
    "exit_codes",
    "deprecation_notices",
    "experimental_notices",
    "platform_restrictions",
    "extra_sections",
    "has_unknown_sections",
    "raw_mentions_experimental",
)


class MergeError(RuntimeError):
    """Raised for incompatible platform inputs."""


def _semantic(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    if isinstance(value, list):
        return [_semantic(item) for item in value]
    if isinstance(value, dict):
        return {key: _semantic(item) for key, item in value.items()}
    return value


def _stable_key(value: Any) -> str:
    return json.dumps(_semantic(value), sort_keys=True, ensure_ascii=False)


def _common_value(values: dict[str, Any]) -> Any:
    counts = Counter(_stable_key(value) for value in values.values())
    key = sorted(counts, key=lambda item: (-counts[item], item))[0]
    selected = next(
        value for platform, value in sorted(values.items()) if _stable_key(value) == key
    )
    return json.loads(json.dumps(selected, ensure_ascii=False))


def merge_trees(trees: list[dict[str, Any]], *, require_all: bool = True) -> dict[str, Any]:
    by_platform: dict[str, dict[str, Any]] = {}
    for tree in trees:
        platform = tree.get("platform")
        if platform not in PLATFORMS or platform in by_platform:
            raise MergeError(f"invalid or duplicate platform: {platform!r}")
        by_platform[platform] = tree
    if require_all and set(by_platform) != set(PLATFORMS):
        raise MergeError("linux, macos, and windows trees are all required")
    versions = {tree["cli_version"] for tree in trees}
    if len(versions) != 1:
        raise MergeError(f"platform CLI versions differ: {sorted(versions)}")

    commands_by_path: dict[tuple[str, ...], dict[str, dict[str, Any]]] = {}
    for platform, tree in by_platform.items():
        for command in tree["commands"]:
            path = tuple(command["path"])
            commands_by_path.setdefault(path, {})[platform] = command

    merged_commands: list[dict[str, Any]] = []
    for path, variants in sorted(commands_by_path.items()):
        base: dict[str, Any] = {
            "path": list(path),
            "name": path[-1] if path else "unity",
            "aliases": sorted(
                {alias for command in variants.values() for alias in command.get("aliases", [])}
            ),
        }
        overrides: dict[str, dict[str, Any]] = {}
        alias_sets = {
            platform: sorted(command.get("aliases", [])) for platform, command in variants.items()
        }
        if len({_stable_key(aliases) for aliases in alias_sets.values()}) > 1:
            for platform, aliases in alias_sets.items():
                overrides.setdefault(platform, {})["aliases"] = aliases
        for field in MERGED_FIELDS:
            values = {
                platform: command.get(field, [] if field.endswith("s") else "")
                for platform, command in variants.items()
            }
            common = _common_value(values)
            base[field] = common
            for platform, value in values.items():
                if _stable_key(value) != _stable_key(common):
                    overrides.setdefault(platform, {})[field] = value
        base["availability"] = {platform: platform in variants for platform in PLATFORMS}
        base["platform_overrides"] = overrides
        base["source_hashes"] = {
            platform: command["source_hash"] for platform, command in sorted(variants.items())
        }
        merged_commands.append(base)

    return {
        "schema_version": 1,
        "cli_version": versions.pop(),
        "platforms": list(PLATFORMS),
        "commands": merged_commands,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        trees = [json.loads(path.read_text(encoding="utf-8")) for path in args.inputs]
        merged = merge_trees(trees)
    except (OSError, json.JSONDecodeError, MergeError, KeyError) as exc:
        print(f"merge failed: {exc}", file=sys.stderr)
        return 1
    args.output.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
