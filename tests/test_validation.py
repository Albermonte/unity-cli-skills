from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.skills_ref_cli import validation_errors
from scripts.validate_generated import (
    ValidationError,
    count_discovered_skill,
    validate_repository,
)

ROOT = Path(__file__).parents[1]


def copy_repository(tmp_path: Path) -> Path:
    destination = tmp_path / "repo"
    shutil.copytree(ROOT, destination, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    return destination


def test_repository_validates() -> None:
    validate_repository(ROOT)
    assert validation_errors(ROOT) == []


def test_counts_decorated_skills_cli_row() -> None:
    output = "\x1b[?25l│\n◇  Available Skills\n│\n│    unity-cli\n│\n│      Use unity-cli safely\n"
    assert count_discovered_skill(output, "unity-cli") == 1


def test_broken_link_fails(tmp_path: Path) -> None:
    root = copy_repository(tmp_path)
    with (root / "SKILL.md").open("a") as handle:
        handle.write("\n[broken](references/missing.md)\n")
    with pytest.raises(ValidationError, match="broken relative link"):
        validate_repository(root)


def test_invalid_schema_fails(tmp_path: Path) -> None:
    root = copy_repository(tmp_path)
    tree = json.loads((root / "data" / "command-tree.json").read_text())
    tree["schema_version"] = 2
    (root / "data" / "command-tree.json").write_text(json.dumps(tree))
    with pytest.raises(Exception, match="1 was expected"):
        validate_repository(root)


def test_multiple_skill_files_fail(tmp_path: Path) -> None:
    root = copy_repository(tmp_path)
    extra = root / "nested" / "SKILL.md"
    extra.parent.mkdir()
    extra.write_text("---\nname: nested\ndescription: Use when testing.\n---\n")
    with pytest.raises(ValidationError, match="only SKILL.md"):
        validate_repository(root)


@pytest.mark.skipif(
    os.environ.get("RUN_SKILLS_CLI_INTEGRATION") != "1", reason="explicit integration test"
)
def test_root_skills_cli_discovery() -> None:
    result = subprocess.run(
        ["npx", "skills", "add", ".", "--list"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert [line.strip() for line in result.stdout.splitlines() if line.strip() == "unity-cli"] == [
        "unity-cli"
    ]
