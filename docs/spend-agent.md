# Spend review agent

One unattended agent reads local session telemetry once a week, finds measured
token waste with `codeburn optimize`, and opens one small draft PR against this
repository. The role is `agents/spend-analyst.md`; the pipeline is
`skills/spend-review/SKILL.md`; dedupe state is `docs/cost-findings.md`.

This is the only write-capable automation in this setup. It exists to turn
measured waste into reviewable source changes, not to apply configuration.

## Where it runs

It runs in a dedicated clone, registered as its own T3 project:

```sh
git clone https://github.com/acwalczyk/agents-config.git \
  ~/Development/agents-config-spend
```

It does not run in the primary checkout. Writing `health/<date>` branches, test
artifacts and commits in the working copy would collide with normal work, and
the binding below denies writes to the primary path as a second guard.

It does not run in `agent-automations`. That project is read-only by design:
`blockReadsOutsideWorkingDirectories` and its sandbox block CodeBurn from reading
`~/.claude/projects/`, and the morning briefing must stay read-only. Sharing a
binding would weaken the briefing or break the review.

### Why a clone rather than a worktree

The T3 `schedule_task` tool takes a `projectId`; it has no worktree or workspace
selector. It cannot bind a scheduled task to an arbitrary worktree. A worktree
could be registered as its own project by path, but it shares refs and the object
database with the primary checkout, and `git fetch`/`git switch` there affect the
shared repository. A clone keeps refs, branches and the working tree independent.
This was read from the tool's declared schema; no scheduled task was run to
confirm runtime behavior.

## Binding

Copy the committed binding into the clone as project settings:

```sh
mkdir -p ~/Development/agents-config-spend/.claude
cp agents/spend-analyst.settings.json \
  ~/Development/agents-config-spend/.claude/settings.json
printf '.claude/\n' >> ~/Development/agents-config-spend/.git/info/exclude
git -C ~/Development/agents-config-spend status --porcelain   # expect empty
```

The binding is committed at `agents/spend-analyst.settings.json` but is inert
there; Claude only loads `.claude/settings.json`. It must not be committed inside
the clone: a project settings file on `main` would apply `dontAsk` and the
sandbox to the primary checkout after a merge and block normal interactive work.
`.claude/` is gitignored, and the local exclude keeps a fresh clone clean before
that ignore file reaches it.

The home paths in the binding are absolute and machine-specific. Adjust them on
another machine; the paths named are the two session stores CodeBurn reads, the
gh files, and the directories the sandbox must not write.

### Allow

- `Read`, `Edit`, `Write` inside the checkout.
- `git` (branch, add, commit, push of the branch it created).
- `gh pr create`, `gh pr view`, `gh pr list`, `gh pr diff`, `gh auth status`.
- `make test`, `scripts/setup.sh --check`.
- `codeburn optimize --format json`, `jq`.

### Deny

- `gh pr merge`, `gh pr review`, `gh pr comment`, `gh pr edit`, `gh pr close`,
  `gh pr ready`, `gh api`, `gh issue`, `gh repo`, `gh release`, `gh workflow`.
- Force push, `git reset --hard`, `git clean`, `git rebase`, pushes to `main`.
- `scripts/setup.sh --apply`, `codeburn optimize --apply`, `codeburn guard`.
- `rm -rf`, `curl`, `wget`, `osascript`, `open`.

`defaultMode` is `dontAsk`, so anything not allowlisted fails closed instead of
waiting for a prompt. The sandbox is mandatory (`failIfUnavailable`,
`allowUnsandboxedCommands: false`) with writes denied to `~/.claude`, `~/.codex`,
`~/.t3`, `~/.config/gh`, the backup state directory and the primary checkout.
Network is limited to GitHub.

### gh authentication

`gh` must authenticate inside the sandbox. That requires gh's token in its native
plaintext store (`~/.config/gh/hosts.yml`, mode `0600`, outside Git) with a
user-level `allowRead` for `hosts.yml` and `config.yml`, plus
`enableWeakerNetworkIsolation` for the macOS trust service. This mirrors the
morning briefing. Moving gh's authentication back to the macOS keyring makes
sandboxed `gh` return 401.

CodeBurn reads `~/.claude/projects` and `~/.codex/sessions`; those paths are in
the binding's `allowRead`. The pipeline never commits raw transcripts or
codeburn output.

## Schedule

The schedule is T3 app state on this machine, not Git. It is a weekly T3
scheduled task that creates a fresh thread in the spend project
(`bindToCurrentThread: false`), so runs do not land in an interactive thread.
Adjust the cadence in T3; nothing in the repository depends on it.

The scheduled prompt should be short and defensive, for example:

```text
Run the spend review. Read skills/spend-review/SKILL.md in this checkout and
follow it exactly. If that file is missing, report that the pipeline is not
installed and stop without changing anything.
```

The guard matters because the clone tracks `main`: until the review pipeline is
merged there, a run has nothing to follow and must not improvise.

## Operating it

- Inspect past runs as threads in the T3 spend project.
- Pause it in T3's scheduler; do not delete the project if you want to keep the
  thread history.
- A run that finds nothing actionable opens no PR and reports why. That is a
  normal outcome, not a failure.
- A failing `make test` baseline aborts the run before any edit.
- Each PR is a draft. Merging, requesting changes or closing it is a human
  decision. A closed-unmerged PR makes its findings `rejected` in the ledger and
  they are not proposed again.

## Not verified

- The permission and sandbox binding has not been exercised by a live scheduled
  run. Its first run is the real test.
- Whether T3's Claude driver loads `.claude/settings.json` from the project root
  in the same way the native CLI does is assumed from the morning briefing
  setup, not measured here.
- CodeBurn's savings are estimates derived from local token accounting, not
  provider invoices.
