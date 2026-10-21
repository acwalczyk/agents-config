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

## Project-scoped installations

The older Claude registrations for `/Users/dwalczyk/Development/HCP/gcp-hcp`
have now been updated explicitly at project scope:

| Plugin | Project before | Project after | User version |
| --- | --- | --- | --- |
| jira@ai-helpers | 0.9.1 | 0.9.6 | 0.9.6 |
| gcp-hcp@gcp-hcp | 0.0.4 | 0.0.6 | 0.0.6 |

Before this update, fresh `claude plugin details` commands from that repository
already resolved Jira 0.9.6 and GCP HCP 0.0.6. The old project records therefore
did not establish that those commands loaded stale content. Project enablement
has precedence over user enablement, but that is distinct from selecting a cached
version; see the [Claude loading reference](https://code.claude.com/docs/en/plugins/loading).

Both native `claude plugin update <id> --scope project --json` operations succeeded.
Only these two selectors changed in the native installation registry. Fingerprints
confirmed that user settings, repository settings, instructions, skills and existing
Git changes were unchanged. A private backup is under
`~/.local/state/agents-config/backups/20261021T213112Z-project-plugins-es94t4gw/`.
The general updater still deliberately operates at user scope; project updates
remain explicit. No project declarations were removed or committed to gcp-hcp.

## Resolved Claude dependency errors

After the project refresh, a fresh `claude plugin list --json` reported these
additional load errors:

- `golang@ai-helpers` required `gopls-lsp@ai-helpers`. The installed
  `gopls-lsp@claude-plugins-official` does not satisfy that qualified dependency.
- `openshift-developer@ai-helpers` reported `ci@ai-helpers` unsatisfied. CI 0.0.80
  was installed but disabled; its cached presence alone did not satisfy loading.

Inspection of the bundle manifest found further dependencies behind the first
reported error. The Claude selection now includes the full declared set:

| Dependency | Installed version | Action |
| --- | --- | --- |
| gopls-lsp@ai-helpers | 1.0.0 | Installed and enabled |
| ci@ai-helpers | 0.0.106 | Updated from 0.0.80 and enabled |
| prodsec-skills@ai-helpers | 1.0.0 | Installed and enabled |
| git@ai-helpers | 0.0.7 | Installed and enabled |
| code-review@ai-helpers | 0.0.18 | Installed and enabled |

Jira and Go already satisfied the bundle's other dependencies. Codex's selection
was unchanged. The [Claude dependency reference](https://code.claude.com/docs/en/plugins/dependencies)
explains that unqualified dependencies resolve within their declaring marketplace.

An isolated native installation exposed an upstream catalog limitation: the
team's `gopls-lsp` entry references Anthropic's repository but does not carry the
official marketplace's inline `lspServers` definition. `plugin details` reports
zero LSP servers for that entry. Keep `gopls-lsp@claude-plugins-official` enabled
alongside it: the team entry satisfies the dependency identity, while the official
entry still exposes one `gopls` language server. No cached plugin files were patched.
The upstream entries can be inspected in the
[team catalog](https://github.com/openshift-eng/ai-helpers/blob/main/.claude-plugin/marketplace.json)
and [official catalog](https://github.com/anthropics/claude-plugins-official/blob/main/.claude-plugin/marketplace.json).

Fresh native lists from agents-config and gcp-hcp report no load errors. Component
inventories resolve Go's skills/MCP/hook, the OpenShift skills/hook, the official
Go LSP, and 130 Product Security skills. This checks metadata and dependency
resolution, not live MCP/LSP startup or the behavior of each skill.

The existing OpenShift SessionStart hook becomes usable with the repaired bundle:
in repositories with `.pre-commit-config.yaml`, it validates that configuration
and installs pre-commit/pre-push Git hooks. No interactive agent session or that
hook was started during this repair.

Native installation backup:
`~/.local/state/agents-config/backups/20261021T213812Z-dependencies-_9scihi8/`.
Chezmoi plugin-enablement backup:
`~/.local/state/agents-config/backups/20261021T213854Z-bj2_mnfh/`.
Fingerprints confirm non-plugin Claude settings, Codex configuration/authentication,
T3 settings, shell files, global instructions, project skills/settings/instructions
and existing project Git changes were preserved.

## Native checks for future updates

An enabled flag and successful update are insufficient to establish that a plugin
resolves correctly. The Claude path in `scripts/update.sh` now checks `plugin list --json` after
successful installation commands and fails if any selected plugin is missing,
disabled, reports load errors, or the check cannot run. Unselected plugin failures
are outside this selected-configuration check.

Run the same check explicitly in a project:

```sh
./scripts/doctor.sh --check-claude-plugins --record --project /path/to/repo
```

Without the explicit check flag, doctor remains an inventory of settings, cache
and registrations. The native check captures command output and reports only
selected IDs and status, suppressing raw native errors. It makes no inference
or MCP requests. Recording adds the check result to the version observations;
an unsuccessful or unavailable native check exits nonzero.

## Reload and verify

Start new Claude/Codex sessions after the refresh. Existing conversation context
can still contain previously advertised skills. No agent session was restarted
as part of this update, and no Jira API requests were needed for validation.
The full T3 conversation test remains pending separately.

See the [official Codex plugin guide](https://learn.chatgpt.com/docs/plugins) and
[native CLI reference](https://learn.chatgpt.com/docs/cli/reference) for reload and
marketplace command behavior.
