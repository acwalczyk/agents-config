#!/usr/bin/env python3
"""Read-only local inventory; no provider requests or token usage."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import tomllib

from manage import ROOT, load_json, validate_source


def check_claude_plugins(home, project):
    selected = load_json(ROOT / "plugins/manifest.json")["claude"]
    try:
        result = subprocess.run(
            ["claude", "plugin", "list", "--json"], cwd=project,
            env={**os.environ, "CLAUDE_CONFIG_DIR": str(home / ".claude")},
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode:
            raise ValueError()
        plugins = json.loads(result.stdout)
        if not isinstance(plugins, list) or any(not isinstance(p, dict) for p in plugins):
            raise ValueError()
    except (OSError, subprocess.TimeoutExpired, ValueError):
        print("WARN native Claude plugin check unavailable; command output suppressed")
        return {"status": "unverified"}
    checks = {}
    for selector in selected:
        entries = [p for p in plugins if p.get("id") == selector]
        errors = any(p.get("errors") or p.get("errorDetails") for p in entries)
        enabled = bool(entries) and all(p.get("enabled") is True for p in entries)
        status = "ok" if enabled and not errors else "failed"
        checks[selector] = {"status": status}
        print(f"NATIVE Claude {selector}: {status}")
    return {
        "status": "ok" if all(p["status"] == "ok" for p in checks.values()) else "failed",
        "project": str(project), "selected_plugins": checks,
    }


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
        for selector in manifest[agent] + manifest.get("disabled", {}).get(agent, []):
            name, market = selector.rsplit("@", 1)
            cache = base / "plugins/cache" / market / name
            cached = sorted(p.name for p in cache.iterdir() if p.is_dir()) if cache.is_dir() else []
            enabled = config.get("enabledPlugins", {}).get(selector) if agent == "claude" else config.get("plugins", {}).get(selector, {}).get("enabled")
            registered = [item.get("version", "unknown") for item in installed.get(selector, [])]
            desired_enabled = selector in manifest[agent]
            records[f"{agent}:{selector}"] = {
                "enabled": bool(enabled), "desired_enabled": desired_enabled,
                "registered_versions": registered, "cached_versions": cached,
                "registered_scopes": [{"scope": item.get("scope"), "version": item.get("version")}
                                      for item in installed.get(selector, [])],
            }
            print(f"{agent:6} {selector}: enabled={bool(enabled)} registered={','.join(registered) or 'unverified'} cached={','.join(cached) or 'missing'}")
            if bool(enabled) != desired_enabled:
                print(f"WARN {agent} {selector} differs from the desired enabled={desired_enabled} selection")
            user_versions = {item.get("version") for item in installed.get(selector, []) if item.get("scope") == "user"}
            for item in installed.get(selector, []):
                if item.get("scope") != "user" and user_versions and item.get("version") not in user_versions:
                    print(f"WARN {agent} {selector}: retained {item.get('scope')} version {item.get('version')} at {item.get('projectPath', 'unknown project')}")
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
    parser.add_argument("--check-claude-plugins", action="store_true", help="check native Claude plugin resolution; no inference or MCP calls")
    args = parser.parse_args()
    project = args.project.expanduser().resolve() if args.project else ROOT
    if not project.is_dir():
        parser.error("--project must name an existing directory")
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
    native_check = check_claude_plugins(args.home.expanduser().resolve(), project) if args.check_claude_plugins else None
    if args.project:
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
        if native_check is not None:
            record["native_claude_plugin_check"] = native_check
        (ROOT / "versions.lock.json").write_text(json.dumps(record, indent=2) + "\n")
        print("Wrote versions.lock.json. Review and commit it if desired.")
    return 1 if native_check is not None and native_check["status"] != "ok" else 0


if __name__ == "__main__":
    raise SystemExit(main())
