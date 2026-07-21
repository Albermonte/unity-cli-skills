from __future__ import annotations

from conftest import command

from scripts.semantic_diff import render_markdown, semantic_diff


def tree(commands: list[dict[str, object]]) -> dict[str, object]:
    return {"cli_version": "1", "commands": commands}


def test_added_and_removed_commands() -> None:
    diff = semantic_diff(
        tree([command(["old"], summary="old")]), tree([command(["new"], summary="new")])
    )
    assert [event["kind"] for event in diff["events"]] == ["command_removed", "command_added"]
    assert "Potentially breaking" in render_markdown(diff)


def test_added_and_removed_options() -> None:
    old = command(["editors"], options=[{"names": ["--old"], "value": None, "default": None}])
    new = command(["editors"], options=[{"names": ["--new"], "value": "<value>", "default": None}])
    kinds = {event["kind"] for event in semantic_diff(tree([old]), tree([new]))["events"]}
    assert kinds == {"option_added", "option_removed"}


def test_option_spelling_and_command_rename() -> None:
    old_option = {"names": ["--old"], "value": None, "default": None}
    new_option = {"names": ["--new"], "value": None, "default": None}
    option_diff = semantic_diff(
        tree([command(["editors"], options=[old_option])]),
        tree([command(["editors"], options=[new_option])]),
    )
    assert [event["kind"] for event in option_diff["events"]] == ["option_spelling_changed"]

    rename_diff = semantic_diff(tree([command(["old"])]), tree([command(["new"])]))
    assert rename_diff["events"][0]["kind"] == "command_renamed"


def test_platform_availability_change() -> None:
    old = command(["editors"])
    new = command(["editors"], availability={"linux": True, "macos": False, "windows": True})
    diff = semantic_diff(tree([old]), tree([new]))
    assert diff["events"][0]["kind"] == "platform_availability_changed"


def test_no_change() -> None:
    value = tree([command(["editors"])])
    assert semantic_diff(value, value)["changed"] is False
