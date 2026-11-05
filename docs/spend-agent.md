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

A T3 worktree would share refs and the object database with the primary checkout,
and `git fetch`/`git switch` there would affect the shared repository. A clone
keeps refs, branches and the working tree independent.

The clone also has to be where the run *executes*, not just where the repository
lives. Observed on this machine (November 5, 2026):

- `schedule_task` accepts `projectId`, `prompt`, `schedule`, `title`, `enabled`,
  `bindToCurrentThread` and `clientRequestId`. It has no workspace or worktree
  selector.
- A scheduled task created with `bindToCurrentThread: false` runs in a T3-managed
  git worktree, for example
  `~/.t3/worktrees/agents-config-spend/t3-0eb96604` on branch
  `t3/weekly-spend-review`. The environment preference
  `newWorktreesStartFromOrigin` is `true`, so that worktree is cut from
  `origin/main` and contains only tracked files. The untracked
  `.claude/settings.json` is absent, so the binding does not load at all.
- Setting the spend project's `defaultThreadEnvMode` to `local` did not change
  that: a second worktree-mode run still landed in a fresh `~/.t3/worktrees/`
  checkout.
- A thread bound to the project root (`worktreePath: null`) does load the
  checkout's `.claude/settings.json`. With `runtimeMode: full-access`, the
  binding's `dontAsk` default applied and the `Bash(curl *)` deny stopped a probe
  command with "Permission to use Bash ... has been denied".

So the trigger is a persistent thread bound to the clone root, and the schedule
posts into that thread. See [Schedule](#schedule).

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
sandbox to the primary checkout after a merge and block normal interactive work,
and it would also reach T3 worktrees cut from `origin/main`. `.claude/` is
gitignored, and the local exclude keeps a fresh clone clean before that ignore
file reaches it.

The untracked file is therefore effective only in threads bound to the clone
root, which is why the schedule is bound to a root thread rather than creating a
thread per run.

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
waiting for a prompt. Rules that are deny-listed are refused before execution:
a probe inside a root-bound thread was denied even though the thread ran with
`full-access`. The sandbox is mandatory (`failIfUnavailable`,
`allowUnsandboxedCommands: false`) with writes denied to `~/.claude`, `~/.codex`,
`~/.t3`, `~/.config/gh`, the backup state directory and the primary checkout.
Network is limited to GitHub.

Filesystem *read* confinement is weaker than the `allowRead` list suggests. In
the same probe, `git -C /Users/dwalczyk/Development/agents-config rev-parse
--show-toplevel` read the primary checkout and succeeded, and
`./scripts/setup.sh --check` read the native Claude, Codex and T3 files. Treat
`allowRead` as documentation of what the pipeline needs, not as a fence, and
treat the permission allow/deny lists as the enforced boundary. Write
confinement was not probed.

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

The schedule is T3 app state on this machine, not Git. It is a weekly (Monday
07:00 local) T3 scheduled task with `bindToCurrentThread: true`, bound to one
persistent thread in the spend project that is attached to the clone root
(`worktreePath: null`). Runs therefore execute where the binding loads, and they
do not land in a T3 worktree.

That binding is what forces the shape: the schedule has to be created *from*
inside the root-bound thread, because `bindToCurrentThread` always means the
calling thread. Creating it from another thread, or creating a fresh thread per
run, silently loses the binding.

The scheduled prompt should be short and defensive:

```text
Run the weekly spend review for agents-config in this checkout.

Read skills/spend-review/SKILL.md and agents/spend-analyst.md, then follow the
pipeline exactly. If skills/spend-review/SKILL.md is missing, report that the
pipeline is not installed and stop without changing anything.

Do not run scripts/setup.sh --apply, codeburn optimize --apply, codeburn guard,
gh pr merge, gh pr review, or a mutating gh api call. Open at most one draft PR
and never force push.
```

The guard matters because the clone tracks `main`: until the review pipeline is
merged there, a run has nothing to follow and must not improvise. The spend
project has `autoPull` enabled so the checkout is current when a run starts, and
the pipeline also switches to `main` and pulls before branching.

Because one thread accumulates every run, its history grows week over week. If it
gets unwieldy, launch a new root-bound thread and recreate the schedule from it;
do not switch the schedule back to one-thread-per-run.

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

- No run has executed the full pipeline end to end. The runs on November 5, 2026
  stopped at the missing-pipeline guard because the clone's `main` predates the
  merge of this pipeline.
- The sandbox's write confinement was not probed. Read confinement outside the
  checkout was probed and did *not* hold.
- Sandboxed `gh` authentication was not exercised: no `gh` command ran in the
  probe thread.
- A T3 worktree run was never given the binding. That path is documented as
  wrong rather than tested with the settings present.
- CodeBurn's savings are estimates derived from local token accounting, not
  provider invoices.
