# Migration

## 1. Prepare and review — completed for the initial commit

- Create a private `acwalczyk/agents-config` remote and local Git repository.
- Port selected non-secret Claude/Codex settings and the existing personal review skill.
- Record current tools/plugins and keep project skills with their repositories.
- Test real chezmoi in temporary destinations, including preservation, fresh setup,
  invalid input, idempotence, symlinks, private backups and restore conflicts.
- Run a values-suppressed preview against the real native configuration.

The initial real-home preview reports only two content changes: generated global
Claude and Codex instructions. Selected settings and the personal skill already
match the current files. Private-directory/file modes can also be enforced on apply.
At the initial commit, no live configuration, plugins, credentials or shell files
had been changed. Subsequently, only the two selected T3 provider instances were
applied. See `claude-profiles.md` for the live probe results and remaining UI check.

## 2. Resolve cutover decisions

1. Claude provider choice is resolved: keep both with explicit per-task launch
   profiles. See `claude-profiles.md`. Existing shell/default settings remain
   unchanged while the named profiles and T3 instances are verified.
2. Decide whether to keep the older personal Jira plugin alongside the team plugin.
3. Use the existing upstream T3 installation first if its native Claude/Codex
   providers meet the per-task selection requirement. Provider settings and auth
   remain T3-owned; a blank `config/t3.json` makes no app changes.

Model prices, routing optimization and detailed workflow design are deferred.
These decisions do not need to be guessed to review or reuse the configuration source.

## 3. Apply selected configuration

Install chezmoi when ready. Review source configuration and instructions, close
the affected agent sessions, run `scripts/setup.sh --check`, then
`scripts/setup.sh --apply`. The wrapper uses isolated chezmoi config/state/cache,
so it does not take over another personal dotfiles repository.

Backups go under `~/.local/state/agents-config/backups/` with private directories
and files. They contain native settings, including any local credentials; do not
move them into this or another Git repository. Restore is described in README.md.
The backup root can be overridden with `--backup-root /outside/the/repository`.

The configuration wrapper is the supported path. A direct chezmoi invocation
bypasses its instruction reconciliation, symlink checks, backups and redaction.
Changes are not transactional across files; if apply fails, inspect the saved
backup and restore before retrying. Run with agents closed to avoid concurrent writes.

## 4. Refresh native plugins and verify

Review `scripts/update.sh --agent AGENT` and use `--apply` only when ready to
update that agent. The script uses its native plugin commands, scopes Claude
installs to the user and leaves project installations and app-bundled plugins alone.
Plugin commands are not configuration deployment and may update native registration.
The update plan does not verify that remote catalogs are current until it is executed.

Re-run `doctor.sh --record`, inspect the version changes, restart sessions and
explicitly invoke a known relevant skill in the actual project. Check both tools;
a cached version directory is not proof that the host loaded it. Native provider
login and any sample inference are separate verification steps, not part of the tests.

## 5. Retire superseded guides and helpers after verification

Replace or archive `~/Development/HCP/AI-DEV-SETUP.md` only after the new guide
and routing configuration cover its useful content. Review `.ai-config.sh` aliases,
paths and exports before removing its shell references. Keep any useful shortcuts
in the chosen shell configuration source rather than leaving two AI setup owners.
The current repository does not yet deploy shell/provider changes.

Do not delete `.claude`, `.codex`, `.t3` or other application directories. Do not
remove `llm-homebase`, containers, credentials or gateway data as incidental cleanup.
Its retirement is a separate scoped action after confirming there are no consumers.

## Optional custom MCP registration

`shared/mcp.json` is an explicit registry of custom servers. It starts empty
because current useful servers are plugin-owned or app-managed. Avoid registering
another copy of them. Each server can provide `claude` and/or `codex` native stanzas:

```json
{
  "servers": {
    "example": {
      "claude": {"command": "example-mcp", "args": ["--stdio"]},
      "codex": {"command": "example-mcp", "args": ["--stdio"]}
    }
  }
}
```

Only populated host stanzas deploy. Other server registrations remain intact;
a selected server's own stanza is source-owned and replaced as a unit. Use native
environment inheritance, credential helpers or host-supported external secret
references. Do not put literal API keys, authorization headers or tokens here.
Do not assume every host expands the same `${VARIABLE}` syntax.
