---
name: real-check
description: Before reporting a code change as done, run a real check that exercises it (the project's tests, type-checker, build, or the changed command itself) and report its actual output, or say plainly which check could not run and why. Trigger on "make sure it works", "verify before you say done", "did you test it?", "kiểm tra thật", when finishing any change to runnable code, or when working at low effort where checks tend to get skipped.
---

# Real check before "done"

"Done" means a check that exercises the change ran and passed, and its output is in the
report. Reading the code again, or a syntax-only check, is not a check.

## Pick the check

Use what the project already uses. Look in `package.json` scripts, `Makefile`/`justfile`,
`pyproject.toml`/`tox.ini`/`noxfile.py`, `Cargo.toml`, `go.mod`, CI workflow files and the
README. Prefer, in order:

1. The narrowest test that goes through the changed code.
2. The test suite or type-check for the package you touched.
3. The build, or running the changed command or endpoint for real.

If no test covers the change and one is cheap to write, write it, and confirm it **fails
without the change** (stash or revert the fix, run it, restore). A test that passes either
way proves nothing.

## Dependencies

If the only thing stopping a check is missing project dependencies, install them with the
project's own package manager and lockfile (`npm ci`, `pnpm install --frozen-lockfile`,
`uv sync`, `pip install -r requirements.txt`, `cargo fetch`). Never `sudo`, never the system
package manager, unless the user says so.

## Report

Quote the command and the relevant tail of its output (pass counts, the error). If no real
check could run, say which one, why, and what the user should run, and do not call the change done.

## Gotchas

- Exit code 0 is not a pass. `pytest` with nothing collected, `jest --passWithNoTests`,
  a filter that matched no tests, or a script that swallows errors all "succeed". Read the
  output for the count of tests that actually ran.
- Watch mode hangs the session: use `vitest run`, `CI=1 npm test`, `jest --watchAll=false`.
- Build caches (Turborepo, Nx, Bazel, Gradle) can replay an old green result. Look for
  "cache hit" and force a re-run when the changed files should have invalidated it.
- In a monorepo, a type-check at the root may skip the package you changed, or run it
  against stale built output of its dependencies. Check the package itself.
- A check command that fails to start (missing binary, wrong directory) is not a failed
  test. Fix the invocation; do not report it as the change's result.
