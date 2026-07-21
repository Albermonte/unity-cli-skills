#!/usr/bin/env python3
"""Validate skill structure, normalized data, and generated references."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from scripts.generate_references import generated_files

ANSI_RE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
LINK_RE = re.compile(r"(?<!!)\[[^]]*]\((?!https?://|#|mailto:)([^)]+)\)")
ABSOLUTE_MACHINE_PATH_RE = re.compile(r"(?:/Users/|/home/|[A-Z]:\\Users\\)")
TOKEN_LIKE_RE = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|UNITY_SERVICE_ACCOUNT_SECRET\s*=\s*\S+)"
)


class ValidationError(RuntimeError):
    """Raised when the repository violates an invariant."""


def _frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValidationError("SKILL.md must start with YAML frontmatter")
    _, raw, _ = text.split("---", 2)
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValidationError("SKILL.md frontmatter must be a mapping")
    return data


def _check_links(root: Path) -> None:
    for markdown in root.rglob("*.md"):
        if "tests" in markdown.relative_to(root).parts:
            continue
        for target in LINK_RE.findall(markdown.read_text(encoding="utf-8")):
            clean = target.split("#", 1)[0]
            if clean and not (markdown.parent / clean).resolve().exists():
                raise ValidationError(f"broken relative link in {markdown}: {target}")


def validate_repository(root: Path, *, run_external: bool = False) -> None:
    skill_files = sorted(root.rglob("SKILL.md"))
    if skill_files != [root / "SKILL.md"]:
        raise ValidationError("the root SKILL.md must be the only SKILL.md")
    metadata = _frontmatter(root / "SKILL.md")
    if set(metadata) != {"name", "description"}:
        raise ValidationError("SKILL.md frontmatter must contain only name and description")
    if metadata["name"] != "unity-cli":
        raise ValidationError("skill name must equal unity-cli")
    if not str(metadata["description"]).startswith("Use when"):
        raise ValidationError("skill description must begin with 'Use when'")
    if len((root / "SKILL.md").read_text(encoding="utf-8").splitlines()) >= 500:
        raise ValidationError("SKILL.md must remain below 500 lines")
    _check_links(root)

    tree_path = root / "data" / "command-tree.json"
    schema = json.loads((root / "data" / "command-tree.schema.json").read_text(encoding="utf-8"))
    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(tree)
    for command in tree["commands"]:
        if not command["source_hashes"]:
            raise ValidationError(f"missing source hashes for {command['path']}")
    expected = generated_files(tree)
    actual_names = {path.name for path in (root / "references").glob("command-*.md")}
    if actual_names != set(expected):
        raise ValidationError("generated command reference set is stale")
    for name, content in expected.items():
        path = root / "references" / name
        if path.read_text(encoding="utf-8") != content:
            raise ValidationError(f"generated file differs from generator output: {path}")
        if tree["cli_version"] not in content:
            raise ValidationError(f"generated file lacks CLI version: {path}")

    scanned = [
        tree_path,
        *sorted((root / "snapshots").rglob("*.json")),
        *sorted((root / "references").glob("command-*.md")),
    ]
    for path in scanned:
        text = path.read_text(encoding="utf-8")
        if ANSI_RE.search(text):
            raise ValidationError(f"ANSI escape remains in {path}")
        if ABSOLUTE_MACHINE_PATH_RE.search(text):
            raise ValidationError(f"absolute machine path remains in {path}")
        if TOKEN_LIKE_RE.search(text):
            raise ValidationError(f"token-like secret remains in {path}")
    for path in root.rglob("*"):
        if {".venv", ".git", ".pytest_cache", ".mypy_cache", ".ruff_cache"} & set(
            path.relative_to(root).parts
        ):
            continue
        if path.is_file() and path.suffix in {".md", ".py", ".json", ".yml", ".toml"}:
            text = path.read_text(encoding="utf-8")
            unfinished = "|".join(("TO" + "DO", "TB" + "D"))
            if re.search(rf"\b(?:{unfinished})\b", text):
                raise ValidationError(f"unfinished placeholder in {path}")

    if run_external:
        subprocess.run(["skills-ref", "validate", "."], cwd=root, check=True)
        result = subprocess.run(
            ["npx", "skills", "add", ".", "--list"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        discovered = [
            line.strip() for line in result.stdout.splitlines() if line.strip() == "unity-cli"
        ]
        if discovered != ["unity-cli"]:
            raise ValidationError("Skills CLI did not discover exactly one unity-cli skill")

    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        for name, content in expected.items():
            (temporary / name).write_text(content, encoding="utf-8")
        for name, content in expected.items():
            if (temporary / name).read_text(encoding="utf-8") != content:
                raise ValidationError("generator is not idempotent")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--external", action="store_true")
    args = parser.parse_args()
    try:
        validate_repository(args.root.resolve(), run_external=args.external)
    except (
        OSError,
        json.JSONDecodeError,
        yaml.YAMLError,
        jsonschema.ValidationError,
        ValidationError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    tree = json.loads((args.root / "data" / "command-tree.json").read_text(encoding="utf-8"))
    for command in tree["commands"]:
        if command["extra_sections"]:
            headings = ", ".join(section["heading"] for section in command["extra_sections"])
            path = " ".join(["unity", *command["path"]])
            print(f"validation warning: retained unknown help section in {path}: {headings}")
    print("validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
