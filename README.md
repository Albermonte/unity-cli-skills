# unity-cli Agent Skill

[![skills.sh](https://skills.sh/b/OWNER/REPOSITORY)](https://skills.sh/OWNER/REPOSITORY)

Unofficial Agent Skill for safe use of the experimental Unity CLI. The public skill is `skills/unity-cli`.

## Install

List before installing:

```bash
npx skills add OWNER/REPOSITORY --list
```

Install into the current project:

```bash
npx skills add OWNER/REPOSITORY
```

Select the skill explicitly:

```bash
npx skills add OWNER/REPOSITORY --skill unity-cli
```

Update or remove:

```bash
npx skills update unity-cli
npx skills remove unity-cli
```

Use the skill by asking an installed compatible agent to install, inspect, automate, troubleshoot, or migrate a standalone Unity CLI workflow. The agent will inspect installed help before choosing syntax.

## Structure

```text
skills/
└── unity-cli/
    ├── SKILL.md               skill definition
    ├── references/            curated guidance and generated command files
    ├── data/                  normalized schema, tree, and provenance
    └── snapshots/             raw normalized platform help
scripts/                       deterministic collection and generation pipeline
tests/                         offline fixtures, golden files, and tests
.github/workflows/             CI and scheduled cross-platform updates
```

## Generated references

The collector runs only `unity --version` and argv ending in `--help`, recursively discovers command paths, strips terminal control sequences, and stores stdout and stderr separately. Parsers retain unknown sections. Platform trees merge into `skills/unity-cli/data/command-tree.json`; generation creates the index and one file per top-level command.

Curated conceptual files are reviewed by humans. Scheduled updates modify only snapshots, normalized data, manifests, and generated command references. No AI model, inference API, local model, embedding service, or generative summarizer is used. The updater does not scrape Unity documentation, so prose-only website changes require manual review.

The current baseline was collected live from Unity CLI `1.0.0-beta.2` on macOS arm64. Linux and Windows availability is intentionally not inferred.

## Development

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/), Node.js 22.20+, and `npx`.

```bash
make install
make check
```

Equivalent direct commands:

```bash
uv sync --frozen
uv run ruff format --check .
uv run ruff check .
uv run mypy scripts tests
uv run pytest
uv run python -m scripts.validate_generated
uv run skills-ref validate skills/unity-cli
npx skills add . --list
```

Pipeline stages:

```bash
make collect
make parse
make merge
make generate
make diff
make validate
```

`make update` collects the local platform and performs an explicitly partial local regeneration. A publishable cross-platform update requires Linux, macOS, and Windows artifacts and runs without `--allow-partial`:

```bash
uv run python -m scripts.update_skill \
  --snapshot linux=skills/unity-cli/snapshots/linux/help.json \
  --snapshot macos=skills/unity-cli/snapshots/macos/help.json \
  --snapshot windows=skills/unity-cli/snapshots/windows/help.json
```

## Review an update pull request

1. Confirm all three platform jobs and validators passed.
2. Review `semantic-diff.md`, potentially breaking changes first.
3. Inspect changed raw help and source hashes for unexpected collapse or secrets.
4. Confirm only generated artifacts changed unless curated guidance was intentionally edited.
5. Run `make check` and repeat generation to prove idempotence.
6. Verify root discovery and a temporary local installation.
7. Review official release notes for prose-only or safety changes.

The scheduled workflow never auto-merges.

## Status and license

This project is unofficial. Unity names and trademarks belong to their owners; Unity does not endorse this project. Original code and authored guidance are MIT-licensed. Official Unity documentation remains subject to Unity's terms and is not reproduced in bulk.
