---
name: spend-review
description: Collect codeburn optimization findings from local agent sessions, dedupe them against docs/cost-findings.md, and open at most one small draft PR with up to three evidence-backed fixes to agents-config. Run only from the dedicated spend checkout, unattended.
---

# Spend review

Turn measured session waste into a reviewable change. One run produces at most
one draft PR and at most three findings. Evidence comes from codeburn and the
repository's own checks; nothing is estimated by hand.

## 1. Preflight

Confirm you are in the dedicated spend checkout, not the primary working copy:

```sh
git rev-parse --show-toplevel      # expect .../agents-config-spend
git status --porcelain             # must be empty; never stash or discard
```

If the working tree is dirty or the root is `/Users/dwalczyk/Development/agents-config`,
stop and report it. Do not clean, reset or stash.

Runs must execute in the checkout root, where `.claude/settings.json` supplies
this binding. A T3 git worktree under `~/.t3/worktrees/` is created from
`origin/main` and never contains that file; if the root is under
`~/.t3/worktrees/`, stop and report that the run is misbound rather than
continuing unbounded.

Start from current `main` so the pipeline you are reading is the deployed one:

```sh
git switch main
git pull --ff-only
```

Establish a baseline before editing:

```sh
make test
```

If the baseline fails, stop without opening a PR and report the failure. A red
baseline is not a finding and must not be "fixed" by this run.

Create the branch from the remote default branch, never from a local `main` that
may be stale:

```sh
git switch -c health/$(date +%F) origin/main
```

If that branch already exists, append `-2`, `-3`, and so on. Never reuse or
force-update an existing branch.

## 2. Collect

```sh
codeburn optimize --format json --period week > "$(mktemp -t codeburn-optimize)"
```

Read only the JSON. The relevant fields per finding are `id`, `title`,
`explanation`, `severity`, `tokensSaved`, `estimatedSavingsUSD` and `fix`.
`summary` gives the period, session and call counts, and total estimated
savings. Keep the file outside the repository and never commit it; it is derived
from private transcripts.

If codeburn fails or returns no findings, report that and stop without a PR.

## 3. Assign a stable ID

Every finding gets a ledger ID of the form `<concept>:<target>`:

- `concept` is a short kebab-case noun for the waste (for example
  `mcp-coverage`). Reuse an existing concept when the same rule fires again.
- `target` is the specific object a fix would change: an MCP server name, a
  destination file in this repository, or a repository name for an external
  file. Use `global` only for aggregate findings with no single destination.

Examples: `mcp-coverage:t3-code`, `instructions-length:gcp-hcp-infra`,
`read-edit-ratio:instructions-common`.

The ledger key is authoritative. Before creating an ID, search
`docs/cost-findings.md` for the same concept and target and reuse that key even
if the wording differs. Different destinations for one concept are different
IDs; the same destination is never re-proposed after a terminal verdict.

## 4. Dedupe

Read `docs/cost-findings.md` before selecting anything.

Skip a finding when its ID is in a terminal state:

- `accepted` — already merged; do not propose it again.
- `rejected` — declined or its PR was closed unmerged; never reopen or restate
  it.
- `deferred` — skip until its `revisit-after` date has passed.

Also check GitHub for prior attempts, because a closed-unmerged PR may not yet be
recorded:

```sh
gh pr list --state all --limit 50 --json number,state,mergedAt,title,body
```

If a closed, unmerged `health/*` PR mentions the ID, treat the ID as `rejected`,
record the PR number in the ledger in this run's PR, and do not propose it.

## 5. Select

Apply all of these filters, then rank the survivors by `estimatedSavingsUSD`
descending and keep at most three:

- The fix must change a file this repository owns (`instructions/`, `config/`,
  `profiles/`, `plugins/`, `shared/`, `skills/`, `agents/`, `scripts/`,
  `tests/`, `docs/`, `README.md`).
- The change must plausibly reduce the measured cost and remain valid for the
  general case, not one session.
- A one-time prompt or shell snippet from `fix.text` is not a repository change
  by itself. Convert it only when it generalizes into a repository-owned file;
  otherwise record it as `observed`.
- Findings with no destination in this repository — another repo's `CLAUDE.md`,
  project MCP configuration, project skills or source — are ledgered and never
  patched. Record them as `deferred` with the owning repository.
- An administrator or provider-policy change is out of scope. Record it and
  stop.

If nothing survives, do not create a PR. Report the findings and reasons in the
run output. Ledger-only observations are written by the next run that does open
a PR.

## 6. Implement

Make one focused commit per finding on the `health/<date>` branch. Each commit
changes the smallest surface that addresses the finding and nothing unrelated.
When a finding touches a managed setting, change only the managed key and keep
the deployment tests passing.

Update `docs/cost-findings.md` in the same PR: set selected findings to
`proposed`, refresh their `Last seen` date, add skipped external findings with
their owner, and add terminal verdicts discovered in step 4. Keep the table's
existing column order.

## 7. Validate

After each commit, run both checks from the repository root:

```sh
make test
./scripts/setup.sh --check
```

If a check fails because of the change and you cannot make it pass with a small,
correct edit, revert that finding's commit and record it as `deferred` with the
failure. If a check fails for an unrelated or environmental reason, open no PR
and report the exact output. Never report an unrun or failing check as passing.

Never run `scripts/setup.sh --apply`, `codeburn optimize --apply` or
`codeburn guard`, never install plugins and never update native configuration.

## 8. Open the PR

```sh
body=$(mktemp -t spend-review-pr)
# write the body described below to "$body"
git push -u origin health/<date>
gh pr create --draft --base main --head health/<date> \
  --title "health/<date>: cost review" --body-file "$body"
```

Write the body outside the repository so it cannot be committed.

The body contains, in this order:

- A one-paragraph summary naming the codeburn period, sessions, calls and total
  estimated savings.
- One section per finding: ledger ID, codeburn rule and title, measured evidence
  (sessions, tokens, estimated USD, the quoted explanation), the change, and why
  it should reduce the measured cost.
- A ledger section listing every verdict added or changed.
- A validation section with the exact commands and observed results.
- A not-verified section: what the change could not confirm, including that the
  savings are an estimate until subsequent sessions are measured.
- The line `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

Use `--draft`: the owner decides when it is ready for review. Do not mark it
ready, comment on it, review it or merge it.

## 9. Report

Return a short report: the findings read, selected and skipped with reasons, the
ledger IDs touched, the validation commands and results, the PR URL, and what
remains unverified. If no PR was opened, state the reason plainly.
