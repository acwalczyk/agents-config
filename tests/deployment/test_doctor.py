import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("agents_config_doctor", ROOT / "scripts/doctor.py")
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)
CANARY = "DOCTOR_CANARY_DO_NOT_PRINT"


class DoctorTest(unittest.TestCase):
    def run_check(self, rows=None, returncode=0, stdout=None, error=None):
        result = subprocess.CompletedProcess([], returncode, stdout if stdout is not None else json.dumps(rows), CANARY)
        output = io.StringIO()
        with patch.object(doctor, "load_json", return_value={"claude": ["go@team", "bundle@team"]}), \
                patch.object(doctor.subprocess, "run", return_value=result, side_effect=error) as run, \
                contextlib.redirect_stdout(output):
            checked = doctor.check_claude_plugins(Path("/temporary/home"), Path("/temporary/project"))
        self.assertNotIn(CANARY, output.getvalue())
        self.assertEqual(run.call_args.args[0], ["claude", "plugin", "list", "--json"])
        self.assertEqual(run.call_args.kwargs["cwd"], Path("/temporary/project"))
        self.assertEqual(run.call_args.kwargs["env"]["CLAUDE_CONFIG_DIR"], "/temporary/home/.claude")
        return checked

    def test_enabled_flags_do_not_hide_load_errors_or_missing_plugins(self):
        for bundle in [None, {"enabled": False}, {"enabled": True, "errors": [CANARY]},
                       {"enabled": True, "errorDetails": [{"type": "dependency-unsatisfied", "dependency": CANARY}]}]:
            with self.subTest(bundle=bundle):
                rows = [{"id": "go@team", "enabled": True}]
                if bundle is not None:
                    rows.append({"id": "bundle@team", **bundle})
                checked = self.run_check(rows)
                self.assertEqual(checked["status"], "failed")
                self.assertEqual(checked["selected_plugins"]["go@team"]["status"], "ok")
                self.assertNotIn(CANARY, json.dumps(checked))

    def test_success_ignores_unselected_plugin_failures(self):
        rows = [{"id": name, "enabled": True} for name in ["go@team", "bundle@team"]]
        rows.append({"id": "unselected@team", "errors": [CANARY]})
        self.assertEqual(self.run_check(rows)["status"], "ok")

    def test_failed_or_malformed_native_output_is_unverified_and_redacted(self):
        cases = [{"returncode": 1, "stdout": CANARY}, {"stdout": CANARY},
                 {"stdout": "{}"}, {"stdout": "[null]"}, {"error": FileNotFoundError(CANARY)},
                 {"error": subprocess.TimeoutExpired("claude", 30, output=CANARY)}]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs):
                self.assertEqual(self.run_check(**kwargs), {"status": "unverified"})
