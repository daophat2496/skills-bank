#!/usr/bin/env python3
"""Explain what a Claude Code session cost, from its transcript.

    session_cost.py                 newest session of the current project
    session_cost.py <id|path.jsonl> a specific session
    session_cost.py --list          recent sessions of the current project

Prices: API list, USD per million tokens, from claude.dev (2026-09-25 and 2026-09-28).
Cache writes bill at 1.25x input (5-minute) or 2x input (1-hour); fast mode at 2x.
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

PRICES = {  # model: (input, output, cache read)
    "claude-opus-5-5": (4.0, 20.0, 0.20),
    "claude-sonnet-5-5": (2.0, 10.0, 0.20),
    "claude-fable-5-1": (10.0, 50.0, 0.25),
    "claude-opus-5": (5.0, 25.0, 0.50),
}
SPIKE_MIN_TOKENS = 20_000


def projects_dir() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")) / "projects"


def project_sessions() -> list[Path]:
    slug = re.sub(r"[^A-Za-z0-9]", "-", os.getcwd())
    d = projects_dir() / slug
    return sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True) if d.exists() else []


def resolve(arg: str | None) -> Path:
    if arg and Path(arg).is_file():
        return Path(arg)
    if arg:
        hits = list(projects_dir().glob(f"*/{arg}*.jsonl"))
        if not hits:
            sys.exit(f"no session matching {arg!r} under {projects_dir()}")
        return hits[0]
    sessions = project_sessions()
    if not sessions:
        sys.exit(f"no sessions for {os.getcwd()} under {projects_dir()}")
    return sessions[0]


def price(model: str) -> tuple[float, float, float] | None:
    base = re.sub(r"(-\d{8}|\[1m\])$", "", model or "")
    return PRICES.get(base)


def turn_cost(model: str, u: dict, fast: bool) -> float | None:
    p = price(model)
    if not p:
        return None
    pin, pout, pread = p
    cc = u.get("cache_creation") or {}
    w5 = cc.get("ephemeral_5m_input_tokens", 0)
    w1h = cc.get("ephemeral_1h_input_tokens", 0)
    if not cc:  # older transcripts: assume 5-minute writes
        w5 = u.get("cache_creation_input_tokens", 0)
    cost = (
        u.get("input_tokens", 0) * pin
        + u.get("cache_read_input_tokens", 0) * pread
        + w5 * pin * 1.25
        + w1h * pin * 2.0
        + u.get("output_tokens", 0) * pout
    ) / 1e6
    return cost * (2 if fast else 1)


def load(path: Path) -> list[dict]:
    turns, seen, compact_pending = [], set(), False
    files = [path, *sorted(path.with_suffix("").glob("subagents/*.jsonl"))]
    for f in files:
        for line in f.open(encoding="utf-8"):
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("subtype") == "compact_boundary" or d.get("isCompactSummary"):
                compact_pending = True
            m = d.get("message")
            if d.get("type") != "assistant" or not isinstance(m, dict) or not m.get("usage"):
                continue
            if m.get("id") in seen:
                continue
            seen.add(m.get("id"))
            u = m["usage"]
            turns.append({
                "t": datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")),
                "model": m.get("model", "?"),
                "side": bool(d.get("isSidechain")) or f != path,
                "u": u,
                "ctx": u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0),
                "write": u.get("cache_creation_input_tokens", 0),
                "cost": turn_cost(m.get("model", ""), u, u.get("speed") == "fast"),
                "after_compact": compact_pending,
            })
            compact_pending = False
    return sorted(turns, key=lambda x: x["t"])


def fmt_tok(n: float) -> str:
    return f"{n/1e6:.2f}M" if n >= 1e6 else f"{n/1e3:.1f}k" if n >= 1e3 else str(int(n))


def money(x: float | None) -> str:
    return "n/a" if x is None else f"${x:.2f}"


def summarize(label: str, turns: list[dict]) -> None:
    if not turns:
        return
    s = lambda k: sum(t["u"].get(k, 0) for t in turns)
    inp, read, write, out = s("input_tokens"), s("cache_read_input_tokens"), s("cache_creation_input_tokens"), s("output_tokens")
    thinking = sum((t["u"].get("output_tokens_details") or {}).get("thinking_tokens", 0) for t in turns)
    total_in = inp + read + write
    costs = [t["cost"] for t in turns]
    known = sum(c for c in costs if c is not None)
    models = sorted({t["model"] for t in turns})
    print(f"\n== {label}: {len(turns)} turns, models: {', '.join(models)}")
    print(f"  input processed  {fmt_tok(total_in)}  (cache read {read/total_in:.0%}, cache write {write/total_in:.0%}, fresh {inp/total_in:.0%})" if total_in else "  no input")
    print(f"  largest context  {fmt_tok(max(t['ctx'] for t in turns))}   input total is {total_in/max(max(t['ctx'] for t in turns),1):.0f}x the largest context")
    print(f"  output           {fmt_tok(out)}  (thinking {fmt_tok(thinking)})")
    print(f"  est. cost        {money(known)}" + ("  (some turns on unpriced models)" if None in costs else ""))
    if known:
        parts = {"cache read": 0.0, "cache write": 0.0, "fresh input": 0.0, "output": 0.0}
        for t in turns:
            p = price(t["model"])
            if not p:
                continue
            u, (pin, pout, pread) = t["u"], p
            cc = u.get("cache_creation") or {}
            k = 2 if u.get("speed") == "fast" else 1
            parts["cache read"] += k * u.get("cache_read_input_tokens", 0) * pread / 1e6
            parts["cache write"] += k * (cc.get("ephemeral_5m_input_tokens", 0) * 1.25 + cc.get("ephemeral_1h_input_tokens", 0) * 2) * pin / 1e6
            parts["fresh input"] += k * u.get("input_tokens", 0) * pin / 1e6
            parts["output"] += k * u.get("output_tokens", 0) * pout / 1e6
        print("  cost split       " + ", ".join(f"{k} {v/known:.0%}" for k, v in parts.items()))


def spikes(turns: list[dict]) -> None:
    main = [t for t in turns if not t["side"]]
    rows = []
    for prev, t in zip([None, *main], main):
        if t["write"] < SPIKE_MIN_TOKENS or t["write"] < 0.5 * max(t["ctx"], 1):
            continue
        if prev is None:
            why = "session start"
        elif t["after_compact"]:
            why = "after compaction"
        elif prev["model"] != t["model"]:
            why = f"model switch {prev['model']} -> {t['model']}"
        elif (gap := (t["t"] - prev["t"]).total_seconds()) > 300:
            why = f"after a {gap/60:.0f} min pause"
        else:
            why = "prefix changed (tools, MCP server, system prompt or effort on a cloud provider)"
        rows.append((t, why))
    print(f"\n== Cache-write spikes (>= {fmt_tok(SPIKE_MIN_TOKENS)} and most of the context): {len(rows)}")
    for t, why in rows:
        print(f"  {t['t']:%H:%M}  wrote {fmt_tok(t['write'])}  {money(t['cost'])}  {why}")


def top(turns: list[dict], n: int = 5) -> None:
    priced = sorted((t for t in turns if t["cost"] is not None), key=lambda t: t["cost"], reverse=True)[:n]
    if not priced:
        return
    print(f"\n== Most expensive turns")
    for t in priced:
        u = t["u"]
        print(f"  {t['t']:%H:%M}  {money(t['cost'])}  ctx {fmt_tok(t['ctx'])}  out {fmt_tok(u.get('output_tokens', 0))}"
              f"  write {fmt_tok(t['write'])}{'  [subagent]' if t['side'] else ''}")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--list" in sys.argv:
        for p in project_sessions()[:15]:
            print(f"{datetime.fromtimestamp(p.stat().st_mtime):%Y-%m-%d %H:%M}  {p.stem}  {p.stat().st_size/1e6:.1f} MB")
        return 0
    path = resolve(args[0] if args else None)
    turns = load(path)
    if not turns:
        sys.exit(f"no assistant turns with usage in {path}")
    span = turns[-1]["t"] - turns[0]["t"]
    print(f"Session {path.stem}  {turns[0]['t']:%Y-%m-%d %H:%M} UTC, {span.total_seconds()/3600:.1f} h")
    summarize("Main conversation", [t for t in turns if not t["side"]])
    summarize("Subagents", [t for t in turns if t["side"]])
    spikes(turns)
    top(turns)
    return 0


if __name__ == "__main__":
    sys.exit(main())
