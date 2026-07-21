from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures"


def command(path: list[str], **overrides: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "path": path,
        "name": path[-1] if path else "unity",
        "aliases": [],
        "summary": "summary",
        "description": "",
        "usage": [],
        "arguments": [],
        "options": [],
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
        "availability": {"linux": True, "macos": True, "windows": True},
        "platform_overrides": {},
        "source_hashes": {"linux": "a" * 64, "macos": "b" * 64, "windows": "c" * 64},
    }
    value.update(overrides)
    return value


def invocation(path: list[str], stdout: str, *, exit_code: int = 0) -> dict[str, Any]:
    normalized = hashlib.sha256(f"stdout\0{stdout}\0stderr\0".encode()).hexdigest()
    return {
        "command_path": path,
        "argv": ["unity", *path, "--help"],
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": "",
        "platform": "linux",
        "architecture": "x86_64",
        "cli_version": "1.0.0-test",
        "normalized_sha256": normalized,
    }
