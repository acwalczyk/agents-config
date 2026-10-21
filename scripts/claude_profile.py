#!/usr/bin/env python3
"""Run the native Claude executable with an explicit provider for this process."""

import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def merge(base, overlay):
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base


def settings_arguments(arguments):
    """Keep SDK settings while giving the chosen provider final precedence."""
    remaining, settings = [], {}
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--":
            remaining.extend(arguments[index:])
            break
        if argument == "--settings":
            index += 1
            if index == len(arguments):
                raise ValueError("--settings requires a value")
            value = arguments[index]
        elif argument.startswith("--settings="):
            value = argument.partition("=")[2]
        else:
            remaining.append(argument)
            index += 1
            continue
        data = json.loads(value) if value.lstrip().startswith("{") else json.loads(Path(value).read_text())
        if not isinstance(data, dict):
            raise ValueError("Settings must be a JSON object")
        merge(settings, data)
        index += 1
    return remaining, settings


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("vertex", "enmaas"):
        sys.exit("Usage: claude_profile.py {vertex|enmaas} [native Claude arguments]")
    profile = sys.argv[1]
    try:
        arguments, settings = settings_arguments(sys.argv[2:])
        overlay = json.loads((ROOT / f"profiles/claude/{profile}.json").read_text())
        merge(settings, overlay)
        environment = dict(os.environ)
        environment.update(overlay["env"])
        binary = os.environ.get("CLAUDE_NATIVE_BINARY") or shutil.which("claude")
        if not binary or Path(binary).resolve() in {(ROOT / "bin/claude-vertex").resolve(), (ROOT / "bin/claude-enmaas").resolve()}:
            raise ValueError("Native Claude binary missing or points back to a profile launcher")
        with tempfile.TemporaryDirectory(prefix=f"agents-config-{profile}-") as directory:
            path = Path(directory) / "settings.json"
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w") as stream:
                json.dump(settings, stream)
            # Put options before -- so an explicit prompt separator remains intact.
            child = subprocess.Popen([binary, "--settings", str(path), *arguments], env=environment)
            def forward(signum, _frame):
                if child.poll() is None:
                    try:
                        child.send_signal(signum)
                    except ProcessLookupError:
                        pass
            for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
                signal.signal(signum, forward)
            result = child.wait()
        sys.exit(result if result >= 0 else 128 - result)
    except (OSError, ValueError):
        sys.exit("Claude profile launch failed: check native binary, profile JSON and --settings inputs (contents suppressed)")


if __name__ == "__main__":
    main()
