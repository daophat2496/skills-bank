---
name: careful
description: Turns on a guard for the rest of the session that makes every destructive shell command (rm -rf, DROP/TRUNCATE, force-push, git reset --hard, kubectl delete, terraform destroy, mkfs, dd to a device) stop for explicit human confirmation. Trigger on "be careful", "careful mode", "I'm touching prod", "this is production", or before working against live infrastructure or a shared database.
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: >-
            python3 -c "import json,re,sys;
            c=json.load(sys.stdin).get('tool_input',{}).get('command','');
            p=r'\brm\s+-[a-z]*(r[a-z]*f|f[a-z]*r)|\bdrop\s+(table|database|schema)\b|\btruncate\s+(table\s+)?\w|\bgit\s+push\b.*\s(--force(?!-with-lease)|-f\b)|\bgit\s+reset\s+--hard|\bgit\s+clean\s+-[a-z]*f|\bkubectl\s+delete\b|\bterraform\s+(destroy|apply\s+.*-destroy)|\bmkfs\b|\bdd\s+.*\bof=/dev/';
            m=re.search(p,c,re.I);
            m and print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'ask','permissionDecisionReason':'careful: destructive command ('+m.group(0).strip()+') needs your confirmation'}}))"
---

# Careful mode

A `PreToolUse` hook is now registered for the rest of this session. Any Bash command
matching a destructive pattern triggers a permission prompt labelled `[skill]`, even in
auto mode. Nothing is blocked outright: the human decides.

Tell the user, in one line, that careful mode is on and lasts until the session ends.

While it is on:

- Prefer the reversible form: `--force-with-lease` over `--force`, a `SELECT` count before a
  `DELETE`, `kubectl diff` / `terraform plan` before applying, moving to a trash dir over `rm -rf`.
- When a prompt is declined, do not retry with a rephrased command that slips past the
  pattern. Ask what the user wants instead.

## Gotchas

- The guard matches the command text, not intent. A destructive command hidden inside a
  script file (`./cleanup.sh`) is not caught. Read scripts before running them.
- It only covers the Bash tool. File deletion via other tools or MCP servers is not covered.
- There is no "off" switch short of ending the session; that is by design.
- Requires `python3` on PATH. Without it the hook errors and the command proceeds normally.
