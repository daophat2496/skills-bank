#!/usr/bin/env python3
"""Package skills as ZIPs for upload at claude.ai (Customize > Skills > Upload skill).

    scripts/zip.py              every skill claude.ai accepts
    scripts/zip.py <name> ...   only these

Output goes to dist/. Skills that only work in Claude Code (hooks, other frontmatter keys
claude.ai rejects, or compatibility: "Claude Code only") are skipped.
"""
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))["skills"]
    wanted = set(sys.argv[1:])
    unknown = wanted - {s["name"] for s in catalog}
    if unknown:
        sys.exit(f"unknown skill(s): {', '.join(sorted(unknown))}")
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    for s in catalog:
        if wanted and s["name"] not in wanted:
            continue
        if not s["claude_ai"]:
            print(f"skip {s['name']}: Claude Code only (hooks, unsupported frontmatter, or declared compatibility)")
            continue
        src = ROOT / s["path"]
        out = dist / f"{s['name']}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(src.rglob("*")):
                if f.is_file():
                    z.write(f, Path(s["name"]) / f.relative_to(src))
        print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
