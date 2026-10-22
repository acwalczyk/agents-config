import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[2]
CHEZMOI = os.environ.get("CHEZMOI") or shutil.which("chezmoi")
CANARY = "CANARY_NOT_A_REAL_KEY_DO_NOT_PRINT"


class DeploymentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not CHEZMOI:
            raise RuntimeError("Real chezmoi is required; set CHEZMOI=/path/to/chezmoi")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="agents-config-test-")
        self.base = Path(self.temporary.name)
        self.repo = self.base / "source"
        shutil.copytree(ROOT, self.repo, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        self.home = self.base / "home"
        self.home.mkdir()
        self.backups = self.base / "backups"

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, relative, data):
        path = self.home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data if isinstance(data, str) else json.dumps(data))
        return path

    def run_setup(self, *args, success=True):
        result = subprocess.run([
            sys.executable, str(self.repo / "scripts/manage.py"),
            "--destination", str(self.home), "--backup-root", str(self.backups), *args,
        ], env={**os.environ, "CHEZMOI": str(CHEZMOI)}, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        self.assertNotIn(CANARY, result.stdout + result.stderr)
        return result

    def snapshot(self):
        return {str(p.relative_to(self.home)): (p.read_bytes(), stat.S_IMODE(p.stat().st_mode)) for p in self.home.rglob("*") if p.is_file()}

    def test_selective_apply_preserves_native_state_idempotent_and_restorable(self):
        self.write(".claude/settings.json", {
            "model": "old", "env": {"ANTHROPIC_API_KEY": CANARY},
            "permissions": {"allow": ["Read(src/**)"], "deny": ["Read(extra/**)"]},
            "enabledPlugins": {"other@private": True}, "unknown": {"future": 1},
        })
        self.write(".codex/config.toml", f'''model = "old"
[memories]
use_memories = true
[mcp_servers.native]
command = "native-server"
[mcp_servers.native.env]
SECRET_TOKEN = "{CANARY}"
[plugins."jira@personal"]
enabled = true
[plugins."golang@ai-helpers"]
enabled = false
extra = "preserve"
[future]
value = 42
''')
        self.write(".codex/auth.json", {"OPENAI_API_KEY": CANARY})
        self.write(".t3/userdata/client-settings.json", {"futurePreference": True})
        self.write(".t3/userdata/state.sqlite", "native database placeholder")
        self.write(".codex/AGENTS.md", "")
        before = self.snapshot()
        self.run_setup("--check")
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.backups.exists())
        self.run_setup("--apply")
        claude = json.loads((self.home / ".claude/settings.json").read_text())
        codex = tomllib.loads((self.home / ".codex/config.toml").read_text())
        self.assertEqual(claude["env"]["ANTHROPIC_API_KEY"], CANARY)
        self.assertEqual(claude["permissions"]["allow"], ["Read(src/**)"])
        self.assertIn("Read(extra/**)", claude["permissions"]["deny"])
        self.assertEqual(claude["unknown"], {"future": 1})
        self.assertTrue(claude["enabledPlugins"]["other@private"])
        self.assertFalse(codex["plugins"]["jira@personal"]["enabled"])
        self.assertEqual(codex["plugins"]["golang@ai-helpers"]["extra"], "preserve")
        self.assertTrue(codex["memories"]["use_memories"])
        self.assertEqual(codex["future"]["value"], 42)
        self.assertEqual(codex["mcp_servers"]["native"]["env"]["SECRET_TOKEN"], CANARY)
        for name in (".codex/auth.json", ".t3/userdata/state.sqlite"):
            self.assertEqual(self.snapshot()[name], before[name])
        self.assertTrue(json.loads((self.home / ".t3/userdata/client-settings.json").read_text())["futurePreference"])
        self.assertEqual(stat.S_IMODE((self.home / ".claude/settings.json").stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((self.home / ".codex/config.toml").stat().st_mode), 0o600)
        applied = self.snapshot()
        self.run_setup("--apply")
        self.assertEqual(self.snapshot(), applied)
        first = sorted(self.backups.iterdir(), key=lambda p: p.stat().st_mtime_ns)[0]
        self.assertEqual(stat.S_IMODE(first.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((first / ".claude/settings.json").stat().st_mode), 0o600)
        self.run_setup("--restore", str(first))
        self.assertEqual(self.snapshot(), before)

    def test_fresh_machine_and_restore_conflict(self):
        self.run_setup("--apply")
        codex = tomllib.loads((self.home / ".codex/config.toml").read_text())
        self.assertNotIn("jira@personal", codex["plugins"])
        self.assertTrue((self.home / ".t3/userdata/settings.json").exists())
        self.assertTrue((self.home / ".t3/userdata/client-settings.json").exists())
        self.assertFalse((self.home / ".claude.json").exists())
        skill = self.home / ".codex/skills/review-code-changes/SKILL.md"
        self.assertEqual(skill.read_bytes(), (self.repo / "skills/review-code-changes/SKILL.md").read_bytes())
        backup = next(self.backups.iterdir())
        self.write(".codex/AGENTS.md", "appended local instruction")
        state = self.snapshot()
        self.run_setup("--restore", str(backup), success=False)
        self.assertEqual(self.snapshot(), state)

    def test_invalid_native_file_fails_without_leaking_or_writing(self):
        for relative, data in (
            (".claude/settings.json", '{"secret": "' + CANARY),
            (".codex/config.toml", 'secret = "' + CANARY),
        ):
            with self.subTest(relative=relative):
                self.write(relative, data)
                before = self.snapshot()
                self.run_setup("--apply", success=False)
                self.assertEqual(before, self.snapshot())
                (self.home / relative).unlink()

    def test_symlinks_and_unported_instructions_fail_closed(self):
        external = self.base / "external"
        external.mkdir()
        (self.home / ".claude").symlink_to(external, target_is_directory=True)
        self.run_setup("--apply", success=False)
        self.assertEqual(list(external.iterdir()), [])
        (self.home / ".claude").unlink()
        self.write(".claude/CLAUDE.md", "Existing important instructions")
        before = self.snapshot()
        self.run_setup("--apply", success=False)
        self.assertEqual(before, self.snapshot())

    def test_t3_component_preserves_other_instances_without_applying_other_tools(self):
        other_preferences = {"hiddenModels": ["keep-hidden"], "modelOrder": ["keep-first"]}
        self.write(".t3/userdata/client-settings.json", {
            "futurePreference": CANARY,
            "providerModelPreferences": {
                "codex": other_preferences,
                "claudeAgent": {"hiddenModels": ["keep-hidden"], "modelOrder": ["keep-first"], "future": True},
                "claude-enmaas": {"hiddenModels": [], "modelOrder": [], "future": True},
            },
        })
        self.write(".t3/userdata/settings.json", {
            "providers": {"codex": {"enabled": True}},
            "providerInstances": {
                "existing": {"driver": "codex", "displayName": "Keep"},
                "claude-vertex": {"driver": "claudeAgent", "config": {"customModels": ["keep"]}},
            },
            "futureSetting": {"secret": CANARY},
        })
        self.run_setup("--apply", "--component", "t3")
        value = json.loads((self.home / ".t3/userdata/settings.json").read_text())
        self.assertTrue(value["providers"]["codex"]["enabled"])
        self.assertEqual(value["providerInstances"]["existing"]["displayName"], "Keep")
        self.assertEqual(value["providerInstances"]["claude-vertex"]["config"]["customModels"], ["keep"])
        self.assertEqual(value["futureSetting"]["secret"], CANARY)
        for instance_id, profile in (("claude-vertex", "vertex"), ("claude-enmaas", "enmaas"),
                                     ("claude-enmaas-anthropic", "enmaas")):
            item = value["providerInstances"][instance_id]
            self.assertEqual(item["driver"], "claudeAgent")
            self.assertEqual(item["config"]["binaryPath"], str((self.repo / f"bin/claude-{profile}").resolve()))
        self.assertEqual(value["providerInstances"]["claude-enmaas"]["displayName"], "Claude via EnMaaS")
        self.assertFalse(value["providerInstances"]["claude-enmaas-anthropic"]["enabled"])
        custom = value["providerInstances"]["claude-enmaas"]["config"]["customModels"]
        self.assertEqual(custom, [
            {"slug": "rits/zai-org/glm-5-3", "name": "GLM 5.3 (EnMaaS)",
             "capabilities": {"optionDescriptors": []}},
            {"slug": "rits/deepseek-ai/DeepSeek-V4.1-Flash-1017", "name": "DeepSeek V4.1 Flash (EnMaaS)",
             "capabilities": {"optionDescriptors": []}},
        ])
        client = json.loads((self.home / ".t3/userdata/client-settings.json").read_text())
        self.assertEqual(client["futurePreference"], CANARY)
        self.assertEqual(client["providerModelPreferences"]["codex"], other_preferences)
        # Only models the route cannot serve are hidden; everything else shows,
        # current first and legacy after, as T3 groups it from its manifest.
        current = ("claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5")
        default = client["providerModelPreferences"]["claudeAgent"]
        self.assertTrue(default["future"])
        self.assertEqual(default["modelOrder"], [])
        self.assertIn("claude-haiku-5-5", default["hiddenModels"])
        self.assertIn("claude-fable-5-1", default["hiddenModels"])
        for model in ("claude-opus-5-5", "claude-sonnet-5-5", "claude-opus-4-8", "claude-sonnet-4-6",
                      "claude-haiku-4-5"):
            self.assertNotIn(model, default["hiddenModels"])
        enmaas = client["providerModelPreferences"]["claude-enmaas"]
        self.assertTrue(enmaas["future"])
        self.assertEqual(enmaas["modelOrder"], [])
        self.assertIn("claude-fable-5-1", enmaas["hiddenModels"])
        for model in current + ("claude-opus-5", "claude-sonnet-4-6"):
            self.assertNotIn(model, enmaas["hiddenModels"])
        retired = client["providerModelPreferences"]["claude-enmaas-anthropic"]
        self.assertEqual(retired["hiddenModels"], [])
        self.assertFalse((self.home / ".claude").exists())
        self.assertFalse((self.home / ".codex").exists())

    def test_empty_t3_component_does_not_apply_other_configuration(self):
        (self.repo / "config/t3-providers.json").write_text("{}")
        (self.repo / "config/t3.json").write_text("{}")
        self.run_setup("--apply", "--component", "t3")
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertFalse(self.backups.exists())

    def test_t3_reuses_default_claude_and_preserves_imported_configuration(self):
        self.write(".t3/userdata/settings.json", {
            "providers": {
                "codex": {"enabled": True, "homePath": "keep-codex-home"},
                "claudeAgent": {"enabled": False, "homePath": "keep-claude-home",
                                "launchArgs": "--keep", "customModels": ["keep-model"]},
            },
            "providerInstances": {"claude-vertex": {"driver": "claudeAgent", "enabled": True}},
        })
        history = self.write(".t3/userdata/state.sqlite", "imported history placeholder")
        self.run_setup("--apply", "--component", "t3")
        value = json.loads((self.home / ".t3/userdata/settings.json").read_text())
        instances = value["providerInstances"]
        claude = instances["claudeAgent"]
        self.assertEqual(claude["displayName"], "Claude")
        self.assertTrue(claude["enabled"])
        self.assertNotIn("enabled", claude["config"])
        self.assertEqual(claude["config"]["homePath"], "keep-claude-home")
        self.assertEqual(claude["config"]["launchArgs"], "--keep")
        self.assertEqual(claude["config"]["customModels"], ["keep-model"])
        self.assertEqual(claude["config"]["binaryPath"], str((self.repo / "bin/claude-vertex").resolve()))
        self.assertEqual(value["providers"]["codex"]["homePath"], "keep-codex-home")
        self.assertNotIn("binaryPath", value["providers"]["claudeAgent"])
        self.assertFalse(value["providers"]["claudeAgent"]["enabled"])
        self.assertEqual(instances["claude-enmaas"]["displayName"], "Claude via EnMaaS")
        self.assertTrue(instances["claude-enmaas"]["enabled"])
        self.assertFalse(instances["claude-enmaas-anthropic"]["enabled"])
        self.assertEqual(instances["claude-enmaas-anthropic"]["config"]["binaryPath"],
                         str((self.repo / "bin/claude-enmaas").resolve()))
        self.assertFalse(instances["claude-vertex"]["enabled"])
        self.assertEqual(history.read_text(), "imported history placeholder")
        before = self.snapshot()
        self.run_setup("--apply", "--component", "t3")
        self.assertEqual(self.snapshot(), before)

    def test_plugin_component_disables_legacy_without_replacing_instructions_or_cache(self):
        self.write(".claude/CLAUDE.md", "Existing global Claude instructions")
        self.write(".codex/AGENTS.md", "Existing global Codex instructions")
        self.write(".codex/config.toml", 'model = "keep-codex-model"\n[plugins."jira@personal"]\nenabled = true\n')
        self.write(".claude/settings.json", {"model": "keep-claude-model", "permissions": {"deny": ["Read(private/**)"]}})
        (self.repo / "shared/mcp.json").write_text(json.dumps({"servers": {"new-server": {"codex": {"command": "not-yet-selected"}}}}))
        cache = self.write(".codex/plugins/cache/personal/jira/0.9.1/keep.txt", "rollback cache")
        self.run_setup("--apply", "--component", "plugins")
        value = tomllib.loads((self.home / ".codex/config.toml").read_text())
        self.assertFalse(value["plugins"]["jira@personal"]["enabled"])
        self.assertTrue(value["plugins"]["jira@ai-helpers"]["enabled"])
        self.assertEqual(value["model"], "keep-codex-model")
        self.assertNotIn("mcp_servers", value)
        claude = json.loads((self.home / ".claude/settings.json").read_text())
        self.assertEqual(claude["model"], "keep-claude-model")
        self.assertEqual(claude["permissions"]["deny"], ["Read(private/**)"])
        self.assertEqual((self.home / ".claude/CLAUDE.md").read_text(), "Existing global Claude instructions")
        self.assertEqual((self.home / ".codex/AGENTS.md").read_text(), "Existing global Codex instructions")
        self.assertEqual(cache.read_text(), "rollback cache")
        self.assertFalse((self.home / ".t3").exists())

    def test_optional_mcp_and_t3_preserve_other_fields(self):
        (self.repo / "shared/mcp.json").write_text(json.dumps({"servers": {"demo": {
            "claude": {"command": "demo-server", "args": ["--stdio"]},
            "codex": {"command": "demo-server", "args": ["--stdio"]},
        }}}))
        (self.repo / "config/t3.json").write_text('{"terminalLinksRequireModifierClick": true}')
        self.write(".claude.json", {"projects": {"keep": True}, "mcpServers": {"native": {"command": "existing"}}})
        self.write(".t3/userdata/client-settings.json", {"other": "keep"})
        self.run_setup("--apply")
        claude = json.loads((self.home / ".claude.json").read_text())
        codex = tomllib.loads((self.home / ".codex/config.toml").read_text())
        self.assertEqual(claude["projects"], {"keep": True})
        self.assertEqual(claude["mcpServers"]["native"]["command"], "existing")
        self.assertEqual(claude["mcpServers"]["demo"], codex["mcp_servers"]["demo"])
        self.assertEqual(json.loads((self.home / ".t3/userdata/client-settings.json").read_text()), {"other": "keep", "terminalLinksRequireModifierClick": True})

    def test_update_is_a_plan_by_default_and_never_runs_agents(self):
        bindir = self.base / "bin"
        bindir.mkdir()
        sentinel = self.base / "executed"
        for agent in ("claude", "codex"):
            path = bindir / agent
            path.write_text(f'#!/bin/sh\ntouch "{sentinel}"\nexit 1\n')
            path.chmod(0o755)
        result = subprocess.run([sys.executable, str(self.repo / "scripts/update.py")],
                                env={**os.environ, "HOME": str(self.home), "PATH": str(bindir)},
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Plan only", result.stdout)
        self.assertFalse(sentinel.exists())

    def test_claude_update_checks_loading_after_successful_install_commands(self):
        bindir = self.base / "bin"
        bindir.mkdir()
        rows_file = self.base / "native-plugins.json"
        sentinel = self.base / "checked"
        native = bindir / "claude"
        native.write_text(f'''#!{sys.executable}
import pathlib, sys
if sys.argv[1:] == ["plugin", "list", "--json"]:
    pathlib.Path({str(sentinel)!r}).touch()
    print(pathlib.Path({str(rows_file)!r}).read_text())
''')
        native.chmod(0o755)
        selected = json.loads((self.repo / "plugins/manifest.json").read_text())["claude"]
        rows = [{"id": name, "enabled": True} for name in selected]
        for failed in (False, True):
            with self.subTest(failed=failed):
                rows[0]["errors"] = [CANARY] if failed else []
                rows_file.write_text(json.dumps(rows))
                result = subprocess.run([
                    sys.executable, str(self.repo / "scripts/update.py"), "--agent", "claude", "--apply",
                ], env={**os.environ, "HOME": str(self.home), "PATH": str(bindir)},
                    capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 1 if failed else 0, result.stdout + result.stderr)
                self.assertTrue(sentinel.exists())
                self.assertNotIn(CANARY, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
