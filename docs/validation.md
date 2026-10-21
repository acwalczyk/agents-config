# Initial repository review — October 21, 2026

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
