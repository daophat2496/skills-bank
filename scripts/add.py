#!/usr/bin/env python3
"""Vendor one skill from a GitHub repo into the bank, pinned to a commit.

    scripts/add.py https://github.com/<owner>/<repo>/tree/<ref>/<path/to/skill> [--provider P] [--name N]

Copies the skill folder unchanged into providers/<P>/skills/<N>, records where it came
from in provider.yaml with status "trial", copies the upstream LICENSE, and prints what
a reviewer should look at. Promote to "approved" by hand after reading it.
"""
import argparse
import datetime
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")
# Worth a human look before approving; not proof of anything bad.
RISKY = re.compile(
    r"curl\s|wget\s|Invoke-WebRequest|\beval\b|base64\s+-d|\brm\s+-rf|"
    r"\$\{?[A-Z_]*(TOKEN|SECRET|KEY|PASSWORD)|ssh\s|chmod\s+\+s|/etc/|~/\.ssh|\.aws/",
)


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--provider", help="defaults to the GitHub owner")
    ap.add_argument("--name", help="defaults to the folder name; use it to resolve a clash")
    a = ap.parse_args()

    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.+?)/?$", a.url)
    if not m:
        sys.exit("expected https://github.com/<owner>/<repo>/tree/<ref>/<path>")
    owner, repo, ref, path = m.groups()
    provider = a.provider or owner.lower()
    name = a.name or Path(path).name
    dest = ROOT / "providers" / provider / "skills" / name
    if dest.exists():
        sys.exit(f"{dest.relative_to(ROOT)} already exists; use scripts/outdated.py to update it")

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        git("init", "-q", cwd=t)
        git("remote", "add", "origin", f"https://github.com/{owner}/{repo}.git", cwd=t)
        git("fetch", "-q", "--depth", "1", "origin", ref, cwd=t)
        git("checkout", "-q", "FETCH_HEAD", cwd=t)
        sha = git("rev-parse", "HEAD", cwd=t)

        src = t / path
        if not (src / "SKILL.md").exists():
            sys.exit(f"no SKILL.md at {path}")
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".git"))

        pdir = dest.parent.parent
        lic = next((t / n for n in LICENSE_NAMES if (t / n).exists()), None)
        lic = lic or next((src / n for n in LICENSE_NAMES if (src / n).exists()), None)
        if lic and not (pdir / "LICENSE").exists():
            shutil.copy(lic, pdir / "LICENSE")

    meta_path = pdir / "provider.yaml"
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {
        "provider": provider,
        "homepage": f"https://github.com/{owner}",
    }
    meta.setdefault("skills", {})[name] = {
        "status": "trial",
        "category": "TODO",
        "tags": [],
        "upstream": {"repo": f"{owner}/{repo}", "ref": sha, "path": path},
        "vendored": datetime.date.today().isoformat(),
        "notes": "",
    }
    meta_path.write_text(yaml.safe_dump(meta, sort_keys=False, allow_unicode=True), encoding="utf-8")

    files = sorted(f for f in dest.rglob("*") if f.is_file())
    print(f"vendored {owner}/{repo}@{sha[:12]}:{path} -> {dest.relative_to(ROOT)}\n")
    print("Review before approving:")
    print(f"  license   {'copied from ' + lic.name if lic else 'NONE FOUND — do not publish without permission'}")
    fm = (dest / "SKILL.md").read_text(encoding="utf-8").split("---")[1]
    for key in ("allowed-tools", "hooks", "disable-model-invocation"):
        if re.search(rf"^{key}:", fm, re.M):
            print(f"  {key:<9} declared in frontmatter — read it")
    for f in files:
        rel = f.relative_to(dest)
        exe = " (executable)" if f.stat().st_mode & 0o111 else ""
        hits = sorted({h.group(0).strip() for h in RISKY.finditer(f.read_text(errors="ignore"))})
        print(f"  {rel}{exe}" + (f"  ⚠ {', '.join(hits)}" if hits else ""))
    print(f"\nNext: set category/tags in {meta_path.relative_to(ROOT)}, then scripts/build.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
