import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SpendAgentTest(unittest.TestCase):
    def setUp(self):
        self.binding = json.loads((ROOT / "agents/spend-analyst.settings.json").read_text())

    def test_binding_is_fail_closed_and_sandboxed(self):
        self.assertEqual(self.binding["permissions"]["defaultMode"], "dontAsk")
        sandbox = self.binding["sandbox"]
        self.assertTrue(sandbox["enabled"])
        self.assertTrue(sandbox["failIfUnavailable"])
        self.assertFalse(sandbox["allowUnsandboxedCommands"])
        self.assertNotIn("bypassPermissions", json.dumps(self.binding))

    def test_binding_denies_irreversible_and_outward_operations(self):
        deny = self.binding["permissions"]["deny"]
        for pattern in (
            "Bash(gh pr merge *)", "Bash(gh pr review *)", "Bash(gh api *)",
            "Bash(git push --force*)", "Bash(git reset --hard *)",
            "Bash(./scripts/setup.sh --apply*)", "Bash(codeburn optimize --apply*)",
            "Bash(codeburn guard*)",
        ):
            self.assertIn(pattern, deny)
        # A broad git allow is acceptable only because deny wins; no denied
        # operation may also appear in the allow list.
        allow = self.binding["permissions"]["allow"]
        self.assertIn("Bash(git *)", allow)
        self.assertFalse(any(
            word in item for item in allow for word in ("merge", "--force", "--apply", "guard")
        ))

    def test_binding_reads_telemetry_and_cannot_write_native_config(self):
        filesystem = self.binding["sandbox"]["filesystem"]
        self.assertIn("/Users/dwalczyk/.claude/projects", filesystem["allowRead"])
        self.assertIn("/Users/dwalczyk/.codex/sessions", filesystem["allowRead"])
        for path in ("/Users/dwalczyk/.claude", "/Users/dwalczyk/.codex", "/Users/dwalczyk/.t3"):
            self.assertIn(path, filesystem["denyWrite"])
        self.assertNotIn("/Users/dwalczyk/Development/agents-config", filesystem["allowWrite"])

    def test_role_and_pipeline_declare_the_required_contract(self):
        role = (ROOT / "agents/spend-analyst.md").read_text()
        skill = (ROOT / "skills/spend-review/SKILL.md").read_text()
        for text in (role, skill):
            self.assertTrue(text.startswith("---\n"))
            frontmatter = text.split("---\n")[1]
            self.assertIn("name:", frontmatter)
            self.assertIn("description:", frontmatter)
        self.assertIn("skills/spend-review/SKILL.md", role)
        for required in (
            "codeburn optimize --format json", "docs/cost-findings.md", "make test",
            "./scripts/setup.sh --check", "gh pr create", "at most three", "rejected",
            "Never run `scripts/setup.sh --apply`", "--draft",
        ):
            self.assertIn(required, skill)

    def test_ledger_declares_terminal_verdicts_and_keeps_stable_ids(self):
        ledger = (ROOT / "docs/cost-findings.md").read_text()
        for verdict in ("`observed`", "`proposed`", "`deferred`", "`accepted`", "`rejected`"):
            self.assertIn(verdict, ledger)
        self.assertIn("`mcp-coverage:t3-code`", ledger)
        self.assertIn("closed without merging", ledger)

    def test_automation_sources_hold_no_credentials_and_claude_dir_is_ignored(self):
        paths = (
            ROOT / "agents/spend-analyst.md",
            ROOT / "agents/spend-analyst.settings.json",
            ROOT / "skills/spend-review/SKILL.md",
            ROOT / "docs/spend-agent.md",
            ROOT / "docs/cost-findings.md",
        )
        pattern = re.compile(r"(sk-ant-|ghp_|github_pat_|AKIA[0-9A-Z]{16})")
        for path in paths:
            self.assertIsNone(pattern.search(path.read_text()), path)
        self.assertIn(".claude/", (ROOT / ".gitignore").read_text().splitlines())


if __name__ == "__main__":
    unittest.main()
