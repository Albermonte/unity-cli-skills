# Troubleshooting

## Minimum safe diagnostic set

Capture and redact:

- OS and architecture.
- `command -v unity` or `Get-Command unity`.
- `unity --version`.
- `unity --help`.
- Complete relevant nested `--help`.
- Exact argv, working-directory role, exit code, stdout, and stderr.
- Relevant read-only diagnostic output exposed by installed help.

Never include credentials, serials, bearer tokens, offline license material, proxy passwords, usernames, or full home/project paths.

## Common failures

### `unity` not found or wrong executable

Reload the terminal, source the installer-created environment file, inspect PATH order, and resolve the executable. A newly installed binary can exist at the installer path while the current shell still lacks it.

### Unsupported OS or architecture

Compare the host against the current installer. Do not force a binary for another platform. Confirm whether translation/emulation is supported before use.

### Installation or upgrade failure

Review the installer before execution. Check download integrity, filesystem space, write permissions, proxy/TLS behavior, antivirus controls, and partial state. Do not clear caches or reinstall until current help documents the recovery effect and the user authorizes it.

### Authentication or credential-store failure

Use status inspection first. Check headless keyring access, service-account variable pairing, clock, browser callback reachability, and stale Hub-shared sessions. Redact all credential material.

### Network or proxy failure

Check the installed global help and proxy configuration help. Verify DNS, TLS, authenticated proxy behavior, PAC/SOCKS support, and precedence. Diagnostic proxy logging can expose URLs or credentials; enable it only for a scoped reproduction and sanitize the result.

### Permission failure

Inspect the CLI home, Editor install path, cache, project, and credential-store permissions. Do not default to elevated execution; fix ownership or choose an authorized location.

### Non-interactive failure

Specify every required value, use the installed non-interactive option, and handle EULAs or confirmations only with documented flags. An omitted version or module may trigger a prompt interactively and fail in CI.

### Ambiguous Editor alias or project version

Use read-only Editor/release/project inspection. Replace aliases with an exact version where reproducibility matters. Confirm project metadata and installed modules before open, build, test, run, or upgrade.

### Unsupported module

List modules for the exact Editor version and architecture. A module available for one Editor or platform may be absent elsewhere.

### Exit-code diagnosis

Treat nonzero as failure. Parse stderr separately. Consult the exact nested help because newer versions use more specific codes than the early `0`/`1`/`130` contract.

### Help parser mismatch

Stop generation. Preserve the raw normalized snapshot, retain unknown sections, add a minimal fixture and parser test, then regenerate. Never discard unrecognized help or publish partial platform data.
