# Installation and upgrade

The Unity CLI is experimental. Review the remote installer before execution, then use the current command from the official [Unity CLI usage guide](https://docs.unity.com/en-us/unity-cli/use-unity-cli).

## Supported installer targets

The current official installers detect:

- macOS: x64 and arm64.
- Linux: x64 and arm64.
- Windows 64-bit: x64 and arm64.

Confirm current support in the installer and release notes before deployment.

## macOS and Linux

Inspect first:

```bash
curl -fsSL https://public-cdn.cloud.unity3d.com/hub/prod/cli/install.sh -o unity-cli-install.sh
less unity-cli-install.sh
```

The current official beta-channel command is:

```bash
curl -fsSL https://public-cdn.cloud.unity3d.com/hub/prod/cli/install.sh | UNITY_CLI_CHANNEL=beta bash
```

The installer uses `UNITY_CLI_HOME` when set and otherwise installs under the user's `.unity` directory. It writes environment files and may update shell startup configuration. Review those changes before unattended use.

## Windows PowerShell

Inspect first:

```powershell
Invoke-RestMethod https://public-cdn.cloud.unity3d.com/hub/prod/cli/install.ps1 -OutFile unity-cli-install.ps1
Get-Content .\unity-cli-install.ps1
```

The current official beta-channel command is:

```powershell
$env:UNITY_CLI_CHANNEL='beta'; irm https://public-cdn.cloud.unity3d.com/hub/prod/cli/install.ps1 | iex
```

## PATH and verification

Reload the terminal after installation. If needed, source the installer-created environment file or add the reported binary directory to PATH. Verify identity and version:

```bash
command -v unity
unity --version
unity --help
```

On Windows, use `Get-Command unity`.

## Channels and pinning

The current Unix installer accepts `alpha`, `beta`, or an empty channel value for stable; the PowerShell installer accepts the channel parameter/environment value. This can change, so inspect the downloaded installer. Pin or archive a reviewed installer and verify the resulting `unity --version` for reproducible CI. Do not invent a version flag if the installer does not expose one.

## Upgrade and removal

Run `unity upgrade --help` before self-update. Verify `unity --version` afterward. Upgrade may replace the current binary; rollback support is version-dependent.

CLI removal is destructive: it can remove the binary, environment files, and stored credentials. Run the installed removal command's complete `--help`, explain the scope, and require explicit authorization.

## CI installation

- Download and inspect or checksum-pin the installer rather than blindly executing mutable remote content.
- Select the required channel explicitly.
- keep installation non-interactive only with flags/environment variables exposed by current help.
- Verify version and top-level help before subsequent steps.
- Cache downloads only when cache integrity and invalidation are understood.
