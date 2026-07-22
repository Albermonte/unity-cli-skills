# Standalone Unity CLI overview

## What it is

The standalone Unity CLI is a terminal tool distributed independently of the Unity Hub desktop application. It manages Unity Editors, modules, projects, authentication, licensing, automation, and other capabilities exposed by the installed release.

The command surface is experimental. Start every task with `unity --version`, `unity --help`, and the complete relevant command path with `--help`.

## Appropriate uses

- Install and inspect Unity Editor versions and modules.
- Manage registered Editors, projects, templates, and installation paths.
- Authenticate or inspect licensing when supported.
- Produce structured output for scripts and CI.
- Run supported project, build, test, Pipeline, or connected-Editor workflows.
- Diagnose the CLI environment.

Availability varies by version and platform. A generated reference proves only what one collected CLI exposed.

## Tool boundaries

| Tool | Invocation | Purpose |
| --- | --- | --- |
| Standalone Unity CLI | `unity ...` | The subject of this skill. |
| Unity Editor CLI | Editor executable plus Editor arguments | Controls an Editor process directly. |
| Deprecated Hub CLI | Hub executable plus `-- --headless ...` | Legacy Hub-embedded interface. |
| UGS CLI | `ugs ...` | Unity Gaming Services. |
| Unity Version Control | `cm ...` | Version-control operations. |
| Package Manager | Editor/package APIs | Unity packages, not CLI installation management. |

The standalone CLI may expose plugins or connected-Editor commands. Confirm ownership and provenance before running an unfamiliar command.

## Why installed help wins

The installed binary defines available command paths, aliases, values, formats, platform behavior, and experimental changes. Website prose and this repository can lag. Use generated files for discovery, not final syntax selection.

## Curated and generated content

Human-authored files explain safe workflows and stable concepts. `references/command-index.md`, `references/command-*.md`, `data/command-tree.json`, `data/source-manifest.json`, and snapshots are generated from normalized help. Scheduled maintenance rewrites only generated artifacts and never uses AI.

Website prose-only changes are not automatically detected. Review official documentation and release notes manually when maintaining curated guidance.
