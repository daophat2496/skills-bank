#!/usr/bin/env python3
"""Validate the bank and regenerate catalog.json, the marketplace and the README gallery.

    scripts/build.py           write generated files
    scripts/build.py --check   fail if anything is invalid or out of date (CI)

Source of truth is providers/<provider>/provider.yaml plus each skill's SKILL.md.
Everything this script writes is generated: never edit it by hand.
"""
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REPO = "daophat2496/skills-bank"
MARKETPLACE = "skills-bank"

# The nine clusters from Anthropic's "How we use skills", plus two of our own.
CATEGORIES = {
    "library-reference": "Library & API reference",
    "verification": "Product verification",
    "data-analysis": "Data fetching & analysis",
    "team-automation": "Business process & team automation",
    "scaffolding": "Code scaffolding & templates",
    "code-quality": "Code quality & review",
    "ci-cd": "CI/CD & deployment",
    "runbooks": "Runbooks",
    "infra-ops": "Infrastructure operations",
    "guardrails": "Guardrails",
    "meta": "Working with skills",
}
STATUSES = {"approved", "trial"}
# Frontmatter keys claude.ai accepts on upload; anything else is rejected there.
CLAUDE_AI_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError("no YAML frontmatter")
    return yaml.safe_load(m.group(1)) or {}


def load() -> tuple[list[dict], list[str]]:
    skills, errors = [], []
    for pdir in sorted(p for p in (ROOT / "providers").iterdir() if p.is_dir()):
        meta_path = pdir / "provider.yaml"
        if not meta_path.exists():
            errors.append(f"{pdir.name}: missing provider.yaml")
            continue
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
        listed = meta.get("skills") or {}
        on_disk = {d.name for d in (pdir / "skills").iterdir() if d.is_dir()} if (pdir / "skills").exists() else set()

        for name in sorted(on_disk - listed.keys()):
            errors.append(f"{pdir.name}/{name}: on disk but not in provider.yaml")
        for name in sorted(listed.keys() - on_disk):
            errors.append(f"{pdir.name}/{name}: in provider.yaml but not on disk")
        if any("upstream" in (v or {}) for v in listed.values()) and not (pdir / "LICENSE").exists():
            errors.append(f"{pdir.name}: vendored skills need the upstream LICENSE at providers/{pdir.name}/LICENSE")

        for name in sorted(on_disk & listed.keys()):
            entry, where = listed[name] or {}, f"{pdir.name}/{name}"
            sdir = pdir / "skills" / name
            try:
                fm = frontmatter(sdir / "SKILL.md")
            except (OSError, ValueError, yaml.YAMLError) as e:
                errors.append(f"{where}: SKILL.md {e}")
                continue
            if not NAME_RE.match(name):
                errors.append(f"{where}: directory name must be kebab-case")
            if fm.get("name") != name:
                errors.append(f"{where}: frontmatter name {fm.get('name')!r} != directory name")
            if not fm.get("description"):
                errors.append(f"{where}: frontmatter needs a description")
            if entry.get("category") not in CATEGORIES:
                errors.append(f"{where}: category must be one of {', '.join(CATEGORIES)}")
            if entry.get("status") not in STATUSES:
                errors.append(f"{where}: status must be approved or trial")
            if entry.get("status") == "approved" and not entry.get("reviewed"):
                errors.append(f"{where}: approved skills need a reviewed date")

            files = [f for f in sdir.rglob("*") if f.is_file()]
            up = entry.get("upstream") or {}
            skills.append({
                "name": name,
                "provider": pdir.name,
                "description": " ".join(str(fm.get("description", "")).split()),
                "category": entry.get("category"),
                "tags": entry.get("tags") or [],
                "status": entry.get("status"),
                "origin": "vendored" if up else "authored",
                "upstream": f"https://github.com/{up['repo']}/tree/{up['ref']}/{up['path']}" if up else None,
                "inspired_by": entry.get("inspired-by"),
                "reviewed": str(entry["reviewed"]) if entry.get("reviewed") else None,
                "notes": entry.get("notes"),
                "path": sdir.relative_to(ROOT).as_posix(),
                "hooks": "hooks" in fm,
                "scripts": any(f.suffix in {".sh", ".py", ".js", ".ts"} or f.stat().st_mode & 0o111 for f in files),
                "claude_ai": set(fm) <= CLAUDE_AI_KEYS,
            })

    seen: dict[str, str] = {}
    for s in skills:
        if s["name"] in seen:
            errors.append(f"name clash: {s['name']} in {seen[s['name']]} and {s['provider']} (rename one; installers flatten names)")
        seen[s["name"]] = s["provider"]
    return skills, errors


def marketplace(skills: list[dict]) -> dict:
    approved = [s for s in skills if s["status"] == "approved"]
    plugins = [{
        "name": "all",
        "source": ".",
        "description": "Every approved skill in the bank.",
        "skills": [f"./{s['path']}" for s in approved],
        "strict": False,
    }]
    for provider in sorted({s["provider"] for s in approved}):
        mine = [s for s in approved if s["provider"] == provider]
        plugins.append({
            "name": f"pack-{provider}",
            "source": ".",
            "description": f"Approved skills from {provider}: {', '.join(s['name'] for s in mine)}.",
            "skills": [f"./{s['path']}" for s in mine],
            "strict": False,
        })
    for s in skills:
        plugins.append({
            "name": s["name"],
            "source": ".",
            "description": s["description"],
            "category": s["category"],
            "tags": s["tags"] + ([] if s["status"] == "approved" else ["trial"]),
            "skills": [f"./{s['path']}"],
            "strict": False,
        })
    return {
        "name": MARKETPLACE,
        "owner": {"name": "daophat2496", "url": "https://github.com/daophat2496"},
        "description": "A personal bank of reviewed agent skills, vendored from their authors and pinned to a commit.",
        "plugins": plugins,
    }


def gallery(skills: list[dict]) -> str:
    out = []
    for key, title in CATEGORIES.items():
        rows = [s for s in skills if s["category"] == key]
        if not rows:
            continue
        out += [f"### {title}", "", "| Skill | Provider | What it does | Status | Notes |", "|---|---|---|---|---|"]
        for s in rows:
            desc = s["description"].split(". ")[0].rstrip(".") + "."
            flags = [f for f, on in (("hooks", s["hooks"]), ("scripts", s["scripts"]), ("claude.ai ✓", s["claude_ai"])) if on]
            src = f"[{s['provider']}]({s['upstream']})" if s["upstream"] else s["provider"]
            out.append(f"| [`{s['name']}`]({s['path']}/SKILL.md) | {src} | {desc} | {s['status']} | {', '.join(flags)} |")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    check = "--check" in sys.argv
    skills, errors = load()
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    if errors:
        return 1

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    start, end = "<!-- gallery:start -->", "<!-- gallery:end -->"
    new_readme = re.sub(f"{start}.*?{end}", lambda _: f"{start}\n\n{gallery(skills)}\n{end}", readme, flags=re.S)

    outputs = {
        ROOT / "catalog.json": json.dumps({"repo": REPO, "skills": skills}, indent=2, ensure_ascii=False) + "\n",
        ROOT / ".claude-plugin" / "marketplace.json": json.dumps(marketplace(skills), indent=2, ensure_ascii=False) + "\n",
        readme_path: new_readme,
    }
    stale = [p for p, text in outputs.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
    if check:
        for p in stale:
            print(f"error: {p.relative_to(ROOT)} is out of date; run scripts/build.py", file=sys.stderr)
        return 1 if stale else 0
    for p in stale:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(outputs[p], encoding="utf-8")
        print(f"wrote {p.relative_to(ROOT)}")
    print(f"{len(skills)} skills OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
