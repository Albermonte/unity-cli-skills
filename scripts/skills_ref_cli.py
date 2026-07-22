#!/usr/bin/env python3
"""Run the reference validator for a skill directory."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path
from typing import cast

import yaml
from skills_ref.validator import validate  # type: ignore[import-untyped]


def validation_errors(skill_directory: Path) -> list[str]:
    skill_file = skill_directory / "SKILL.md"
    if not skill_file.is_file():
        return ["SKILL.md not found"]
    text = skill_file.read_text(encoding="utf-8")
    try:
        frontmatter = yaml.safe_load(text.split("---", 2)[1])
        name = frontmatter["name"]
    except (IndexError, KeyError, TypeError, yaml.YAMLError):
        return cast(list[str], validate(skill_directory))
    if skill_directory.name == name:
        return cast(list[str], validate(skill_directory))
    with tempfile.TemporaryDirectory() as directory:
        normalized = Path(directory) / name
        normalized.mkdir()
        shutil.copy2(skill_file, normalized / "SKILL.md")
        return cast(list[str], validate(normalized))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate",))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    errors = validation_errors(args.directory.resolve())
    if errors:
        print(f"Validation failed for {args.directory}:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"Valid skill: {args.directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
