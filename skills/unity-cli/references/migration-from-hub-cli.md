# Migration from the Unity Hub CLI

The standalone CLI is not a drop-in wrapper around the deprecated Hub CLI. Migrate one command at a time against installed help.

## Invocation

| Hub CLI | Standalone Unity CLI |
| --- | --- |
| `"Unity Hub" -- --headless <command>` | `unity <command>` |

Remove both the Hub executable wrapper and the `-- --headless` separator. Do not preserve unsupported Hub global flags.

## Verified changes from the official migration guide

- Editor install version changed from a required `--version`/`-v` flag to a positional version in early standalone releases. Check current `unity install --help`.
- Module installation uses the standalone command's current Editor selector and module values; do not translate flags mechanically.
- Registering local Editors moved from an `editors --add` flag to a nested `editors add` command in the documented release.
- Structured output is selected globally where supported; piped defaults and format support vary by release.
- Errors moved from stdout to stderr in the documented standalone behavior.
- Hub flags such as `--headless`, `--errors`, `--silent`, `--logLevel`, and other legacy globals have no guaranteed equivalent.

## Migration checklist

1. Record the old Hub CLI version, operating systems, commands, inputs, outputs, and expected exit codes.
2. Install and pin the standalone CLI.
3. Run `unity --version` and `unity --help` on every target platform.
4. Replace the invocation wrapper.
5. Resolve each command and complete nested path from installed help.
6. Replace version, module, Editor registration, and project selectors.
7. Remove unsupported legacy flags.
8. Select an explicit structured output format.
9. Separate stdout and stderr.
10. Add non-interactive handling only where exposed.
11. Test success, failure, cancellation, ambiguous version, network, and permission cases.
12. Verify state after each mutating command.

Do not migrate license or credential operations by analogy. Review their complete current help and require explicit authorization.
