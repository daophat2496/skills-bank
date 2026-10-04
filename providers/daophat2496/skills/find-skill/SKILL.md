---
name: find-skill
description: Searches the personal skills bank (github.com/daophat2496/skills-bank) for reviewed skills that fit a need, and explains how to install them at project or user scope. Trigger on "find a skill for", "is there a skill that", "which skill should I add to this project", "tìm skill", "có skill nào để", or when the user describes a recurring task a skill could cover.
---

# Find a skill in the bank

The bank is a curated set of skills the owner has reviewed. Only recommend skills from it;
installing straight from an upstream repo bypasses that review.

## Read the catalog

Use a local clone if one exists (`$SKILLS_BANK_DIR`, else `~/skills-bank`), otherwise fetch:

```bash
curl -fsSL https://raw.githubusercontent.com/daophat2496/skills-bank/main/catalog.json
```

Each entry has `name`, `provider`, `description`, `category`, `tags`, `status`
(`approved` or `trial`), `claude_ai` (uploadable to claude.ai), `hooks`, `scripts`.

## Answer

Match on `description`, `category` and `tags` against what the user needs, not just keywords.
For each candidate give: name, provider, one line on what it does, status, and whether it
runs hooks or scripts. Say plainly when nothing fits.

Then ask where it should live before installing anything:

| Scope | Claude Code | Other agents (Codex, Cursor, …) |
|---|---|---|
| This project | `/plugin install <name>@skills-bank`, choose *project* | `npx skills add daophat2496/skills-bank -s <name>` |
| Whole machine | same, choose *user* | add `-g` |

First use of the marketplace needs `/plugin marketplace add daophat2496/skills-bank`.
A whole provider is `pack-<provider>`; everything approved is `all`.

## Gotchas

- `trial` skills have not been fully reviewed. Say so when recommending one.
- A skill with `hooks: true` changes tool behaviour for the rest of the session. Mention it.
- Installing a single skill and a pack that contains it gives two copies. Pick one.
- If the need is real but the bank has nothing, suggest an upstream candidate to vendor with
  `scripts/add.py` in the bank repo. Do not install it from upstream directly.
