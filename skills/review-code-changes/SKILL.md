---
name: review-code-changes
description: Review local code changes after implementation and before commit or PR for correctness, edge cases, test quality, repository conventions, efficiency, and readiness. Use for a senior-engineer review of an implementation diff, including repository validation. Do not use for plan-only review or deployed-system testing.
---

# Review Code Changes

Review the actual diff as a repository owner would. Give a decision backed by concrete findings and executed checks. Review implementation without editing it unless the user asks for fixes. Repository formatting commands may change files; inspect and report those changes.

## Establish the review scope

- Identify the repository, review baseline, staged and unstaged changes, untracked files, and any supplied implementation plan or ticket. State the baseline used. Include relevant call sites and tests, not only changed lines.
- Read applicable `AGENTS.md`, repository instructions, nearby code, and CI or Makefile targets. Derive conventions and validation commands from this repository rather than assuming a universal toolchain.
- Compare the diff with the intended behavior. Distinguish required work, necessary implementation plumbing, and unrelated expansion. If no plan is supplied, review the stated goal and describe any ambiguity that affects the verdict.

## Assess the change

- Trace important paths through success, failure, retries, and cleanup. Check applicable boundaries such as empty or missing input, limits, duplicate calls, ordering, concurrency, ownership, compatibility, and partial failure. Raise edge cases with a plausible trigger and consequence. Recommend an in-scope fix when proportionate; label larger work as a separate-ticket candidate and explain the remaining risk.
- Check correctness, error handling, API behavior, naming, structure, and consistency with nearby repository patterns. Evaluate runtime, memory, I/O, and code size where the change could materially affect them. Prefer simpler code when behavior and clarity are preserved; avoid speculative micro-optimizations.
- Inspect added or changed source comments. Flag session-specific references such as “Issue #5,” stale implementation narration, and comments longer than three lines. Keep suggested comments to two or three lines. Respect comments required by API documentation, licensing, or repository tooling.
- Judge tests by the behaviors and failures they cover. Identify missing meaningful coverage, redundant cases, excessive fixtures, and assertions that do not prove the intended behavior. Suggest consolidation, including table-driven cases where clear, without merging tests that need distinct setup or failure diagnosis. Do not reward test count or line count by itself.
- Ask whether a senior owner could approve the diff as it stands. Report actionable problems, not generic best-practice lists. Verify each finding against current code and cite the relevant file and line.

## Run repository checks

- Discover and run the repository's formatting, generated-file verification, lint or static checks, and full unit-test target when available. Run additional checks required by the changed area. Follow repository-specific prerequisites and avoid commands that deploy, mutate remote resources, or require secrets merely for review.
- Inspect the diff after formatting; report any file changes. If formatting changes code, validate the resulting state. Do not commit, push, post comments, or make implementation fixes unless requested.
- Record each command and result. If a check cannot run or finish, give the reason and exact coverage achieved. Distinguish a code failure from an environment or pre-existing failure when evidence permits. Never report an unrun or incomplete check as passing.

## Report

Lead with **Approve**, **Request changes**, or **Validation incomplete** and a one-sentence reason. Approve only when no blocking findings remain and required checks pass. List blocking findings first, then non-blocking improvements and separate-ticket candidates. For each finding, give location, trigger, consequence, and the smallest reasonable change. If there are no actionable findings, say so.

Finish with the validation commands and their results, formatting changes, and any unverified areas or remaining risks. Keep the report concise enough to act on; do not turn every checklist item into a finding.
