# Output and automation

Confirm all formats and global options with `unity --help`. The live macOS `1.0.0-beta.2` snapshot exposes `human`, `json`, `tsv`, and `ndjson`, plus `--no-banner`, `--non-interactive`, `--quiet`, and related environment variables. Earlier releases differ.

## Format selection

- `human`: terminal-oriented text; may contain color, symbols, tables, or animated progress.
- `json`: structured completed results and errors where supported.
- `tsv`: record-oriented output suitable for simple pipelines.
- `ndjson`: streaming records, especially useful for long-running progress where supported.

Select a format explicitly in automation. Never assume every command supports every format merely because the global help lists it.

## Global automation settings

The collected version exposes:

| Option | Environment variable | Purpose |
| --- | --- | --- |
| `--format <format>` | `UNITY_FORMAT` | Select output format. |
| `--no-banner` | `UNITY_NO_BANNER` | Suppress the banner. |
| `--non-interactive` | `UNITY_NON_INTERACTIVE` | Disable prompts. |
| `--quiet` | `UNITY_QUIET` | Suppress informational output. |
| `--verbose` | `UNITY_VERBOSE` | Include detailed failure diagnostics. |

Use values accepted by installed help. Confirmation flags such as `--yes` are command-specific.

## Streams and exit codes

Keep stdout and stderr separate. Parse stdout only as the selected data format. Record sanitized stderr for diagnostics. Never infer success from output alone; check the process exit code.

Official documentation for earlier releases documents `0` for success, `1` for general error, and `130` for user cancellation, with newer releases adding more specific codes. The complete installed command help and actual exit code are authoritative.

## Progress and cancellation

Do not parse human progress bars. Prefer supported NDJSON or JSON output. Treat signals and cancellation as failure unless the workflow explicitly handles the documented cancellation code. Preserve partial-download or resume state only when current help documents it.

## Stable CI practice

1. Pin the CLI and Editor versions.
2. Run `unity --version`, `unity --help`, and relevant nested help.
3. Set non-interactive behavior and explicit structured output.
4. Pass argv as an array.
5. Capture stdout and stderr separately.
6. Apply timeouts appropriate to downloads and Editor work.
7. Check exit codes.
8. Validate the structured output schema before consuming it.
9. Redact secrets and user-specific paths.
10. Verify resulting state with a read-only command.
