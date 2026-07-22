---
name: unity-cli
description: Use when installing, configuring, automating, troubleshooting, or migrating workflows involving the standalone Unity CLI, including Unity Editor installations, modules, projects, authentication, licensing, structured output, and CI.
---

# Unity CLI

## Purpose

Operate the standalone `unity` CLI safely. Treat the installed CLI's help as authoritative because the CLI is experimental and command surfaces can change between releases.

## Identify the correct CLI

Confirm the executable is the standalone Unity CLI before acting:

```bash
command -v unity
unity --version
unity --help
```

Do not confuse it with:

- Unity Editor command-line arguments passed to an Editor executable.
- The deprecated Unity Hub CLI and its `-- --headless` wrapper.
- Unity Gaming Services CLI (`ugs`).
- Unity Version Control (`cm`).
- Package Manager commands.
- A third-party executable or plugin named `unity`.

Read [references/overview.md](references/overview.md) when identity or scope is unclear.

## Required preflight checks

Before selecting or running a command:

1. Determine the operating system and architecture.
2. Run `unity --version`.
3. Run `unity --help`.
4. Run `unity <relevant-command> --help`.
5. For nested commands, run the complete path, such as `unity projects clone --help`.
6. Prefer installed help over remembered syntax, generated references, or website examples.
7. Determine whether the operation is read-only or state-changing.
8. Verify platform-specific availability and experimental notices.
9. Never assume experimental syntax is stable across versions.

Use [references/command-index.md](references/command-index.md) only to locate the versioned generated reference, then confirm locally with `--help`.

## Command selection workflow

1. Start with the narrowest read-only inspection command exposed by help.
2. Resolve aliases, version selectors, paths, architectures, modules, and required values from the installed help.
3. Prefer preview or dry-run options only when that exact command's help exposes them.
4. Build argv as separate arguments in automation; do not interpolate discovered values into shell code.
5. Explain the target and effect before a state-changing command.
6. Execute only after required user authorization.
7. Check the process exit code and verify the resulting state with a read-only command.

## Automation and structured output

- Use an explicitly supported structured format for automation. Confirm formats with installed help.
- Keep stdout and stderr separate. Parse stdout as data; retain stderr for diagnostics.
- Check the process exit code even when structured output is present.
- Do not parse animated progress output.
- Avoid interactive prompts in CI. Use non-interactive and confirmation options only when help exposes them.
- Pin the CLI and Editor versions when reproducibility matters.
- Never log credentials, bearer tokens, serials, offline license material, or service-account secrets.

Read [references/output-and-automation.md](references/output-and-automation.md) for stream, format, environment, cancellation, and CI guidance.

## Platform-specific handling

Determine OS and architecture before installation, Editor architecture selection, path changes, or module work. Do not transplant flags between platforms unless each target platform's help exposes them. Read [references/installation-and-upgrade.md](references/installation-and-upgrade.md).

## State-changing operations

Treat these as state-changing or destructive and explain them before execution:

- Installing, upgrading, or uninstalling the CLI or an Editor.
- Adding or removing Editor modules.
- Registering Editors or changing defaults and global install paths.
- Creating, importing, cloning, linking, unlinking, deleting, or upgrading projects.
- Removing credentials or changing authentication state.
- Activating, returning, or modifying licenses.
- Clearing caches.
- Changing proxy, language, analytics, or persistent configuration.

Never activate or return a license, remove credentials, delete or upgrade a project, clear a cache, uninstall software, or change a global path without explicit authorization. Inspect exact behavior with the complete command path and `--help` first.

Read [references/authentication-and-licensing.md](references/authentication-and-licensing.md) before auth or license work. Read [references/migration-from-hub-cli.md](references/migration-from-hub-cli.md) before changing Hub CLI scripts.

## Troubleshooting workflow

1. Capture OS, architecture, `command -v unity` or platform equivalent, `unity --version`, exact argv, exit code, stdout, and stderr.
2. Re-run the complete command path with `--help`.
3. Use read-only diagnostic commands exposed by installed help.
4. Check PATH, permissions, proxy/network access, credential-store access, non-interactive settings, Editor/version/module resolution, and platform support.
5. Redact secrets and user-specific paths before sharing diagnostics.
6. Stop if help parsing is incomplete, output is structurally unexpected, or the command may mutate state unexpectedly.

Read [references/troubleshooting.md](references/troubleshooting.md) for targeted checks.

## Reference map

- Concepts and boundaries: [references/overview.md](references/overview.md)
- Installation and upgrades: [references/installation-and-upgrade.md](references/installation-and-upgrade.md)
- Automation and output: [references/output-and-automation.md](references/output-and-automation.md)
- Authentication and licensing: [references/authentication-and-licensing.md](references/authentication-and-licensing.md)
- Hub CLI migration: [references/migration-from-hub-cli.md](references/migration-from-hub-cli.md)
- Troubleshooting: [references/troubleshooting.md](references/troubleshooting.md)
- Generated commands: [references/command-index.md](references/command-index.md)
- Provenance: [references/sources.md](references/sources.md)
