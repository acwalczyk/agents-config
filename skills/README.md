# Personal skills

Keep existing native and repository skills in place. A plugin being installed
does not guarantee a skill is applicable or loaded in every task. Use its
explicit invocation when predictable selection matters.

- `review-code-changes/` is the existing personal skill, copied unchanged and
  deployed to its current Codex location. Divergence blocks deployment.
- `spend-review/` is the unattended cost-review pipeline. It is not deployed to
  another agent; it runs from the dedicated spend checkout and edits this
  repository. See [Spend review agent](../docs/spend-agent.md).

Discover selected team plugins with `scripts/doctor.sh`.
