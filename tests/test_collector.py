from __future__ import annotations

import subprocess
from typing import Any

import pytest

from scripts import collect_help


def test_normalizes_ansi_and_crlf() -> None:
    assert collect_help.normalize_text("\x1b[31mError\x1b[0m\r\nnext\r") == "Error\nnext\n"


@pytest.mark.parametrize("token", ["has space", "../escape", "a/b", "a\\b", "x;rm", "\x01bad"])
def test_rejects_unsafe_tokens(token: str) -> None:
    with pytest.raises(collect_help.CollectionError):
        collect_help.validate_token(token)


def test_invocation_uses_argv_and_separate_streams(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured.update({"argv": argv, **kwargs})
        return subprocess.CompletedProcess(argv, 0, "ok\r\n", "warning\r\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = collect_help.run_invocation(
        "unity",
        ["editors", "list"],
        timeout=3,
        platform_name="linux",
        architecture="x86_64",
        cli_version="1",
    )
    assert captured["argv"] == ["unity", "editors", "list", "--help"]
    assert captured["shell"] is False
    assert result["stdout"] == "ok\n"
    assert result["stderr"] == "warning\n"


def test_invocation_decodes_utf8_independent_of_windows_code_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_stdout = "Emoji reaction, e.g. 👍\n".encode()

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        encoding = kwargs.get("encoding", "cp1252")
        stdout = raw_stdout.decode(encoding)
        return subprocess.CompletedProcess(argv, 0, stdout, "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = collect_help.run_invocation(
        "unity",
        ["collaboration", "reactions", "add"],
        timeout=3,
        platform_name="windows",
        architecture="x86_64",
        cli_version="1.0.0-beta.6",
    )

    assert result["stdout"] == "Emoji reaction, e.g. 👍\n"


def test_timeout_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*args: Any, **kwargs: Any) -> Any:
        raise subprocess.TimeoutExpired(["unity", "--help"], 1)

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(collect_help.CollectionError, match="timed out"):
        collect_help.run_invocation(
            "unity", [], timeout=1, platform_name="linux", architecture="x86_64", cli_version="1"
        )


def test_nonzero_version_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess([], 1, "", "failure"),
    )
    with pytest.raises(collect_help.CollectionError):
        collect_help.get_version("unity", 1)
