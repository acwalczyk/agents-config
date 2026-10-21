#!/usr/bin/env python3
"""Plan native plugin updates; --apply --agent is required to execute them."""

import argparse
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tomllib

from manage import ROOT, load_json, validate_source


def commands(agent):
    manifest = load_json(ROOT / "plugins/manifest.json")
    home = Path.home()
    if agent == "claude":
        path = home / ".claude/plugins/known_marketplaces.json"
        existing = json.loads(path.read_text()) if path.exists() else {}
        path = home / ".claude/plugins/installed_plugins.json"
        installed = json.loads(path.read_text()).get("plugins", {}) if path.exists() else {}
    else:
        path = home / ".codex/config.toml"
        existing = tomllib.loads(path.read_text()).get("marketplaces", {}) if path.exists() else {}
    for market, source in manifest["marketplaces"].items():
        if market not in existing:
            yield [agent, "plugin", "marketplace", "add", source]
        yield [agent, "plugin", "marketplace", "update" if agent == "claude" else "upgrade", market]
    for selector in manifest[agent]:
        if agent == "claude":
            is_user_install = any(item.get("scope") == "user" for item in installed.get(selector, []))
            yield [agent, "plugin", "update" if is_user_install else "install", "--scope", "user", selector]
        else:
            yield [agent, "plugin", "add", selector]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", choices=("claude", "codex"))
    parser.add_argument("--apply", action="store_true", help="run native installers; may download and execute plugin installation hooks")
    args = parser.parse_args()
    if args.apply and not args.agent:
        parser.error("--apply requires an explicit --agent")
    validate_source()
    for agent in ([args.agent] if args.agent else ["claude", "codex"]):
        plan = list(commands(agent))
        for command in plan:
            print(shlex.join(command), flush=True)
        if args.apply:
            if not shutil.which(agent):
                sys.exit(f"{agent} is missing")
            for command in plan:
                # Keep native confirmation prompts; never accept arbitrary install hooks.
                result = subprocess.run(command, cwd=ROOT)
                if result.returncode:
                    sys.exit("Native update stopped. Earlier operations may have succeeded; inspect before retrying.")
    if args.apply:
        print("Restart the agent, run doctor.sh --record, then review the changed version observations.")
    else:
        print("Plan only. No plugins or marketplace snapshots were changed.")
    print("Bundled app plugins and jira@personal are preserved and excluded from this updater.")
    print("Codex uses marketplace upgrade plus plugin add; there is no plugin-update command in CLI 0.163.0.")


if __name__ == "__main__":
    main()
