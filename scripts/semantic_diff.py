#!/usr/bin/env python3
"""Produce a deterministic semantic diff between Unity CLI command trees."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

BREAKING = {
    "command_removed",
    "command_renamed",
    "alias_removed",
    "option_removed",
    "option_spelling_changed",
    "option_value_changed",
    "subcommand_removed",
    "argument_changed",
    "usage_changed",
    "default_changed",
    "environment_variable_removed",
    "platform_availability_changed",
    "unknown_section_introduced",
}


def _option_map(command: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {name: option for option in command["options"] for name in option["names"]}


def _event(kind: str, path: tuple[str, ...], detail: str) -> dict[str, Any]:
    return {
        "breaking": kind in BREAKING,
        "kind": kind,
        "path": list(path),
        "detail": detail,
    }


def _command_fingerprint(command: dict[str, Any]) -> str:
    fields = (
        "summary",
        "description",
        "arguments",
        "options",
        "subcommands",
        "environment_variables",
        "exit_codes",
        "availability",
    )
    return json.dumps({field: command[field] for field in fields}, sort_keys=True)


def _option_fingerprint(option: dict[str, Any]) -> str:
    return json.dumps(
        {key: value for key, value in option.items() if key != "names"}, sort_keys=True
    )


def semantic_diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    if old["cli_version"] != new["cli_version"]:
        events.append(
            _event("cli_version_changed", (), f"{old['cli_version']} -> {new['cli_version']}")
        )
    old_commands = {tuple(command["path"]): command for command in old["commands"]}
    new_commands = {tuple(command["path"]): command for command in new["commands"]}
    removed_paths = set(old_commands) - set(new_commands)
    added_paths = set(new_commands) - set(old_commands)
    for old_path in sorted(removed_paths):
        candidates = [
            new_path
            for new_path in added_paths
            if _command_fingerprint(old_commands[old_path])
            == _command_fingerprint(new_commands[new_path])
        ]
        if len(candidates) == 1:
            new_path = candidates[0]
            events.append(
                _event(
                    "command_renamed",
                    old_path,
                    f"{' '.join(old_path)} -> {' '.join(new_path)}",
                )
            )
            removed_paths.remove(old_path)
            added_paths.remove(new_path)
    for path in sorted(removed_paths):
        events.append(_event("command_removed", path, "command removed"))
    for path in sorted(added_paths):
        events.append(_event("command_added", path, "command added"))
    for path in sorted(old_commands.keys() & new_commands.keys()):
        before, after = old_commands[path], new_commands[path]
        for alias in sorted(set(after["aliases"]) - set(before["aliases"])):
            events.append(_event("alias_added", path, alias))
        for alias in sorted(set(before["aliases"]) - set(after["aliases"])):
            events.append(_event("alias_removed", path, alias))
        old_options, new_options = _option_map(before), _option_map(after)
        removed_options = set(old_options) - set(new_options)
        added_options = set(new_options) - set(old_options)
        for old_name in sorted(removed_options):
            option_candidates = [
                new_name
                for new_name in added_options
                if _option_fingerprint(old_options[old_name])
                == _option_fingerprint(new_options[new_name])
            ]
            if len(option_candidates) == 1:
                new_option_name = option_candidates[0]
                events.append(
                    _event(
                        "option_spelling_changed",
                        path,
                        f"{old_name} -> {new_option_name}",
                    )
                )
                removed_options.remove(old_name)
                added_options.remove(new_option_name)
        for name in sorted(added_options):
            events.append(_event("option_added", path, name))
        for name in sorted(removed_options):
            events.append(_event("option_removed", path, name))
        for name in sorted(old_options.keys() & new_options.keys()):
            for field, kind in (("value", "option_value_changed"), ("default", "default_changed")):
                if old_options[name].get(field) != new_options[name].get(field):
                    events.append(
                        _event(
                            kind,
                            path,
                            f"{name}: {old_options[name].get(field)} -> "
                            f"{new_options[name].get(field)}",
                        )
                    )
        old_subcommands = {item["name"] for item in before["subcommands"]}
        new_subcommands = {item["name"] for item in after["subcommands"]}
        for name in sorted(new_subcommands - old_subcommands):
            events.append(_event("subcommand_added", path, name))
        for name in sorted(old_subcommands - new_subcommands):
            events.append(_event("subcommand_removed", path, name))
        old_environment = {item["name"] for item in before["environment_variables"]}
        new_environment = {item["name"] for item in after["environment_variables"]}
        for name in sorted(new_environment - old_environment):
            events.append(_event("environment_variable_added", path, name))
        for name in sorted(old_environment - new_environment):
            events.append(_event("environment_variable_removed", path, name))
        comparisons = (
            ("arguments", "argument_changed"),
            ("usage", "usage_changed"),
            ("availability", "platform_availability_changed"),
        )
        for field, kind in comparisons:
            if before[field] != after[field]:
                events.append(_event(kind, path, f"{field} changed"))
        if before["summary"] != after["summary"] or before["description"] != after["description"]:
            events.append(
                _event("description_only_changed", path, "summary or description changed")
            )
        if not before["extra_sections"] and after["extra_sections"]:
            events.append(
                _event("unknown_section_introduced", path, "unrecognized help section added")
            )
    events.sort(key=lambda item: (not item["breaking"], item["kind"], item["path"], item["detail"]))
    return {
        "schema_version": 1,
        "old_cli_version": old["cli_version"],
        "new_cli_version": new["cli_version"],
        "changed": bool(events),
        "events": events,
    }


def render_markdown(diff: dict[str, Any]) -> str:
    lines = [
        "## Unity CLI semantic diff",
        "",
        f"`{diff['old_cli_version']}` → `{diff['new_cli_version']}`",
        "",
    ]
    if not diff["events"]:
        return "\n".join([*lines, "No semantic changes.", ""])
    for breaking in (True, False):
        selected = [event for event in diff["events"] if event["breaking"] is breaking]
        if not selected:
            continue
        lines.extend([f"### {'Potentially breaking' if breaking else 'Other changes'}", ""])
        for event in selected:
            path = " ".join(["unity", *event["path"]])
            lines.append(f"- `{event['kind']}` — `{path}`: {event['detail']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--json-output", type=Path, default=Path("semantic-diff.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("semantic-diff.md"))
    args = parser.parse_args()
    diff = semantic_diff(
        json.loads(args.old.read_text(encoding="utf-8")),
        json.loads(args.new.read_text(encoding="utf-8")),
    )
    args.json_output.write_text(
        json.dumps(diff, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    args.markdown_output.write_text(render_markdown(diff), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
