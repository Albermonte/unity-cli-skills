#!/usr/bin/env python3
"""Parse normalized Unity CLI help snapshots into platform command trees."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SECTION_ALIASES = {
    "usage": "usage",
    "usages": "usage",
    "arguments": "arguments",
    "positionals": "arguments",
    "positional arguments": "arguments",
    "options": "options",
    "global options": "options",
    "commands": "subcommands",
    "subcommands": "subcommands",
    "examples": "examples",
    "environment": "environment_variables",
    "environment variables": "environment_variables",
    "exit codes": "exit_codes",
}
HEADING_RE = re.compile(r"^([A-Za-z][A-Za-z0-9 /_-]*):\s*$")
ENTRY_RE = re.compile(r"^\s{2,}(\S.*?)\s{2,}(\S.*)$")
DEFAULT_RE = re.compile(r"\[default:\s*([^\]]+)\]", re.IGNORECASE)
CHOICES_RE = re.compile(r"\[possible values:\s*([^\]]+)\]", re.IGNORECASE)
ENV_RE = re.compile(r"(?:env:|environment variable:?)[ ]*([A-Z][A-Z0-9_]+)", re.IGNORECASE)


class ParseError(RuntimeError):
    """Raised when a snapshot is structurally unsafe to parse."""


def _entries(lines: Iterable[str]) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line in lines:
        match = ENTRY_RE.match(line)
        if match:
            entries.append((match.group(1).strip(), match.group(2).strip()))
        elif line.strip() and entries:
            name, description = entries[-1]
            entries[-1] = (name, f"{description} {line.strip()}")
    return entries


def _parse_names(spec: str) -> tuple[list[str], str | None]:
    value_match = re.search(r"(?:=|\s)(<[^>]+>|\[[^]]+\]|[A-Z][A-Z0-9_-]*)$", spec)
    value = value_match.group(1) if value_match else None
    names_part = spec[: value_match.start()].strip() if value_match else spec
    names = [part.strip() for part in names_part.split(",") if part.strip().startswith("-")]
    return names, value


def _parse_options(lines: list[str]) -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    for spec, description in _entries(lines):
        names, value = _parse_names(spec)
        if not names:
            continue
        default_match = DEFAULT_RE.search(description)
        choices_match = CHOICES_RE.search(description)
        options.append(
            {
                "names": names,
                "value": value,
                "description": description,
                "required": "required" in description.lower(),
                "repeatable": "repeat" in description.lower() or "multiple" in description.lower(),
                "default": default_match.group(1) if default_match else None,
                "choices": (
                    [item.strip() for item in choices_match.group(1).split(",")]
                    if choices_match
                    else []
                ),
            }
        )
    return options


def _parse_arguments(lines: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "name": spec,
            "description": description,
            "required": not spec.startswith("[") and "optional" not in description.lower(),
            "repeatable": "..." in spec or "multiple" in description.lower(),
        }
        for spec, description in _entries(lines)
    ]


def _parse_subcommands(lines: list[str]) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    seen: set[str] = set()
    for spec, description in _entries(lines):
        first_token = spec.split()[0]
        pipe_names = [item for item in first_token.split("|") if item]
        name = pipe_names[0]
        aliases = pipe_names[1:]
        alias_match = re.search(r"\(alias(?:es)?:\s*([^)]+)\)", spec)
        if alias_match:
            aliases.extend(item.strip() for item in alias_match.group(1).split(","))
        existing = next((command for command in commands if command["name"] == name), None)
        if existing is not None:
            new_aliases = [alias for alias in aliases if alias not in existing["aliases"]]
            if any(alias in seen for alias in new_aliases):
                raise ParseError(f"duplicate alias: {name}")
            existing["aliases"].extend(new_aliases)
            if len(description) > len(existing["summary"]):
                existing["summary"] = description
            seen.update(new_aliases)
            continue
        if name in seen or any(alias in seen for alias in aliases):
            raise ParseError(f"duplicate subcommand or alias: {name}")
        seen.update([name, *aliases])
        commands.append({"name": name, "aliases": aliases, "summary": description})
    return commands


def parse_help_text(command_path: list[str], text: str) -> dict[str, Any]:
    if "\x1b" in text:
        from scripts.collect_help import normalize_text

        text = normalize_text(text)
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    sections: dict[str, list[str]] = {}
    extra_sections: list[dict[str, Any]] = []
    preamble: list[str] = []
    current: str | None = None
    unknown_name: str | None = None
    unknown_lines: list[str] = []

    def flush_unknown() -> None:
        nonlocal unknown_name, unknown_lines
        if unknown_name is not None:
            extra_sections.append({"heading": unknown_name, "lines": unknown_lines})
        unknown_name = None
        unknown_lines = []

    for line in lines:
        if current == "usage" and not line.strip():
            current = None
            continue
        if line.strip().lower().startswith("usage:") and line.strip()[6:].strip():
            flush_unknown()
            current = "usage"
            sections.setdefault(current, []).append(line.strip()[6:].strip())
            continue
        heading = HEADING_RE.match(line.strip())
        if heading:
            flush_unknown()
            label = heading.group(1)
            current = SECTION_ALIASES.get(label.lower())
            if current is None:
                unknown_name = label
            else:
                sections.setdefault(current, [])
            continue
        if unknown_name is not None:
            unknown_lines.append(line)
        elif current is None:
            preamble.append(line)
        else:
            sections[current].append(line)
    flush_unknown()

    prose = [line.strip() for line in preamble if line.strip()]
    summary = prose[0] if prose else ""
    description = "\n".join(prose[1:])
    usage = [line.strip() for line in sections.get("usage", []) if line.strip()]
    examples = [line.strip() for line in sections.get("examples", []) if line.strip()]
    environment_variables = [
        {"name": name.split()[0], "description": description}
        for name, description in _entries(sections.get("environment_variables", []))
    ]
    for option in _parse_options(sections.get("options", [])):
        for variable in ENV_RE.findall(option["description"]):
            if not any(item["name"] == variable for item in environment_variables):
                environment_variables.append(
                    {"name": variable, "description": f"Mirrors {', '.join(option['names'])}."}
                )
    exit_codes = [
        {"code": name, "description": description}
        for name, description in _entries(sections.get("exit_codes", []))
    ]
    content = "\n".join(lines).lower()
    return {
        "path": command_path,
        "name": command_path[-1] if command_path else "unity",
        "aliases": [],
        "summary": summary,
        "description": description,
        "usage": usage,
        "arguments": _parse_arguments(sections.get("arguments", [])),
        "options": _parse_options(sections.get("options", [])),
        "subcommands": _parse_subcommands(sections.get("subcommands", [])),
        "examples": examples,
        "environment_variables": environment_variables,
        "exit_codes": exit_codes,
        "deprecation_notices": [line for line in prose if "deprecated" in line.lower()],
        "experimental_notices": [line for line in prose if "experimental" in line.lower()],
        "platform_restrictions": [
            line
            for line in prose
            if any(word in line.lower() for word in ("windows only", "macos only", "linux only"))
        ],
        "extra_sections": extra_sections,
        "has_unknown_sections": bool(extra_sections),
        "raw_mentions_experimental": "experimental" in content,
    }


def parse_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    required = {"platform", "architecture", "cli_version", "invocations"}
    if missing := required - snapshot.keys():
        raise ParseError(f"snapshot missing fields: {', '.join(sorted(missing))}")
    commands: list[dict[str, Any]] = []
    paths: set[tuple[str, ...]] = set()
    for invocation in snapshot["invocations"]:
        if invocation["exit_code"] != 0:
            raise ParseError(f"nonzero help result for {invocation['command_path']}")
        path = tuple(invocation["command_path"])
        if path in paths:
            raise ParseError(f"duplicate help result for {path}")
        paths.add(path)
        command = parse_help_text(list(path), invocation["stdout"])
        command["source_hash"] = invocation["normalized_sha256"]
        commands.append(command)
    command_map = {tuple(command["path"]): command for command in commands}
    for parent in commands:
        for child in parent["subcommands"]:
            target = command_map.get((*tuple(parent["path"]), child["name"]))
            if target is not None:
                target["aliases"] = child["aliases"]
                if not target["summary"]:
                    target["summary"] = child["summary"]
    expected = {
        (*tuple(command["path"]), child["name"])
        for command in commands
        for child in command["subcommands"]
        if not command["path"] or child["name"] != "help"
        if not command["path"] or command["path"][-1] != "help"
    }
    if missing_paths := expected - paths:
        rendered = ", ".join(" ".join(path) for path in sorted(missing_paths))
        raise ParseError(f"incomplete recursive collection: {rendered}")
    return {
        "schema_version": 1,
        "cli_version": snapshot["cli_version"],
        "platform": snapshot["platform"],
        "architecture": snapshot["architecture"],
        "commands": sorted(commands, key=lambda command: command["path"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        tree = parse_snapshot(json.loads(args.snapshot.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ParseError) as exc:
        print(f"parse failed: {exc}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(tree, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
