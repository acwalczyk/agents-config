# agents-config

Versioned configuration for a local AI development environment using native
Claude Code and Codex. Choose an agent for each task. T3 is the proposed shared
entry point; the existing desktop installation and its state are retained.

**Status:** configuration source prepared and tested. Both Claude provider profiles
are available. T3 is configured for OpenAI/Codex, Claude (Vertex) and Claude via
EnMaaS, which also lists GLM 5.3 and DeepSeek V4.1 Flash; each Claude entry hides
only the models its route cannot serve. The extra named Vertex instance is disabled.
Full T3 chat verification is pending. Selected user-level team plugins have been refreshed,
and Codex's older personal Jira plugin is disabled with its installation retained.
Claude's declared dependencies are installed and its native load checks pass.
The approved shared/agent instructions are deployed globally to Claude and Codex.
Retiring old setup guides remains a migration step.
Developer workflows and costs come later. See [Claude profiles](docs/claude-profiles.md)
and [plugin selection](docs/plugin-selection.md).

## Layout

```text
agents-config/
├── AGENTS.md                  # Instructions for maintaining this repository
├── .env.example               # Template for local endpoint/project values (copy to .env)
├── instructions/              # Common personal rules + Claude/Codex additions
├── config/                    # Selected non-secret native settings
├── profiles/claude/           # Explicit Vertex and EnMaaS routing overlays
├── bin/                       # Native Claude launchers for terminal and T3
├── shared/
│   ├── providers.toml         # Provider profile selection and local auth locations
│   └── mcp.json               # Explicit custom MCP registrations by host
├── dotfiles/                  # Chezmoi native-path templates and selective modifiers
├── plugins/manifest.json      # Selected team plugins and marketplace sources
├── skills/                    # Existing personal skill; new workflows deferred
├── tools/Brewfile             # Explicit dependency installation list
├── scripts/                   # Setup preview/apply/restore, inventory, update plan
├── tests/deployment/          # Real chezmoi tests in temporary destinations
├── versions.lock.json         # Observed versions; not a dependency resolution lock
└── docs/                      # Audit, decisions, migration and source references
```

## Everyday commands

Requirements: Python 3.11+ and chezmoi 2.73.3+. Both are now available on this
machine's PATH. For another Mac, install chezmoi with `brew install chezmoi`, or
review `tools/Brewfile` before using `brew bundle --file=tools/Brewfile`.

Local values: the profile launchers (`bin/claude-vertex`, `bin/claude-enmaas`)
read environment-specific values — the EnMaaS endpoint and the Vertex project
ID — from a local, gitignored `.env`. After cloning, copy `.env.example` to
`.env` and fill in your values; a launcher fails closed, naming the missing
variable, until you do. Credentials never go into `.env`; they stay in the
agents' native authentication stores.

```sh
./scripts/doctor.sh                         # Local inventory; no inference or network
./scripts/doctor.sh --project /path/to/repo  # Also inspect that project's skill locations
./scripts/doctor.sh --check-claude-plugins  # Native resolution check; no model calls
./scripts/setup.sh --check                  # Default: validate and preview, no native writes
./scripts/setup.sh --check --component t3   # Preview only T3 provider/settings changes
./scripts/setup.sh --check --component plugins # Preview only plugin enable/disable choices
make test                                  # Deployment tests, shell syntax, whitespace
./scripts/update.sh                        # Print native plugin update commands only
```

`CHEZMOI=/absolute/path/to/chezmoi` overrides the deployment/test binary. Runtime
configuration previews print file status, never native setting values. Do not
publish raw `chezmoi diff` output: existing settings may contain credentials.

When a cutover is authorized, close the affected agent sessions and run:

```sh
./scripts/setup.sh --apply
```

This previews first, makes an external private backup, applies with chezmoi,
and checks the resulting configuration. It does not install tools, change
authentication, update plugins or edit shell startup files.

Update a selected agent's team plugins separately:

```sh
./scripts/update.sh --agent claude --apply
./scripts/update.sh --agent codex --apply
./scripts/doctor.sh --check-claude-plugins --record
```

Native installers may download or run plugin installation hooks and can prompt.
The updater does not accept arbitrary hooks automatically. Operations stop at
the first failure; previous successful updates remain applied. Restart sessions
after updates. Review and commit the new observations in `versions.lock.json`.
No automatic background updater has been enabled.
Claude updates also check native plugin resolution before reporting success.
The explicit doctor check exits nonzero if a selected plugin is absent, disabled,
has load errors, or the native check cannot run. It uses `--project` when supplied;
otherwise it checks from this repository. Ordinary doctor inventory remains separate.
These checks inspect plugin metadata; they do not start MCP/LSP servers or invoke skills.

## Ownership

Chezmoi owns the deployment of selected settings and personal instructions.
Claude/Codex own authentication, session state and native plugin installation.
Projects own their instructions and skills. T3 owns its providers, threads,
database and authentication. No native configuration file is symlinked into Git.

- Claude: manage the selected model/effort, additive permission rules and selected
  plugin enablement; preserve all other settings, including native credentials.
- Codex: manage the selected model/effort and team plugin enablement; preserve
  memories, app plugins, project settings, MCP runtime and other configuration.
- Global instruction files are generated from `instructions/`. Existing unported
  instructions block deployment rather than being silently replaced.
- The existing personal `review-code-changes` skill is copied unchanged and
  deployed to its current Codex location. Divergence blocks deployment.
- T3 server/client settings are deployed from the populated source definitions.
  The source reuses the default Claude instance, adds Claude via EnMaaS and disables
  the extra Vertex instance. Client preferences set per-route model visibility;
  other providers' preferences are preserved. Claude's top-level `.claude.json` is ignored
  unless custom MCP definitions are populated.

The merge preserves parsed JSON/TOML values. Formatting and TOML comments may
change on apply. Permission lists are additive. Removing a plugin from the enabled
selection does not uninstall or disable it; explicit `disabled` entries disable
existing installations while preserving their files. Fresh machines do not get
placeholder entries for legacy plugins that were never installed.

Credentials, auth files, local backups, logs, chats, caches and databases stay
outside Git. Environment-specific identifiers (the EnMaaS endpoint, the Vertex
project ID) live only in the local `.env` created from `.env.example`; committed
profiles reference them with `${NAME}` placeholders, and launchers fail closed
when a value is missing. `.env` holds identifiers, never credentials. Read
[the inventory](docs/inventory.md), [migration steps](docs/migration.md) and
[design decisions and references](docs/decisions.md) before cutover.

## Revert

Change source configuration with ordinary Git commits/reverts and preview again.
For an exact configuration snapshot restore, use the backup path printed by apply:

```sh
./scripts/setup.sh --restore /absolute/path/to/backup
```

Restore first verifies all managed files still match their post-apply hashes. If
an application has changed a file, it stops before restoring anything so you can
reconcile the change. Backups contain native credentials: keep them local and
private. Restore covers file contents/modes, not newly created directories,
application versions, plugin caches, sessions or remote provider configuration.
