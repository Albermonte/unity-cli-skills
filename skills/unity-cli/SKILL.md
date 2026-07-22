---
name: unity-cli
description: Use when installing, configuring, automating, troubleshooting, or migrating workflows involving the standalone Unity CLI, including Unity Editor installations, modules, projects, authentication, licensing, structured output, and CI.
---

# Unity CLI

Treat installed help as authoritative. The CLI is experimental. Syntax changes.

## Identify and inspect

```bash
command -v unity
unity --version
unity --help
```

Confirm this is the standalone Unity CLI. Not:

- Unity Editor arguments.
- Deprecated Unity Hub CLI or `-- --headless`.
- Unity Gaming Services CLI (`ugs`).
- Unity Version Control (`cm`).
- Package Manager.
- Third-party `unity` tools.

Before each command:

1. Detect OS and architecture.
2. Check `unity --version` and relevant help.
3. Use the complete nested path: `unity projects clone --help`.
4. Classify the operation: read-only or state-changing.
5. Check platform support and experimental notices.

Use generated references only for discovery. Confirm locally with `--help`.

## Execute

- Start with the narrowest read-only inspection.
- Resolve aliases, versions, paths, architectures, modules, and required values from installed help.
- Use preview or dry-run only when that command exposes it.
- In automation, build separate argv. Never interpolate discovered values into shell code.
- Before mutations: explain target and effect; get required authorization.
- Check exit code. Verify state with a read-only command.

## Automation

- Use only help-confirmed structured formats.
- Separate stdout and stderr. Parse stdout; retain stderr.
- Always check exit code. Never parse animated progress.
- Avoid CI prompts. Use non-interactive flags only when exposed by help.
- Pin CLI and Editor versions when reproducibility matters.
- Never log credentials, tokens, serials, offline licenses, or service-account secrets.
- Never copy flags across platforms without checking each platform's help.

## Mutations

Mutations include:

- Install, upgrade, or uninstall CLI/Editor/modules.
- Register Editors; change defaults or global paths.
- Create, import, clone, link, unlink, delete, or upgrade projects.
- Change credentials, authentication, licenses, caches, proxy, language, analytics, or persistent config.

Require explicit authorization before license activation/return, credential removal, project deletion/upgrade, cache clearing, uninstall, or global-path changes. First inspect the complete command path with `--help`.

## Troubleshoot

1. Capture OS, architecture, executable path, version, exact argv, exit code, stdout, and stderr.
2. Check the complete command path with `--help`.
3. Use help-exposed read-only diagnostics.
4. Check PATH, permissions, network/proxy, credential store, non-interactive settings, Editor/version/module resolution, and platform support.
5. Redact secrets and user paths.
6. Stop on incomplete help, unexpected output shape, or unexpected mutation risk.

## References

- Unclear identity/scope: [overview.md](references/overview.md)
- Install, upgrade, platform handling: [installation-and-upgrade.md](references/installation-and-upgrade.md)
- Automation, streams, formats, CI: [output-and-automation.md](references/output-and-automation.md)
- Before auth/license work: [authentication-and-licensing.md](references/authentication-and-licensing.md)
- Before changing Hub CLI scripts: [migration-from-hub-cli.md](references/migration-from-hub-cli.md)
- Diagnostics: [troubleshooting.md](references/troubleshooting.md)
- Generated command discovery: [command-index.md](references/command-index.md)
- Provenance: [sources.md](references/sources.md)
