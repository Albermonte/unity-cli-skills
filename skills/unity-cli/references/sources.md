# Sources and provenance

This project is unofficial and is not endorsed by Unity Technologies.

## Initial curated sources

- [Agent Skills specification](https://agentskills.io/specification)
- [Agent Skills documentation index](https://agentskills.io/llms.txt)
- [Skills CLI repository](https://github.com/vercel-labs/skills)
- [Unity CLI overview](https://docs.unity.com/en-us/unity-cli)
- [Unity CLI introduction](https://docs.unity.com/en-us/unity-cli/unity-cli)
- [Unity CLI usage guide](https://docs.unity.com/en-us/unity-cli/use-unity-cli)
- [Unity CLI reference](https://docs.unity.com/en-us/unity-cli/unity-cli-reference)
- [Unity CLI release notes](https://docs.unity.com/en-us/unity-cli/release-notes)

Official pages informed the initial human-authored guidance. Large portions are not copied. Unity documentation remains subject to Unity's terms.

## Generated sources

Generated command references derive only from normalized output of:

```text
unity --version
unity --help
unity <command> --help
unity <command> <subcommand> --help
```

Collection recurses to deeper paths when help exposes them. The collector invokes no operational command. `data/source-manifest.json` records the committed snapshot hashes.

The initial committed baseline was collected live from macOS arm64. Linux and Windows remain unavailable until a successful cross-platform scheduled collection. Website prose-only changes are not detected automatically because the updater does not scrape `docs.unity.com`.
