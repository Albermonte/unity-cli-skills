from __future__ import annotations

from pathlib import Path

import pytest
from conftest import invocation

from scripts.parse_help import ParseError, parse_help_text, parse_snapshot


def test_parses_realistic_sections(fixture_dir: Path) -> None:
    parsed = parse_help_text(["editors"], (fixture_dir / "editors-help.txt").read_text())
    assert parsed["usage"] == ["unity editors|e [options] [command]"]
    assert parsed["subcommands"][1]["name"] == "add"
    assert parsed["options"][1]["value"] == "<arch>"
    assert parsed["options"][1]["choices"] == ["arm64", "x86_64"]
    assert parsed["examples"] == ["unity editors --installed --format json"]
    assert parsed["exit_codes"][1]["code"] == "1"
    assert parsed["extra_sections"][0]["heading"] == "Future Section"


def test_parses_aliases_short_long_repeatable_and_crlf(fixture_dir: Path) -> None:
    parsed = parse_help_text(["install"], (fixture_dir / "install-help.txt").read_text())
    module = parsed["options"][0]
    assert module["names"] == ["-m", "--module"]
    assert module["repeatable"] is True
    assert parsed["arguments"][0]["required"] is False
    assert parsed["options"][2]["default"] == "beta"


def test_extracts_environment_variable_from_option(fixture_dir: Path) -> None:
    parsed = parse_help_text([], (fixture_dir / "top-help.txt").read_text())
    assert parsed["environment_variables"] == [
        {"name": "UNITY_FORMAT", "description": "Mirrors --format."}
    ]
    assert parsed["subcommands"][0]["aliases"] == ["e"]


def test_snapshot_requires_nested_help(fixture_dir: Path) -> None:
    top = (fixture_dir / "top-help.txt").read_text()
    snapshot = {
        "platform": "linux",
        "architecture": "x86_64",
        "cli_version": "1.0.0-test",
        "invocations": [invocation([], top)],
    }
    with pytest.raises(ParseError, match="incomplete recursive collection"):
        parse_snapshot(snapshot)


def test_nonzero_help_fails() -> None:
    snapshot = {
        "platform": "linux",
        "architecture": "x86_64",
        "cli_version": "1",
        "invocations": [invocation([], "", exit_code=2)],
    }
    with pytest.raises(ParseError, match="nonzero"):
        parse_snapshot(snapshot)
