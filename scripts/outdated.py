#!/usr/bin/env python3
"""Show which vendored skills changed upstream since they were pinned.

    scripts/outdated.py            list skills whose upstream folder changed
    scripts/outdated.py <name>     also print the full diff for that skill

Updating is deliberate: read the diff, then re-vendor with scripts/add.py (after
removing the old folder) and re-review. A new upstream commit is not approved by default.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    found = False
    for meta_path in sorted(ROOT.glob("providers/*/provider.yaml")):
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
        for name, entry in (meta.get("skills") or {}).items():
            up = (entry or {}).get("upstream")
            if not up or (only and name != only):
                continue
            found = True
            with tempfile.TemporaryDirectory() as tmp:
                t = Path(tmp)
                git("init", "-q", cwd=t)
                git("remote", "add", "origin", f"https://github.com/{up['repo']}.git", cwd=t)
                git("fetch", "-q", "--depth", "1", "origin", up["ref"], cwd=t)
                git("fetch", "-q", "--depth", "1", "origin", "HEAD", cwd=t)
                head = git("rev-parse", "FETCH_HEAD", cwd=t).strip()
                stat = git("diff", "--stat", up["ref"], head, "--", up["path"], cwd=t).strip()
                if not stat:
                    print(f"{name}: up to date ({up['ref'][:12]})")
                    continue
                print(f"{name}: CHANGED {up['ref'][:12]} -> {head[:12]}\n{stat}\n")
                if only:
                    print(git("diff", up["ref"], head, "--", up["path"], cwd=t))
    if not found:
        print("no vendored skills" + (f" named {only}" if only else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
