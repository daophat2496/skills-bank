# skills-bank

A personal bank of agent skills I have read and approved. Skills come from their
original authors and are vendored here pinned to a commit, alongside a few I wrote myself.
Install from here, not from upstream: what you get is exactly what was reviewed.

Skills follow the open [Agent Skills](https://code.claude.com/docs/en/skills) format
(a folder with a `SKILL.md`), so they work in Claude Code, Codex, Cursor and other agents.

## Install

**Claude Code**: add the marketplace once, then install. Claude Code asks for the
scope: *user* (every project on this machine), *project* (shared with the repo), or *local*.

```text
/plugin marketplace add daophat2496/skills-bank
/plugin install careful@skills-bank          # one skill
/plugin install pack-daophat2496@skills-bank # one provider
/plugin install all@skills-bank              # everything approved
```

**Other agents** via the [`skills` CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add daophat2496/skills-bank -s careful   # one skill, this project
npx skills add daophat2496/skills-bank -g           # all, user-wide
```

**Plain copy**, no tooling: `scripts/install.sh careful --scope project`
(or pipe it from GitHub, see the script header).

**claude.ai**: `scripts/zip.py` builds `dist/<skill>.zip` for *Customize › Skills › Upload*.
Only skills marked `claude.ai ✓` below can be uploaded; hooks are Claude Code–only.

Not sure what you need? Install `find-skill` at user scope and ask
"is there a skill for reviewing code?".

## Gallery

Generated from `providers/*/provider.yaml` by `scripts/build.py`.

<!-- gallery:start -->

### Product verification

| Skill | Provider | What it does | Status | Notes |
|---|---|---|---|---|
| [`real-check`](providers/daophat2496/skills/real-check/SKILL.md) | daophat2496 | Before reporting a code change as done, run a real check that exercises it (the project's tests, type-checker, build, or the changed command itself) and report its actual output, or say plainly which check could not run and why. | approved | claude.ai ✓ |

### Data fetching & analysis

| Skill | Provider | What it does | Status | Notes |
|---|---|---|---|---|
| [`session-cost`](providers/daophat2496/skills/session-cost/SKILL.md) | daophat2496 | Explains what a Claude Code session cost and why, from the session transcript on disk - turns, cache hit rate, cache-write spikes and their likely causes (pauses, model switches, compaction), output vs input, the most expensive turns - and suggests what to change. | approved | scripts |

### Code quality & review

| Skill | Provider | What it does | Status | Notes |
|---|---|---|---|---|
| [`blocking-review`](providers/daophat2496/skills/blocking-review/SKILL.md) | daophat2496 | Reviews the current branch's diff (or a given PR, commit range or files) and reports only problems worth blocking the merge for, each with file and line, why it is wrong, and a concrete way to show it fails. | approved | claude.ai ✓ |

### Guardrails

| Skill | Provider | What it does | Status | Notes |
|---|---|---|---|---|
| [`careful`](providers/daophat2496/skills/careful/SKILL.md) | daophat2496 | Turns on a guard for the rest of the session that makes every destructive shell command (rm -rf, DROP/TRUNCATE, force-push, git reset --hard, kubectl delete, terraform destroy, mkfs, dd to a device) stop for explicit human confirmation. | approved | hooks |

### Working with skills

| Skill | Provider | What it does | Status | Notes |
|---|---|---|---|---|
| [`find-skill`](providers/daophat2496/skills/find-skill/SKILL.md) | daophat2496 | Searches the personal skills bank (github.com/daophat2496/skills-bank) for reviewed skills that fit a need, and explains how to install them at project or user scope. | approved | claude.ai ✓ |

<!-- gallery:end -->

## Layout

```text
providers/<provider>/
├── provider.yaml          # status, category, tags, upstream repo + commit, review notes
├── LICENSE                # upstream licence, for vendored skills
└── skills/<skill>/        # the skill folder, byte-for-byte as upstream
catalog.json               # generated: machine-readable index
.claude-plugin/marketplace.json   # generated: one plugin per skill, per provider, and "all"
```

A *provider* is whoever wrote the skill, not an AI vendor.

## Adding a skill

```bash
scripts/add.py https://github.com/<owner>/<repo>/tree/<ref>/<path/to/skill>
```

It vendors the folder at a pinned commit, copies the licence, marks it `trial`, and lists
what to read: scripts, hooks, `allowed-tools`, network calls. Review it against
[REVIEWING.md](REVIEWING.md), set category and tags, flip to `approved`, run `scripts/build.py`.

`scripts/outdated.py` shows which vendored skills changed upstream since they were pinned.
Updates are never automatic.

## Licence

My own skills and the tooling are MIT. Vendored skills keep their authors' licence,
in `providers/<provider>/LICENSE`. Only skills whose licence allows redistribution are here.
