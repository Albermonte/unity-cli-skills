# Authentication and licensing

Authentication and licensing handle sensitive credentials and seats. Inspect the installed nested help before any action.

## Authentication

`unity auth login` can use an interactive browser flow. Current releases may also support service accounts for unattended workflows. The release that introduced service-account support documents `UNITY_SERVICE_ACCOUNT_ID` and `UNITY_SERVICE_ACCOUNT_SECRET`; verify them with installed help before use.

The CLI stores sessions in the operating-system credential store and may share authentication with Unity Hub. Credential-store access can fail in headless sessions even when environment variables are correct.

Safe pattern:

1. Run `unity auth --help` and the chosen nested command's help.
2. Prefer `unity auth status` for read-only inspection.
3. Inject CI secrets through the platform secret store.
4. Never echo, commit, persist in command history, or include secrets in diagnostic artifacts.
5. Treat logout or credential clearing as destructive and require authorization.

Do not assume browser login works on a remote worker. Do not claim service-account support unless the installed release exposes it.

## Licensing

The collected `1.0.0-beta.2` command tree exposes license listing, status, activation, return, and floating-server inspection. Exact activation methods and required values are version-dependent.

- Listing and status are read-only but can reveal organization, product, expiration, or machine details.
- Activation changes machine licensing and can consume a seat.
- Return changes licensing and can release a seat.
- Offline request/response files and serials are secrets.

Before activation or return:

1. Run the complete command path with `--help`.
2. Identify the license and organization without exposing secrets.
3. Explain seat and machine impact.
4. Obtain explicit authorization.
5. Use the supported non-interactive mechanism only if help documents it.
6. Verify with read-only status/list output and redact the result.

Never activate or return a license during help collection, diagnostics, tests, or scheduled maintenance.

## Troubleshooting safely

Capture command path, sanitized exit code, and redacted stderr. Confirm keyring availability, sign-in state, clock, proxy, permissions, and organization selection. Replace secret values, serials, bearer tokens, offline files, usernames, and home paths before sharing.
