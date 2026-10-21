# Plugin selection and refresh — October 21, 2026

Selected Jira source: `jira@ai-helpers`. The older `jira@personal` is explicitly
disabled in Codex, with its version 0.9.1 installation retained for rollback.
Both had the same 13 skill names and 17 command names. The team version adds
risk/spike creation guidance and fixes rich-text status-summary formatting.
No Jira issues, comments or statuses were changed by this setup work.

## Configuration ownership

`plugins/manifest.json` lists enabled plugins and explicit disabled legacy entries.
Chezmoi writes their enablement to native settings. Disabling a legacy plugin
changes its existing entry only; it does not create an unresolved marketplace
entry on a fresh machine. Removing a plugin from a list does not uninstall it.
The native update commands operate only on selected enabled plugins.

Apply only plugin choices, without changing model defaults, permission rules,
MCP registrations or global instruction files:

```sh
./scripts/setup.sh --check --component plugins
./scripts/setup.sh --apply --component plugins
```

The native setting files are serialized again, so JSON/TOML formatting can change.
The previous native files are saved in an external private backup before apply.
Model aliases, provider profiles and authentication remain outside this selection.

## Verified user-level versions

| Plugin | Claude before | Claude after | Codex after |
| --- | --- | --- | --- |
| openshift-developer | 1.1.14 | 1.1.34 | 1.1.34 |
| golang | 0.3.1 | 0.7.0 | 0.7.0 |
| gcp-hcp | 0.0.4 | 0.0.6 | 0.0.6 |
| hcp | 0.0.2 | 0.0.3 | 0.0.3 |
| jira | 0.9.1 | 0.9.6 | 0.9.6 |
| gopls-lsp | 1.0.0 | 1.0.0 | 1.0.0 |

Claude's three marketplace refreshes and six user-level update checks succeeded.
Codex's three Git marketplaces were current; all six native plugin-add operations
succeeded at the versions above. `codex plugin list --json` confirms those plugins
are installed and enabled, and confirms personal Jira is installed but disabled.

Installed/cached versions are observations, not a reproducible binary lock or
proof that a running session has reloaded them. `doctor.sh --record` records both
desired enablement and observed cache/registration evidence in `versions.lock.json`.
The latest inventory also finds Homebrew's chezmoi 2.73.3 on PATH; this update did
not install it. The initial audit's missing-binary finding is historical.

## Retained project-scoped installations

Claude still has older project-scoped installations for
`/Users/dwalczyk/Development/HCP/gcp-hcp`:

| Plugin | Retained project version | Refreshed user version |
| --- | --- | --- |
| jira@ai-helpers | 0.9.1 | 0.9.6 |
| gcp-hcp@gcp-hcp | 0.0.4 | 0.0.6 |

The updater deliberately operates at user scope. These project installations
were preserved rather than silently migrated; verify their effective scope before
assuming a new project session uses the user-level version. `doctor.sh` reports
the older project registrations and their paths.

## Reload and verify

Start new Claude/Codex sessions after the refresh. Existing conversation context
can still contain previously advertised skills. No agent session was restarted
as part of this update, and no Jira API requests were needed for validation.
The full T3 conversation test remains pending separately.

See the [official Codex plugin guide](https://learn.chatgpt.com/docs/plugins) and
[native CLI reference](https://learn.chatgpt.com/docs/cli/reference) for reload and
marketplace command behavior.
