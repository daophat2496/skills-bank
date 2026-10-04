#!/usr/bin/env bash
# Copy skills from the bank into a skills directory. For agents without plugin support,
# or when you want plain files you can read and edit.
#
#   scripts/install.sh <skill|pack-<provider>|all>... [--scope project|user] [--dest DIR]
#
#   --scope   project → ./.claude/skills   user → ~/.claude/skills   (asked if omitted)
#   --dest    any other skills directory, e.g. for another agent
#
# Works from a clone, or straight from GitHub:
#   bash <(curl -fsSL https://raw.githubusercontent.com/daophat2496/skills-bank/main/scripts/install.sh) careful
set -euo pipefail

die() { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }

BANK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd || true)"
if [[ ! -f "$BANK/catalog.json" ]]; then
  BANK="$(mktemp -d)"; trap 'rm -rf "$BANK"' EXIT
  git clone -q --depth 1 https://github.com/daophat2496/skills-bank.git "$BANK"
fi

SCOPE=""; DEST=""; WANT=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope) SCOPE="${2:?}"; shift 2 ;;
    --dest)  DEST="${2:?}"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) WANT+=("$1"); shift ;;
  esac
done
[[ ${#WANT[@]} -gt 0 ]] || die "name at least one skill, pack-<provider>, or all"

if [[ -z "$DEST" ]]; then
  if [[ -z "$SCOPE" ]]; then
    read -rp "Install for this project (p) or for your user on this machine (u)? [p/u] " ans
    case "$ans" in u|U) SCOPE=user ;; *) SCOPE=project ;; esac
  fi
  case "$SCOPE" in
    project) DEST="$PWD/.claude/skills" ;;
    user)    DEST="$HOME/.claude/skills" ;;
    *) die "--scope must be project or user" ;;
  esac
fi

# Resolve names to skill paths from the catalog.
mapfile -t PATHS < <(python3 - "$BANK/catalog.json" "${WANT[@]}" <<'PY'
import json, sys
skills = json.load(open(sys.argv[1]))["skills"]
out = []
for w in sys.argv[2:]:
    if w == "all":
        hit = [s for s in skills if s["status"] == "approved"]
    elif w.startswith("pack-"):
        hit = [s for s in skills if s["provider"] == w[5:] and s["status"] == "approved"]
    else:
        hit = [s for s in skills if s["name"] == w]
    if not hit:
        sys.exit(f"nothing matches {w!r}")
    out += [s["path"] for s in hit]
print("\n".join(dict.fromkeys(out)))
PY
)

mkdir -p "$DEST"
for p in "${PATHS[@]}"; do
  name="$(basename "$p")"
  if [[ -e "$DEST/$name" ]]; then
    printf '\033[33m!\033[0m %s already in %s, skipped\n' "$name" "$DEST"; continue
  fi
  cp -R "$BANK/$p" "$DEST/$name"
  printf '\033[32m✓\033[0m %s → %s\n' "$name" "$DEST/$name"
done
