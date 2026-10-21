#!/usr/bin/env python3
"""Read-only local inventory; no provider requests or token usage."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import tomllib

from manage import ROOT, load_json, validate_source


def version(command):
    executable = shutil.which(command)
    if not executable:
        return "missing"
    try:
        result = subprocess.run([executable, "--version"], capture_output=True, text=True, timeout=10)
        return result.stdout.strip().splitlines()[0] if result.returncode == 0 else "version unavailable"
    except (OSError, subprocess.TimeoutExpired):
        return "version unavailable"


def read_config(path):
    if not path.exists():
        return {}
    try:
        data = path.read_text()
        value = tomllib.loads(data) if path.suffix == ".toml" else json.loads(data)
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except (ValueError, OSError):
        print(f"WARN invalid/unreadable {path.name}; contents suppressed")
        return {}


def inventory(home):
    manifest = load_json(ROOT / "plugins/manifest.json")
    records = {}
    for agent in ("claude", "codex"):
        base = home / f".{agent}"
        config = read_config(base / ("settings.json" if agent == "claude" else "config.toml"))
        installed = read_config(base / "plugins/installed_plugins.json").get("plugins", {})
        for selector in manifest[agent]:
            name, market = selector.rsplit("@", 1)
            cache = base / "plugins/cache" / market / name
            cached = sorted(p.name for p in cache.iterdir() if p.is_dir()) if cache.is_dir() else []
            enabled = config.get("enabledPlugins", {}).get(selector) if agent == "claude" else config.get("plugins", {}).get(selector, {}).get("enabled")
            registered = [item.get("version", "unknown") for item in installed.get(selector, [])]
            records[f"{agent}:{selector}"] = {"enabled": bool(enabled), "registered_versions": registered, "cached_versions": cached}
            print(f"{agent:6} {selector}: enabled={bool(enabled)} registered={','.join(registered) or 'unverified'} cached={','.join(cached) or 'missing'}")
        if agent == "codex" and config.get("plugins", {}).get("jira@personal", {}).get("enabled") and config.get("plugins", {}).get("jira@ai-helpers", {}).get("enabled"):
            print("WARN Codex enables two Jira plugin sources; choose one before deduplicating")
        for directory in (base / "skills", home / ".agents/skills" if agent == "codex" else base / "commands"):
            if directory.is_dir():
                entries = sorted(p.name for p in directory.iterdir() if not p.name.startswith("."))
                print(f"DISCOVERY {directory}: {', '.join(entries) or 'empty'}")
    claude = read_config(home / ".claude/settings.json")
    t3 = read_config(home / ".t3/userdata/settings.json")
    for instance_id in load_json(ROOT / "config/t3-providers.json"):
        instance = t3.get("providerInstances", {}).get(instance_id)
        binary = Path(instance.get("config", {}).get("binaryPath", "")) if instance else None
        print(f"T3 {instance_id}: configured={instance is not None} launcher_present={bool(binary and binary.is_file())}")
    vertex = home / ".config/claude-code-vertex/env.sh"
    if claude.get("env", {}).get("ANTHROPIC_BASE_URL") and vertex.exists() and "CLAUDE_CODE_USE_VERTEX=1" in vertex.read_text():
        print("WARN Claude has a settings endpoint plus a Vertex shell loader; effective routing requires verification")
    for label, path in {
        "Claude settings": home / ".claude/settings.json",
        "Codex authentication": home / ".codex/auth.json",
        "T3 authentication": home / ".t3/userdata/clerk-tokens.json",
    }.items():
        print(f"LOCAL {label}: {'present' if path.exists() else 'absent'} (never exported)")
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--project", type=Path, help="inspect one project, without recursive repository scans")
    parser.add_argument("--record", action="store_true", help="write observed versions.lock.json to this repository")
    args = parser.parse_args()
    validate_source()
    versions = {name: version(name) for name in ("claude", "codex", "chezmoi", "uv", "gh", "python3")}
    t3 = Path("/Applications/T3 Code (Alpha).app/Contents/Info.plist")
    if t3.exists():
        with t3.open("rb") as stream:
            versions["t3_desktop"] = plistlib.load(stream).get("CFBundleShortVersionString", "unknown")
    print("Source: valid. Native provider connectivity and skill invocation have not been tested.")
    for name, value in versions.items():
        print(f"TOOL {name}: {value}")
    records = inventory(args.home.expanduser())
    if args.project:
        project = args.project.expanduser().resolve()
        for relative in ("AGENTS.md", "CLAUDE.md", ".agents/skills", ".claude/skills"):
            path = project / relative
            print(f"PROJECT {relative}: {'present' if path.exists() else 'absent'}")
            if path.is_dir():
                for entry in sorted(path.glob("*/SKILL.md")):
                    print(f"  {entry.parent.name}")
    if args.record:
        record = {
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "kind": "observations; not a binary/plugin resolution lock",
            "deployment_tested_with": {"chezmoi": "2.73.3", "minimum_python": "3.11"},
            "tools": versions, "selected_plugins": records,
        }
        (ROOT / "versions.lock.json").write_text(json.dumps(record, indent=2) + "\n")
        print("Wrote versions.lock.json. Review and commit it if desired.")


if __name__ == "__main__":
    main()
