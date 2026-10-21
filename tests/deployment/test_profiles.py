import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ProfileTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="agents-config-profile-test-")
        self.base = Path(self.temporary.name)
        self.binary = self.base / "native-claude"
        self.binary.write_text(f"#!{sys.executable}\n" + '''import json,os,pathlib,stat,sys
args=sys.argv[1:];path=pathlib.Path(args[args.index('--settings')+1])
print(json.dumps({'settings':json.loads(path.read_text()),'path':str(path),
 'mode':stat.S_IMODE(path.stat().st_mode),'args':args,'stdin':sys.stdin.read(),
 'env':{k:os.environ.get(k) for k in ['CLAUDE_CODE_USE_VERTEX','ANTHROPIC_BASE_URL','ANTHROPIC_API_KEY']}}))
''')
        self.binary.chmod(0o755)
        self.env = {**os.environ, "CLAUDE_NATIVE_BINARY": str(self.binary),
                    "CLAUDE_CODE_USE_VERTEX": "1", "ANTHROPIC_BASE_URL": "https://stale.invalid",
                    "ANTHROPIC_API_KEY": "SYNTHETIC_CREDENTIAL"}

    def tearDown(self):
        self.temporary.cleanup()

    def test_provider_overrides_preserve_sdk_settings_protocol_and_local_credentials(self):
        source = self.base / "sdk-settings.json"
        source.write_text(json.dumps({"alwaysThinkingEnabled": False, "env": {"EXTRA": "keep", "CLAUDE_CODE_USE_VERTEX": "stale"}}))
        for profile in ("vertex", "enmaas"):
            with self.subTest(profile=profile):
                result = subprocess.run([str(ROOT / f"bin/claude-{profile}"), "--settings", str(source),
                    '--settings={"showThinkingSummaries":true}', "--input-format", "stream-json"],
                    env=self.env, input='{"type":"user"}\n', text=True, capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                data = json.loads(result.stdout)
                self.assertFalse(data["settings"]["alwaysThinkingEnabled"])
                self.assertTrue(data["settings"]["showThinkingSummaries"])
                self.assertEqual(data["settings"]["env"]["EXTRA"], "keep")
                self.assertEqual(data["args"].count("--settings"), 1)
                self.assertIn("stream-json", data["args"])
                self.assertEqual(data["stdin"], '{"type":"user"}\n')
                self.assertEqual(data["mode"], 0o600)
                self.assertFalse(Path(data["path"]).exists())
                if profile == "vertex":
                    self.assertEqual(data["settings"]["env"]["CLAUDE_CODE_USE_VERTEX"], "1")
                    self.assertEqual(data["env"]["ANTHROPIC_API_KEY"], "")
                    self.assertEqual(data["settings"]["env"]["ANTHROPIC_BASE_URL"], "")
                else:
                    self.assertEqual(data["settings"]["env"]["CLAUDE_CODE_USE_VERTEX"], "")
                    self.assertEqual(data["env"]["ANTHROPIC_API_KEY"], "SYNTHETIC_CREDENTIAL")
                    self.assertNotIn("ANTHROPIC_API_KEY", data["settings"]["env"])

    def test_invalid_settings_fail_without_disclosing_contents(self):
        result = subprocess.run([str(ROOT / "bin/claude-enmaas"), "--settings", '{"secret":"DO_NOT_PRINT'],
                                env=self.env, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("DO_NOT_PRINT", result.stdout + result.stderr)

    def test_provider_defaults_remain_unchanged_and_prompt_separator_is_preserved(self):
        environment = {**self.env, "ANTHROPIC_DEFAULT_SONNET_MODEL": "inherited-model"}
        result = subprocess.run([str(ROOT / "bin/claude-enmaas"), "--", "--settings", "literal prompt"],
                                env=environment, input="", capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["args"][-3:], ["--", "--settings", "literal prompt"])
        self.assertNotIn("model", data["settings"])
        self.assertNotIn("ANTHROPIC_DEFAULT_SONNET_MODEL", data["settings"]["env"])

    def test_cancellation_reaches_native_process_and_cleans_overlay(self):
        marker = self.base / "stopped"
        ready = self.base / "ready"
        self.binary.write_text(f"#!{sys.executable}\n" + f'''import pathlib,signal,sys,time
path=pathlib.Path(sys.argv[sys.argv.index('--settings')+1])
def stop(*_):
 pathlib.Path({str(marker)!r}).write_text(str(path))
 sys.exit(0)
signal.signal(signal.SIGTERM,stop)
pathlib.Path({str(ready)!r}).touch()
while True:time.sleep(0.05)
''')
        process = subprocess.Popen([str(ROOT / "bin/claude-vertex")], env=self.env)
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(ready.exists())
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=5)
            self.assertTrue(marker.exists())
            self.assertFalse(Path(marker.read_text()).exists())
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()


if __name__ == "__main__":
    unittest.main()
