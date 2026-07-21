#!/usr/bin/env python3
"""Collect recursive Unity CLI help without executing command behavior."""

from __future__ import annotations

import argparse
import hashlib
import json
import locale
import os
import platform as host_platform
import re
import subprocess
import sys
from collections import deque
from collections.abc import Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ANSI_RE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$", re.ASCII)
DEFAULT_ENV = {
    "CI": "true",
    "TERM": "dumb",
    "NO_COLOR": "1",
    "COLUMNS": "120",
    "UNITY_NON_INTERACTIVE": "1",
    "UNITY_NO_BANNER": "1",
}
PLATFORM_NAMES = {"Darwin": "macos", "Linux": "linux", "Windows": "windows"}


class CollectionError(RuntimeError):
    """Raised when help collection cannot produce a complete snapshot."""


def normalize_text(value: str) -> str:
    """Remove terminal control sequences and normalize line endings."""
    return ANSI_RE.sub("", value.replace("\r\n", "\n").replace("\r", "\n"))


def validate_token(token: str) -> str:
    """Reject tokens that could escape an argv-only command invocation."""
    if not TOKEN_RE.fullmatch(token) or ".." in token:
        raise CollectionError(f"unsafe command token: {token!r}")
    return token


def normalized_hash(stdout: str, stderr: str) -> str:
    content = f"stdout\0{stdout}\0stderr\0{stderr}".encode()
    return hashlib.sha256(content).hexdigest()


def collection_environment() -> dict[str, str]:
    env = os.environ.copy()
    env.update(DEFAULT_ENV)
    for candidate in ("C.UTF-8", "en_US.UTF-8"):
        try:
            locale.setlocale(locale.LC_ALL, candidate)
        except locale.Error:
            continue
        env["LC_ALL"] = candidate
        env["LANG"] = candidate
        break
    return env


def run_invocation(
    executable: str,
    command_path: Sequence[str],
    *,
    timeout: float,
    platform_name: str,
    architecture: str,
    cli_version: str,
) -> dict[str, Any]:
    path = [validate_token(token) for token in command_path]
    argv = [executable, *path, "--help"] if path else [executable, "--help"]
    try:
        result = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=collection_environment(),
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CollectionError(f"help timed out for {' '.join(argv)}") from exc
    stdout = normalize_text(result.stdout)
    stderr = normalize_text(result.stderr)
    return {
        "command_path": path,
        "argv": ["unity", *path, "--help"],
        "exit_code": result.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "platform": platform_name,
        "architecture": architecture,
        "cli_version": cli_version,
        "normalized_sha256": normalized_hash(stdout, stderr),
    }


def get_version(executable: str, timeout: float) -> str:
    try:
        result = subprocess.run(
            [executable, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=collection_environment(),
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CollectionError("unity --version timed out") from exc
    version = normalize_text(result.stdout).strip()
    if result.returncode != 0 or not version or "\n" in version:
        raise CollectionError("unity --version did not return a usable version")
    return version


def collect(
    executable: str = "unity",
    *,
    timeout: float = 30,
    platform_name: str | None = None,
    architecture: str | None = None,
    progress: bool = False,
) -> dict[str, Any]:
    """Collect all reachable help paths, failing on duplicates or failed help."""
    from scripts.parse_help import parse_help_text

    current_platform = platform_name or PLATFORM_NAMES.get(host_platform.system())
    if current_platform not in {"linux", "macos", "windows"}:
        raise CollectionError(f"unsupported platform: {current_platform!r}")
    current_arch = architecture or host_platform.machine().lower()
    version = get_version(executable, timeout)
    queue: deque[tuple[str, ...]] = deque([()])
    seen: set[tuple[str, ...]] = set()
    invocations: list[dict[str, Any]] = []

    while queue:
        path = queue.popleft()
        if path in seen:
            continue
        seen.add(path)
        invocation = run_invocation(
            executable,
            path,
            timeout=timeout,
            platform_name=current_platform,
            architecture=current_arch,
            cli_version=version,
        )
        if progress:
            print(f"collected {' '.join(invocation['argv'])}", file=sys.stderr, flush=True)
        if invocation["exit_code"] != 0:
            raise CollectionError(f"help failed for {' '.join(invocation['argv'])}")
        parsed = parse_help_text(list(path), invocation["stdout"])
        invocations.append(invocation)
        if path and path[-1] == "help":
            continue
        aliases: set[str] = set()
        for child in parsed["subcommands"]:
            name = validate_token(child["name"])
            # Commander exposes a synthetic `help` child at every nesting level.
            if path and name == "help":
                continue
            child_aliases = [validate_token(alias) for alias in child["aliases"]]
            if name in aliases or any(alias in aliases for alias in child_aliases):
                raise CollectionError(
                    f"duplicate command or alias below {' '.join(path) or 'unity'}"
                )
            aliases.update([name, *child_aliases])
            child_path = (*path, name)
            if child_path == path:
                raise CollectionError(f"command discovery loop at {' '.join(path)}")
            queue.append(child_path)

    return {
        "schema_version": 1,
        "platform": current_platform,
        "architecture": current_arch,
        "cli_version": version,
        "invocations": sorted(invocations, key=lambda item: item["command_path"]),
    }


def write_json_atomic(data: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unity", default="unity", help="Unity CLI executable")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--platform", choices=("linux", "macos", "windows"))
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args()
    try:
        write_json_atomic(
            collect(
                args.unity,
                timeout=args.timeout,
                platform_name=args.platform,
                progress=args.progress,
            ),
            args.output,
        )
    except CollectionError as exc:
        print(f"collection failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
