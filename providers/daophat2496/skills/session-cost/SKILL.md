---
name: session-cost
description: Explains what a Claude Code session cost and why, from the session transcript on disk - turns, cache hit rate, cache-write spikes and their likely causes (pauses, model switches, compaction), output vs input, the most expensive turns - and suggests what to change. Trigger on "why was this session so expensive", "how much did this cost", "check my usage", "session cost", "phiên này tốn bao nhiêu", or after a long or surprising session.
compatibility: Claude Code only (reads local session transcripts)
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/session_cost.py *)
---

# Session cost

Run the analyzer. With no argument it reads the newest session of the current project;
pass a session id or a `.jsonl` path for another one, `--list` to see recent sessions.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/session_cost.py
```

Then explain the result to the user in plain terms, and recommend at most three changes,
each tied to a number in the output. What moves the bill, roughly in order:

| Signal in the output | Likely cause | What to change |
|---|---|---|
| Low cache hit rate, write spikes after long gaps | Pauses longer than the cache lifetime (5 min on an API key, 1 h on a subscription) | Keep sessions moving; `/compact` before a break, not after |
| Write spike right after a model change | New model starts with an empty cache | Switch models at a natural break, after `/compact` or with a fresh session |
| Many turns, input total many times the context size | Retry loops, reading files piecemeal | Give the model a check to run; ask it to batch reads |
| High output on a small change | Effort too high for the task, or repeated attempts | Lower effort for routine work; raise it only for one hard step |
| Context large for most turns | Leftovers from earlier work resent every turn | `/clear` between unrelated tasks; `/compact keep <what matters>` at a break |

## Gotchas

- Dollar figures use list API prices built into the script (dated in its header). On a
  subscription they measure how much work was done, not a bill.
- Unknown models are reported in tokens only. Add their prices to `PRICES` in the script.
- The transcript records each API response several times (once per content block); the
  script de-duplicates by message id. Summing raw lines double-counts.
- Subagent turns are included when they are in the transcript; they are listed separately
  because they often run on a different model.
- `/usage` inside Claude Code is the authoritative number for the live session. This skill
  is for the *why*, and for sessions that have already ended.
