# Local inventory — October 21, 2026

Read-only inspection of known AI configuration locations, shell startup and
relevant development directories. This was a targeted audit, not an exhaustive
scan of every personal directory. No credential values were copied or logged.
`versions.lock.json` records the observed tool versions and selected plugin caches.

## Active tools and state

| Tool | Observed state | Treatment |
| --- | --- | --- |
| Claude Code | CLI 2.1.304; native settings, plugins and local sessions | Retain native app state; port selected settings |
| Codex | CLI 0.163.0; Desktop projects/chat; API-key authentication | Retain auth, app plugins, memory, project and session state |
| T3 Code Alpha | Desktop 0.0.45; client settings, provider/thread SQLite state and Clerk auth | Retain installation and state; validate native providers during cutover |
| OpenCode | CLI 1.18.20; points at local LiteLLM/homebase gateway | Legacy path; no new daily dependency |
| llm-homebase | Existing gateway environment and routing config under HCP | Retain until separately retired; do not copy secrets |
| CodeBurn / OMP | Installed, outside current daily Claude/Codex workflow | Revisit only in the appropriate later layer |
| chezmoi | Not installed on PATH | Official 2.73.3 binary tested in a temporary directory |

## Findings that affect migration

1. **Claude provider ambiguity.** `~/.claude/settings.json` contains an EnMaaS
   endpoint and native credential. `~/.zshrc` and `~/.bashrc` load
   `~/.config/claude-code-vertex/env.sh`, enabling Vertex, project
   `example-vertex-project`, region `global`. HCP's `.ai-config.sh` adds further model
   and effort variables. The actual effective provider was not established by a
   paid request. Resolve the desired provider before changing any of these.
2. **Multiple configuration sources.** `~/Development/HCP/.ai-config.sh` and
   `AI-DEV-SETUP.md` describe an older combined setup. Shell startup still sources
   the helper. Retiring its documentation is different from deleting app homes.
   The gateway has a separate OpenAI credential; do not consolidate by copying it.
3. **Plugin version drift.** Selected Claude plugins are older than Codex's cached
   counterparts. Claude marketplace timestamps for team sources were August 4;
   the official source was refreshed October 21. A marketplace refresh alone is
   not proof that installed plugins or running sessions have updated.
4. **Duplicate Jira sources in Codex.** Both `jira@personal` and `jira@ai-helpers`
   are enabled, exposing overlapping skills. Both remain enabled pending a choice;
   the new update manifest manages the team source only.
5. **Skill discovery depends on scope.** HyperShift has both `.agents/skills` and
   `.claude/skills`; their instructions/adapters can differ. Other repositories
   have Claude-only skills. Starting in the parent Development directory does not
   make all child repository skills available. Repository skills stay repository-owned.
6. **Global instructions are not a universal filename.** Codex's native global
   `~/.codex/AGENTS.md` is empty and no global Claude instruction file was found.
   This repository generates both native instruction files from a common source.
7. **App-written configuration must be preserved.** Codex has bundled app plugins,
   memory settings and an app-managed `node_repl` MCP registration. T3 has database
   and authentication state. Whole-file replacement with another person's templates
   would lose useful local state.

## Selected plugin capabilities already present

| Source | Useful capabilities to discover | Scope reminder |
| --- | --- | --- |
| ai-helpers / openshift-developer | Implementation, local review gates, PR feedback, CI triage, test plans, backports | Match the actual task; some workflows perform writes |
| ai-helpers / golang | Go lint, dependency/CVE work, Go release analysis | Do not invoke a fix workflow for a read-only question |
| gcp-hcp | Architecture context, scoped PR review, plan drift, feature support assessment | Some skills are explicit invocation workflows |
| ai-helpers / jira | Readiness, issue conventions, catch-up and issue creation | Jira writes require the user's exact preview and approval |
| hcp | Platform-specific cluster creation workflows | Not needed just to configure this machine |
| Personal review-code-changes | Review a local implementation before commit/PR | Ported unchanged; distinct from PR report generation |
| Codex bundled tools | Browser/computer tools, documents, diagrams and app coordination | Available according to the active app/runtime |

Installed, enabled, discoverable, applicable and actually invoked are different
states. `doctor.sh` reports local evidence, not a guarantee that an agent will
select a skill. Explicit invocation remains the reliable choice when one is required.
Connectivity, credentials and execution of every skill were not tested.

## Native locations retained

- `~/.claude/`, `~/.claude.json`: settings, native auth-related configuration,
  plugins, project state and transcripts.
- `~/.codex/`: config, auth, plugins, sessions, memories and databases.
- `~/.agents/skills` and existing per-agent skill directories: discover separately;
  do not blindly merge or delete duplicates.
- `~/.t3/userdata/`: client settings, authentication, databases and runtime state.
- `~/.config/opencode/` and HCP's `llm-homebase/`: legacy native configuration.
- Shell startup and Vertex loader: unchanged during repository preparation.
