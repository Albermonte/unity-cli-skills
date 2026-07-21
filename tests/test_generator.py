from __future__ import annotations

from pathlib import Path

from conftest import command

from scripts.generate_references import generate, generated_files


def sample_tree() -> dict[str, object]:
    return {
        "schema_version": 1,
        "cli_version": "1.0.0-test",
        "platforms": ["linux", "macos", "windows"],
        "commands": [command(["editors"], aliases=["e"], summary="Manage editors")],
    }


def test_index_matches_golden() -> None:
    expected = (Path(__file__).parent / "golden" / "command-index.md").read_text()
    assert generated_files(sample_tree())["command-index.md"] == expected


def test_generation_is_idempotent_and_removes_stale(tmp_path: Path) -> None:
    stale = tmp_path / "command-old.md"
    stale.write_text("stale")
    generate(sample_tree(), tmp_path)
    first = {path.name: path.read_text() for path in tmp_path.iterdir()}
    generate(sample_tree(), tmp_path)
    second = {path.name: path.read_text() for path in tmp_path.iterdir()}
    assert first == second
    assert not stale.exists()


def test_markdown_escapes_table_pipes() -> None:
    tree = sample_tree()
    tree["commands"][0]["summary"] = "one | two"  # type: ignore[index]
    assert "one \\| two" in generated_files(tree)["command-index.md"]
