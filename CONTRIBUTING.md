# Contributing

`skills/unity-cli/SKILL.md` is the only skill definition.

## Generated and curated files

Do not manually edit generated command references, normalized data, source manifests, or snapshots under `skills/unity-cli`. Edit curated references directly, ground factual commands in current official sources and installed help, and avoid copying Unity documentation verbatim.

## Behavior changes

1. Add the smallest real help fixture that demonstrates the behavior.
2. Write or update a failing test first.
3. Change the parser, collector, merger, generator, diff, or validator.
4. If normalized structure changes, version and update `skills/unity-cli/data/command-tree.schema.json` plus validation tests.
5. Regenerate references.
6. Review the deterministic semantic diff.
7. Run `make check`.

Unknown help sections must remain in `extra_sections` or fail parsing. Never weaken a test merely to accept unexplained output.

## Local validation

```bash
make install
make check
npx skills add . --list
```

The list must contain exactly `unity-cli`. Test installation in a temporary project:

```bash
npx skills add . --skill unity-cli --agent codex --yes
```

Verify the installed skill includes `SKILL.md`, `references/`, and `data/`, and that relative links still resolve.

Before publication, use the repository URL with `--list` to test skills.sh-compatible discovery. Do not commit temporary installations, semantic-diff output, credentials, or diagnostic logs.
