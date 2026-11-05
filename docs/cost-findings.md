# Cost findings ledger

Dedupe memory for the unattended spend review. The pipeline in
`skills/spend-review/SKILL.md` writes here; a person may also edit a verdict
directly. Record measured observations only: each row cites the codeburn rule
and the specific target, not a guess.

## Columns

| Column | Meaning |
| --- | --- |
| `ID` | Stable `<concept>:<target>` key. Authoritative once written. |
| `Rule` | The codeburn finding `id` that produced the row. |
| `First seen` / `Last seen` | Dates the finding was observed, not the dates of activity. |
| `Verdict` | `observed`, `proposed`, `deferred`, `accepted` or `rejected`. |
| `Evidence` | Measured numbers and the smallest useful quote. No transcript dumps. |
| `PR` | Pull request number when one was opened. |

## Rules

- Terminal verdicts are `accepted` and `rejected`. A terminal ID is never
  proposed again. `observed` and `deferred` are non-terminal; `deferred` also
  carries a `revisit-after` date in its evidence.
- A `health/*` PR closed without merging marks its finding `rejected`. Record the
  PR number, do not reopen it and do not restate the finding.
- Different targets for one concept are different IDs. The same target is never
  re-proposed after a terminal verdict.
- Findings whose destination is another repository are recorded here and not
  patched by this repository.
- Savings figures are codeburn client estimates from local token accounting, not
  invoices.

## Entries

| ID | Rule | First seen | Last seen | Verdict | Evidence | PR |
| --- | --- | --- | --- | --- | --- | --- |
| `mcp-coverage:t3-code` | mcp-low-coverage | 2026-11-05 | 2026-11-05 | observed | `t3-code`: 5/83 tools used (6%) across 51 sessions; ~16.3M tokens, ~$2.29 est. | — |
| `mcp-scope:plugin-ci-ship-status` | mcp-project-scope | 2026-11-05 | 2026-11-05 | observed | Used in `hypershift` (2 calls); loaded unused in `gcp-hcp-infra`, `gcp-hcp`, `release` and 3 more. Destination is project MCP configuration, not this repository. | — |
| `low-worth-sessions:global` | low-worth-sessions | 2026-11-05 | 2026-11-05 | observed | 6 possibly low-worth expensive sessions; ~$21.80 est. | — |
| `context-heavy:global` | context-heavy-sessions | 2026-11-05 | 2026-11-05 | observed | 10 context-heavy sessions; ~$0.61 est. | — |
| `read-edit-ratio:instructions-common` | read-edit-ratio | 2026-11-05 | 2026-11-05 | observed | 428 reads to 525 edits (0.8:1); codeburn's healthy floor is 4:1. Candidate destination is the shared instructions. | — |
| `redundant-rereads:instructions-common` | redundant-rereads | 2026-11-05 | 2026-11-05 | observed | 118 redundant re-reads; `psc_endpoint_controller.go` 25x, `hostedcluster_controller.go` 14x. Candidate destination is the shared instructions. | — |
| `instructions-length:gcp-hcp-infra` | claude-md-too-long | 2026-11-05 | 2026-11-05 | observed | 421 lines; ~6.6K tokens per call. Owned by `gcp-hcp-infra`. | — |
| `instructions-length:release` | claude-md-too-long | 2026-11-05 | 2026-11-05 | observed | 263 lines. Owned by `release`. | — |
| `cost-outliers:global` | cost-outliers | 2026-11-05 | 2026-11-05 | observed | 2 high-cost session outliers; ~$0.29 est. | — |
| `bash-output-cap:claude-settings` | bash-output-cap | 2026-11-05 | 2026-11-05 | observed | 30K-char cap against ~15K typical output; ~3.8K tokens per bash call. Candidate destination is `config/claude.json` plus the deployment allowlist. | — |
