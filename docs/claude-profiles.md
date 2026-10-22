# Claude provider profiles

Selected arrangement: keep both Vertex and EnMaaS and choose explicitly per task.
Both profiles use the existing native Claude configuration directory, plugins,
instructions and local state. No alternate account directory or credential copy
is created. Start a new task/thread when choosing a different provider.

## Launch from a terminal

From the repository, use `bin/claude-vertex` or `bin/claude-enmaas`, followed by
ordinary Claude arguments. To use GLM 5.3 through EnMaaS:

```sh
/Users/dwalczyk/Development/agents-config/bin/claude-enmaas --model rits/zai-org/glm-5-3
```

GLM 5.3 is the selected model for the T3 EnMaaS entry. The terminal command names
its exact gateway ID; no native model default or Sonnet/Opus/Haiku alias mapping
was changed. Earlier Sonnet 4.6 testing was a connectivity probe. The user's
EnMaaS guide identifies `rits/zai-org/glm-5-3` as hosted GLM and documents support
through the Anthropic Messages endpoint used by Claude Code. It also explains
that `/v1/models` can omit hosted models, so this supported ID is pinned locally.

## What the launchers do

1. Read the selected non-secret overlay in `profiles/claude/`.
2. Expand `${NAME}` placeholders in the overlay from the local gitignored
   `.env` (copy `.env.example` to create it); a missing value stops the launch.
3. Merge any `--settings` files/JSON supplied by the caller, including T3's SDK.
4. Apply provider-routing overrides last in both process environment and settings.
5. Run the installed native `claude` executable, preserving stdin/stdout and
   forwarding cancellation signals. Remove the private temporary overlay on exit.

Vertex sets its existing GCP project (ID from `.env`) and global region and
clears gateway URL,
Anthropic credentials and other provider selectors for that process. Google
Application Default Credentials remain local and are used normally.

EnMaaS clears the cloud-provider selectors, sets the gateway endpoint from
`.env`, and reuses
the existing native `ANTHROPIC_API_KEY`. The key is omitted from the profile file.
The original user settings and shell startup files are unchanged. Plain `claude`
therefore retains its old behavior; use a named launcher for predictable routing.

Settings files override shell values in normal Claude sessions. Clearing a stale
selector requires an empty string in the overlay, not simply omitting the key.
See [Anthropic environment precedence](https://code.claude.com/docs/en/env-vars)
and [CLI settings overrides](https://code.claude.com/docs/en/cli-reference).

## T3

The desired T3 picker has three active provider entries:

| Instance | Driver | Executable |
| --- | --- | --- |
| OpenAI / Codex | Existing native Codex provider | Existing configuration |
| Claude | Claude Code Agent SDK | Repository `bin/claude-vertex` |
| EnMaaS | Claude Code Agent SDK | Repository `bin/claude-enmaas` |

The Claude entry uses T3's existing `claudeAgent` instance ID. T3 automatically
creates this default instance when it has no explicit entry; adding two new named
Claude instances without consolidating it produced four picker entries. The extra
`claude-vertex` instance is now explicitly disabled and retained for history
references. `claude-enmaas` keeps its ID and is displayed as `EnMaaS`.
Imported threads and authentication are not removed or reimported.

Chezmoi expands executable paths relative to this repository and merges those
instances into `~/.t3/userdata/settings.json`. When explicitly configuring the
default instance for the first time, the modifier carries forward its existing
legacy provider configuration before applying selected fields. Other settings
and provider entries remain intact. Moving the repository requires reapplying
the T3 configuration.
EnMaaS has one custom entry named GLM 5.3 with that exact model ID. Its capability
descriptors are empty to avoid advertising Claude-specific reasoning, fast-mode
or context controls. No title-generation provider or existing thread is changed.

`config/t3.json` hides the 13 built-in Claude models in T3's current cached catalog
only for `claude-enmaas` and puts GLM first. The client-settings modifier merges
per instance, preserving other providers' preferences. This finite visibility list
should be reviewed when T3 adds models; it is not an automatic future-model filter.

Preview/apply just these T3 entries with:

```sh
./scripts/setup.sh --check --component t3
./scripts/setup.sh --apply --component t3
```

For the first T3 test, start a new local thread in an empty test project, choose
EnMaaS and GLM 5.3, and ask it to reply OK
without using tools. Choose Claude on another new thread for the Vertex test.
The terminal launchers invoke the same native Claude binary used through T3.

The separate EnMaaS entry uses the native Claude agent as its client and retains
that driver's icon. The model is GLM, served by EnMaaS. The built-in Claude
catalog is hidden for this entry; Claude/Vertex and Codex keep their model lists.
Other hosted models require their own supported IDs and capability verification.
The guide states GLM's limits as 1,000,000 context tokens and 65,536 output tokens;
this configuration declares no larger window and adds no model-specific limit
override to other models.

T3 Alpha 0.0.45, installed commit `6c8fed35dded`, was inspected locally. Its Claude
driver supports custom executables and calls the Agent SDK with `extraArgs` for
chat. Its helper text generation has another launch path. Using the named binary
wrappers applies the routing overlay in both paths and preserves SDK settings.
This is why the setup does not rely solely on T3's launch-arguments field.
See the upstream [Claude provider documentation](https://github.com/pingdotgg/t3code/blob/main/docs/user/providers-claude.md).

## Verification

On October 21, 2026:

- EnMaaS `/v1/models` returned HTTP 200 using the existing native credential.
- Vertex completed a tool-free native CLI smoke test using its inherited Sonnet
  4.5 alias. Reported cost: $0.000837.
- EnMaaS rejected that alias before generating tokens, then completed a tool-free
  native CLI test with explicit Sonnet 4.6. Reported cost: $0.000156.
- Hosted GLM 5.3 completed a tool-free native CLI test through the EnMaaS launcher:
  result `OK`, exact model usage `rits/zai-org/glm-5-3`, no CLI error. It used a
  512-token output cap and reported $0.002335; this is a client estimate, not an invoice.
- The smoke tests used empty temporary directories, temporary Claude state, no
  project instructions, no tools or MCP servers, and a $0.05 budget per call.
- Full T3 chat execution remains to be verified; native CLI success alone is not
  proof that the entire T3 conversation flow succeeds.
- The T3-only configuration was applied with a private external snapshot. Both
  provider entries and executable paths are present in native settings. Fingerprints
  confirm that Claude/Codex configuration and shell startup stayed unchanged.
- Computer-control permission was unavailable, so the T3 UI could not be used to
  perform the final chat test. Its installed server code watches external settings
  changes, but persisted entries alone do not prove successful runtime loading.
- The GLM configuration and EnMaaS-only visibility preferences were applied with
  a private backup. Their post-apply preview matches source; projecting the current
  cached catalog through those preferences leaves only GLM visible for EnMaaS.
  Other provider settings/preferences and native credentials were preserved.
- Automatic approval review rejected a renewed T3 computer-use inspection because
  of the earlier permission restriction. No workaround was attempted. The picker
  appearance and full T3 chat remain unverified; native GLM inference passed.

Costs above are values reported by the CLI for these tests, not verified provider
invoices or agreed model prices. Pricing analysis remains a later task.
