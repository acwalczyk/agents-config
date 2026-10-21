#!/usr/bin/env python3
"""Preview selective chezmoi changes without displaying native configuration."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
MANAGED_HEADER = b"<!-- Managed by agents-config."


def load_json(path):
    return json.loads(path.read_text())


def targets():
    files = [
        ".claude/settings.json", ".claude/CLAUDE.md", ".codex/config.toml",
        ".codex/AGENTS.md", ".codex/skills/review-code-changes/SKILL.md",
    ]
    if load_json(ROOT / "config/t3.json"):
        files.append(".t3/userdata/client-settings.json")
    if load_json(ROOT / "config/t3-providers.json"):
        files.append(".t3/userdata/settings.json")
    if any("claude" in server for server in load_json(ROOT / "shared/mcp.json")["servers"].values()):
        files.append(".claude.json")
    return files


def safe_path(destination, relative):
    path = destination / relative
    for part in (path, *path.parents):
        if part == destination:
            break
        if part.is_symlink():
            raise ValueError(f"Refusing symlink at {relative}; port it explicitly first")
    if path.exists() and not path.is_file():
        raise ValueError(f"Expected a regular file at {relative}")
    return path


def digest(data):
    return None if data is None else hashlib.sha256(data).hexdigest()


def contents(path):
    return path.read_bytes() if path.exists() else None


def parsed(relative, data):
    if relative.endswith(".json"):
        value = json.loads(data or b"{}")
    elif relative.endswith(".toml"):
        value = tomllib.loads((data or b"").decode())
    else:
        return data
    if not isinstance(value, dict):
        raise ValueError("Expected a configuration object")
    return value


def validate_source():
    for agent in ("claude", "codex", "t3"):
        config = load_json(ROOT / f"config/{agent}.json")
        if not isinstance(config, dict):
            raise ValueError(f"config/{agent}.json must be an object")
    allowed = {
        "claude": {"model", "effortLevel", "alwaysThinkingEnabled", "permissions"},
        "codex": {"model", "model_reasoning_effort"},
    }
    for agent, keys in allowed.items():
        if set(load_json(ROOT / f"config/{agent}.json")) - keys:
            raise ValueError(f"Unexpected managed keys in config/{agent}.json")
    plugins = load_json(ROOT / "plugins/manifest.json")
    for agent in ("claude", "codex"):
        for plugin in plugins[agent]:
            if "@" not in plugin or plugin.rsplit("@", 1)[1] not in plugins["marketplaces"]:
                raise ValueError(f"Unknown marketplace in {agent} selection")
    for profile in ("vertex", "enmaas"):
        value = load_json(ROOT / f"profiles/claude/{profile}.json")
        if not isinstance(value.get("env"), dict) or not all(isinstance(v, str) for v in value["env"].values()):
            raise ValueError(f"Invalid {profile} environment")
    for instance in load_json(ROOT / "config/t3-providers.json").values():
        binary = (ROOT / instance["config"]["binaryPath"]).resolve()
        if not binary.is_relative_to(ROOT / "bin") or not binary.is_file():
            raise ValueError("T3 provider binary must be a repository profile launcher")
    tomllib.loads((ROOT / "shared/providers.toml").read_text())


class Deployment:
    def __init__(self, destination, workspace, component="all"):
        self.destination = destination
        self.selected_targets = [name for name in targets() if component == "all" or name.startswith(".t3/")]
        binary = os.environ.get("CHEZMOI") or shutil.which("chezmoi")
        if not binary:
            raise ValueError("chezmoi missing; install with brew install chezmoi, then retry")
        config = workspace / "chezmoi.toml"
        config.touch()
        self.command = [
            binary, "--source", str(ROOT), "--working-tree", str(ROOT),
            "--destination", str(destination), "--config", str(config),
            "--cache", str(workspace / "cache"),
            "--persistent-state", str(workspace / "state.boltdb"), "--no-tty",
        ]

    def run(self, *args):
        result = subprocess.run(self.command + list(args), capture_output=True, timeout=60)
        if result.returncode:
            # Native errors may contain credentials or complete configuration lines.
            raise ValueError("chezmoi operation failed; check source syntax and native file format (output suppressed)")
        return result.stdout

    def preview(self):
        before, after = {}, {}
        managed = set(self.run("managed", "--include", "files").decode().splitlines())
        if managed != set(targets()):
            raise ValueError("Chezmoi file selection differs from the deployment allowlist")
        for relative in self.selected_targets:
            path = safe_path(self.destination, relative)
            before[relative] = contents(path)
            data = before[relative]
            if relative.endswith(("AGENTS.md", "CLAUDE.md")) and data and data.strip() and not data.startswith(MANAGED_HEADER):
                raise ValueError(f"Port existing {relative} instructions before replacing them")
            if relative.endswith("skills/review-code-changes/SKILL.md") and data:
                source = (ROOT / "skills/review-code-changes/SKILL.md").read_bytes()
                if data != source:
                    raise ValueError("Personal review skill differs; reconcile it with skills/ before applying")
            try:
                old = parsed(relative, data)
            except (ValueError, UnicodeError):
                raise ValueError(f"Invalid native format at {relative} (contents suppressed)") from None
            rendered = self.run("cat", str(path))
            try:
                new = parsed(relative, rendered)
            except (ValueError, UnicodeError):
                raise ValueError(f"Invalid rendered format at {relative} (contents suppressed)") from None
            after[relative] = rendered
            print(f"{'UPDATE' if old != new else 'OK    '} {relative}")
        return before, after


def private_write(path, data, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fchmod(stream.fileno(), mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def apply(deployment, before, after, backup_root):
    if not before:
        print("No configuration targets selected. Nothing applied.")
        return
    if backup_root.is_relative_to(ROOT):
        raise ValueError("Backups must be outside the source repository")
    backup_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-"), dir=backup_root))
    records = {}
    for relative, data in before.items():
        path = safe_path(deployment.destination, relative)
        if contents(path) != data:
            raise ValueError(f"{relative} changed during preview; retry with agents closed")
        records[relative] = {"before": digest(data), "mode": stat.S_IMODE(path.stat().st_mode) if data is not None else None}
        if data is not None:
            private_write(backup / relative, data)
            # Every directory holding backups is private, including nested directories.
            for parent in (backup / relative).parents:
                if parent == backup:
                    break
                parent.chmod(0o700)
    manifest = {"destination": str(deployment.destination), "files": records}
    manifest_path = backup / "manifest.json"
    private_write(manifest_path, json.dumps(manifest, indent=2).encode())
    try:
        deployment.run("--force", "apply", "--parent-dirs", *[str(deployment.destination / name) for name in before])
        for relative, expected in after.items():
            actual = contents(deployment.destination / relative)
            if parsed(relative, actual) != parsed(relative, expected):
                raise ValueError(f"Post-apply mismatch at {relative}; backup retained")
    finally:
        for relative, record in records.items():
            record["after"] = digest(contents(deployment.destination / relative))
        private_write(manifest_path, json.dumps(manifest, indent=2).encode())
        print(f"Backup: {backup}")
    print("Configuration applied. Restart agents to reload instructions and plugins.")


def restore(backup, destination):
    manifest = load_json(backup / "manifest.json")
    if manifest["destination"] != str(destination):
        raise ValueError("Backup destination does not match --destination")
    allowed = set(targets()) | {".claude.json", ".t3/userdata/client-settings.json", ".t3/userdata/settings.json"}
    for relative, record in manifest["files"].items():
        if relative not in allowed:
            raise ValueError("Unexpected path in backup manifest")
        path = safe_path(destination, relative)
        if "after" not in record or digest(contents(path)) != record["after"]:
            raise ValueError(f"{relative} changed since apply; reconcile manually before restore")
        if record["before"] is not None and digest(contents(backup / relative)) != record["before"]:
            raise ValueError("Backup contents do not match the manifest")
    for relative, record in manifest["files"].items():
        path = destination / relative
        if record["before"] is None:
            path.unlink(missing_ok=True)
        else:
            private_write(path, (backup / relative).read_bytes(), record["mode"])
    print("Restored configuration snapshot. Native sessions and plugin versions were not restored.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="default: validate and preview; no native writes")
    modes.add_argument("--apply", action="store_true", help="apply after preview and external backup; close agents first")
    modes.add_argument("--restore", type=Path, metavar="BACKUP", help="restore if files have not changed since apply")
    parser.add_argument("--destination", type=Path, default=Path.home())
    parser.add_argument("--backup-root", type=Path, default=Path.home() / ".local/state/agents-config/backups")
    parser.add_argument("--component", choices=("all", "t3"), default="all", help="limit preview/apply to one component")
    args = parser.parse_args()
    destination = args.destination.expanduser().resolve()
    try:
        validate_source()
        if args.restore:
            restore(args.restore.expanduser().resolve(), destination)
            return
        with tempfile.TemporaryDirectory(prefix="agents-config-") as work:
            deployment = Deployment(destination, Path(work), args.component)
            before, after = deployment.preview()
            if args.apply:
                apply(deployment, before, after, args.backup_root.expanduser().resolve())
            else:
                print("Preview only. No native configuration was changed.")
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        # Parser exceptions may embed input values. Do not expose them.
        if isinstance(error, (json.JSONDecodeError, tomllib.TOMLDecodeError)):
            print("ERROR: invalid source syntax (contents suppressed)", file=sys.stderr)
        elif isinstance(error, ValueError):
            print(f"ERROR: {error}", file=sys.stderr)
        else:
            print(f"ERROR: {type(error).__name__}; operation stopped", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
