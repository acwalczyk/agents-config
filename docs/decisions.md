# Decisions and source references

## Keep a small shared source and native runtimes

The portable layer consists of instructions, selected preferences, plugin
selection and custom MCP definitions. Authentication and application state stay
native. Environment-specific identifiers (the gateway endpoint and the Vertex
project ID) live in a local, gitignored `.env` created from `.env.example`;
committed profile overlays reference them with `${NAME}` placeholders, and the
launchers fail closed when a referenced value is missing. `.env` never holds
credentials. No model-routing proxy is introduced.
Choosing Claude Code or Codex per task does not require transcript conversion.

Use one deployment owner: chezmoi. Native selective modifiers preserve other
settings; generated instruction files have explicit ownership. This follows
[chezmoi's documented partial-file management](https://www.chezmoi.io/user-guide/manage-different-types-of-file/).
The `dotfiles/` source root follows its
[source-root convention](https://www.chezmoi.io/reference/special-files/chezmoiroot/).
The wrapper isolates its own chezmoi state instead of changing global chezmoi settings.

Native host formats remain distinct. See
[Claude settings](https://code.claude.com/docs/en/settings),
[Codex configuration](https://learn.chatgpt.com/docs/config-file/config-basic),
[Codex skills](https://learn.chatgpt.com/docs/build-skills) and
[Claude plugin discovery](https://code.claude.com/docs/en/discover-plugins).
Keep global rules short and project knowledge local. A skill can share content
without every host supporting the same tools, invocation flags or discovery roots.

## Borrow concepts from the team's configuration, not its personal defaults

Reviewed teammate source:
[patjlm/agents-config at 063381c](https://github.com/patjlm/agents-config/tree/063381c42cf4d3ff020dd558b75c418358848790).
Useful patterns include common instructions, per-agent rendering, shared non-secret
metadata, explicit plugin selection, validation and keeping secrets external.
This implementation is independent; it does not run or import the teammate installer.

We retain our inventory, deployment tests, diagnostic command, external snapshots
and migration guide. We do not adopt the teammate's provider/project choices,
GLM defaults, personal hooks, universal delegation policy or full-file overwrite.
Those would change permissions, routing or app integrations without establishing
that they suit this environment.

## T3 upstream first; fork features are optional

The teammate's actual changes were on
[patjlm/t3code's local branch at 52c2553](https://github.com/patjlm/t3code/tree/52c25535c83471c37c563c8fd0de9f03837508c4),
not its default branch. The six unique commits add terminal splitting/resizing,
link/selection preferences, scroll behavior and unfocused-pane dimming. They do
not add model routing, shared skill installation or a new provider backend.

At inspection that branch was six commits ahead and 146 behind upstream's main
relative to their merge base. This is a dated snapshot, not a current maintenance
guarantee. No fork release was found. Adopt it only if those terminal features
justify maintaining a local fork; do not make it a setup dependency by default.
See upstream
[installation](https://github.com/pingdotgg/t3code/blob/main/docs/user/install.md),
[Claude provider](https://github.com/pingdotgg/t3code/blob/main/docs/user/providers-claude.md)
and [Codex provider](https://github.com/pingdotgg/t3code/blob/main/docs/user/providers-codex.md)
documentation when validating the existing desktop version.

## Track observations without claiming a reproducible binary lock

Git reproduces intended configuration. `versions.lock.json` records observed
versions/caches; it does not pin Homebrew, guarantee plugin loading or restore
an old runtime automatically. Homebrew's Brewfile installs its current packages.
Native catalogs and running agents need separate refresh/restart verification.
Future exact binary pinning can be added if the maintenance benefit is demonstrated.

There is no evidence here establishing that OpenCode always doubles tokens or
that a routing proxy always saves money. Compare actual completed-task usage in
the later cost layer rather than using those claims to select the local setup.
