# Initial repository review — October 21, 2026

Each section records validation at that step; later sections supersede earlier
deployment limits.

**Approve** for the prepared configuration source: no blocking findings remain
in the initial diff. This does not certify live provider connectivity or complete
the application cutover.

Scope: new repository against an empty Git baseline; all staged and unstaged
content reviewed using the existing personal `review-code-changes` skill.
The skill itself was ported unchanged, not redesigned.

## Executed checks

- `CHEZMOI=/private/tmp/agents-config-validation/chezmoi make test`: all six
  deployment tests pass using the real chezmoi binary. The tests exercise native
  setting/credential preservation, repeat application, exact file restore, fresh
  destinations, restore conflicts, malformed input redaction, symlink and unported
  instruction rejection, optional MCP/T3 merging and non-executing update plans.
- Shell syntax and staged/unstaged whitespace checks pass as part of `make test`.
- `python3 -m compileall -q scripts tests/deployment`: passes.
- Real-home `setup.sh --check`: selected Claude/Codex settings and existing personal
  skill match; only the two generated global instruction files would change content.
- `doctor.sh --record --project /Users/dwalczyk/Development/HCP/hypershift`:
  records installed tool/cache evidence and reports provider ambiguity and duplicate Jira sources.
- Native update command syntax checked against installed CLI help; plans inspected
  without executing plugin or marketplace updates.
- Known native/gateway credential values checked against tracked files: no matches.
  No native auth files, gateway `.env` or state databases are tracked.
- Fingerprints of inspected live configuration, authentication, shell startup,
  personal skill and old setup-guide files remain unchanged during final validation.
- GitHub repository metadata confirms the remote is private.

Chezmoi 2.73.3 was downloaded from the official release into a temporary directory.
The Darwin arm64 archive's SHA-256 matched its published release checksum:
`ec2d0005f369c912ee9891a26c30d65dc0eda51708f06948e5f7a43db69e1aa7`.
No global chezmoi installation was performed.

## Limits

No live application configuration has been applied. Native provider authentication,
sample inference, T3 provider compatibility and actual remote plugin updates remain
unverified. The tests cover configuration handling with synthetic fixtures, not
every plugin's behavior. Configuration restore is file-based and cannot roll back
plugin binaries, sessions or remote actions. Follow `migration.md` for cutover.

## Provider-profile follow-up

**Approve** the source changes against initial commit `ec8f075`: 12 deployment
and launcher tests pass, including T3-only scope, empty-selection handling,
SDK-settings merging, stdin/stdout preservation, cancellation cleanup, unchanged
model defaults and credential isolation. Shell syntax, Python compilation and
staged whitespace checks pass. Known native credential values are absent from source.

Both named launchers completed minimal live CLI inference. T3's two provider
entries were applied and a second T3-only preview is unchanged. Other inspected
native configuration stayed unchanged. Full T3 chat remains unverified because
computer-control permission was unavailable. See `claude-profiles.md` for exact
test models, reported usage and the remaining manual UI check.

## Plugin consolidation follow-up

**Approve** the source changes against `2e55364`. The explicit disabled list is
validated, preserves legacy installations, and avoids unresolved legacy entries
on fresh machines. The plugin-only component changes enablement while leaving
models, permission policies, MCP registrations and global instructions untouched.

Thirteen deployment/launcher tests pass, including plugin-only scope, legacy-cache
preservation and exact restoration. Shell syntax, Python compilation, whitespace
checks and a native-setting comparison against the external backup pass. Native
Claude update commands and Codex marketplace/plugin commands completed successfully.
Codex's plugin list confirms team Jira enabled and personal Jira disabled, both
still installed. `versions.lock.json` records refreshed versions and retained scopes.

Existing sessions were not restarted, no Jira API writes were performed, and two
older project-scoped Claude installations remain documented separately. Full T3
chat validation remains pending.

## Project-plugin refresh follow-up

Both explicit native project-scope updates succeeded in gcp-hcp: Jira 0.9.1 to
0.9.6 and GCP HCP 0.0.4 to 0.0.6. Fresh `claude plugin list --json` confirms
matching user/project versions and no load errors on those two plugins. Before
the updates, `plugin details` already resolved the current versions; the retained
older registrations were not proof of stale loading in those fresh commands.

Native registry comparison shows only those two plugin selectors changed. Private
backup fingerprints confirm native user settings and project settings, skills,
instructions, Git status and staged/unstaged diffs were preserved. Doctor records
the aligned registrations and no longer warns about these older project versions.
This follow-up changes documentation and observed inventory only; no implementation
or deployment behavior changed.

**Validation incomplete** for the broader plugin setup: the native Claude list
reports unsatisfied `gopls-lsp@ai-helpers` and `ci@ai-helpers` dependencies for Go
and OpenShift Developer respectively. The earlier successful update checks did
not check native load errors. Those dependency choices remain a separate next
step. No model calls or Jira requests were made during this follow-up.

## Claude dependency repair and native-check follow-up

**Approve** the source changes against `70d335f`, reviewed with the existing
personal `review-code-changes` skill. No blocking findings remain. The Claude
selection includes all declared bundle dependencies; the updater verifies native
resolution after successful native update/install commands. Doctor exposes the
same check explicitly, records its status when requested and exits nonzero for
missing/disabled/broken plugins or an unavailable check. Raw native output is
captured and suppressed. Codex's selection and configuration are unchanged.

- `make test`: all 17 tests pass. Added cases exercise errors hidden behind enabled
  flags, missing/disabled plugins, unavailable/malformed native output, output
  redaction, selected scope, and update-command success followed by load failure.
- `python3 -m compileall -q scripts tests/deployment`: passes.
- Shell syntax and staged/unstaged whitespace checks pass.
- Native doctor failed before repair and passes afterward in gcp-hcp. Fresh native
  lists from both agents-config and gcp-hcp report no plugin load errors.
- Component checks show Go/OpenShift skills and hooks, Go's MCP server and the
  official Go language server. The team Go dependency entry exposes zero LSP
  servers, so the official entry remains enabled alongside it.
- `setup.sh --check --component plugins`: both native setting files match source.
- Private backup comparisons confirm all non-plugin Claude settings, Codex
  settings/authentication, T3 settings, shell files, global instructions, project
  skills/settings/instructions and existing project Git changes were preserved.
- Known native credential values are absent from tracked and pending source files.

Native installation/enablement was separately authorized and performed through
native plugin commands and the chezmoi wrapper. No model inference, Jira requests,
interactive-session startup or plugin hook execution was needed for these checks.
Live MCP/LSP server startup and each skill's behavior remain outside this metadata
verification. Full T3 chat and global-instruction deployment remain pending.

## Approved global-instruction deployment

The user reviewed `instructions/common.md`, `instructions/claude.md` and
`instructions/codex.md` and approved them. No instruction source content changed
during deployment. The supported chezmoi wrapper deployed the rendered files to
`~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`, with a private backup at
`~/.local/state/agents-config/backups/20261021T214932Z-ktigk2c2/`.

- Pre-apply preview identified only those two instruction content changes.
- Post-apply preview reports all six managed files matching source.
- Both generated files contain the managed header, full approved shared text and
  the corresponding agent-specific text.
- Fingerprints confirm native settings/authentication, plugin registrations,
  personal skill, T3 settings, shell files, source instructions, project
  instructions/skills/settings and existing project Git changes stayed unchanged.
- Codex uses the expected home, has no global `AGENTS.override.md`, and surfaced
  the approved global instructions in this chat after deployment.

This step changes deployment records only; the existing deployment implementation
and instruction source were unchanged. Whitespace validation passes. The 17 tests
passed in the preceding implementation step and were not rerun for this deployment
record. No dedicated model probe or Jira request was made. A new Claude session
will pick up its global file; the full T3 chat check and old-guide/helper retirement
remain pending.

OpenAI Docs was used to check Codex discovery and refresh behavior against the
[official AGENTS.md documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

## T3 provider-count correction

**Approve** the source changes against `f1d3109`, reviewed with the personal
`review-code-changes` skill. The screenshots showed a default Claude entry plus
the two named instances, giving four active entries with Codex. Installed T3's
registry hydration code confirms that it synthesizes the built-in default unless
an explicit entry uses that driver's ID.

The corrected source reuses `claudeAgent` for Claude through Vertex, labels
`claude-enmaas` as EnMaaS and disables the extra `claude-vertex` entry. The modifier
carries existing legacy configuration into the default instance without aliasing
or mutating it. The legacy in-config enabled flag is omitted so it cannot veto
the selected envelope flag. Imported history and authentication remain app-owned.

- `make test`: all 18 tests pass, including legacy home/model/launch-argument
  preservation, explicit enablement over an old disabled flag, duplicate disablement,
  untouched history data, repeat application and other deployment safeguards.
- Python compilation, shell syntax and whitespace checks pass.
- T3-only deployment succeeded with private backup
  `~/.local/state/agents-config/backups/20261021T215748Z-3o5xjcni/`.
- Post-apply preview matches source. Applying the installed registry's default
  hydration/enablement rules to the saved settings resolves exactly Codex, Claude
  and EnMaaS as active; the extra named Vertex instance is disabled.
- Native comparison confirms EnMaaS routing/models, other providers, unrelated
  T3 server/client settings, authentication, Claude/Codex configuration, global
  instructions and shell files were preserved. History databases were not targets.

The rendered picker after correction and full T3 chat execution remain unverified.
Close/reopen the picker or restart T3 if it retains the old list. EnMaaS remains
on its existing native Claude backend; whether to support every gateway model,
including GLM, is a pending user choice. This correction changes no model defaults
and performs no model inference.
