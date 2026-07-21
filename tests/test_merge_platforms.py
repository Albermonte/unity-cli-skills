from __future__ import annotations

import pytest

from scripts.merge_platforms import MergeError, merge_trees


def tree(platform: str, *, option: str = "--common") -> dict[str, object]:
    return {
        "platform": platform,
        "cli_version": "1",
        "commands": [
            {
                "path": ["editors"],
                "name": "editors",
                "aliases": ["e"],
                "summary": "Manage editors",
                "description": "",
                "usage": ["unity editors"],
                "arguments": [],
                "options": [
                    {
                        "names": [option],
                        "value": None,
                        "description": "",
                        "required": False,
                        "repeatable": False,
                        "default": None,
                        "choices": [],
                    }
                ],
                "subcommands": [],
                "examples": [],
                "environment_variables": [],
                "exit_codes": [],
                "deprecation_notices": [],
                "experimental_notices": [],
                "platform_restrictions": [],
                "extra_sections": [],
                "has_unknown_sections": False,
                "raw_mentions_experimental": False,
                "source_hash": platform[0] * 64,
            }
        ],
    }


def test_merges_platform_difference() -> None:
    merged = merge_trees([tree("linux"), tree("macos", option="--arch"), tree("windows")])
    command = merged["commands"][0]
    assert command["availability"] == {"linux": True, "macos": True, "windows": True}
    assert "macos" in command["platform_overrides"]


def test_requires_every_platform() -> None:
    with pytest.raises(MergeError, match="all required"):
        merge_trees([tree("macos")])


def test_partial_merge_marks_availability() -> None:
    merged = merge_trees([tree("macos")], require_all=False)
    assert merged["commands"][0]["availability"]["linux"] is False


def test_rejects_version_mismatch() -> None:
    windows = tree("windows")
    windows["cli_version"] = "2"
    with pytest.raises(MergeError, match="versions differ"):
        merge_trees([tree("linux"), tree("macos"), windows])
