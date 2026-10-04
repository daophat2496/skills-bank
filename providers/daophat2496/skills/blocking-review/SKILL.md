---
name: blocking-review
description: Reviews the current branch's diff (or a given PR, commit range or files) and reports only problems worth blocking the merge for, each with file and line, why it is wrong, and a concrete way to show it fails. Trigger on "review this", "review my changes", "anything blocking?", "check before I merge", "pre-PR review", "review code giúp tôi", or before opening a pull request.
---

# Blocking review

The output is a short list a reviewer can act on, not a tour of the diff. A finding earns its
place only if you would refuse to merge because of it.

## Scope

Default target: the diff from the merge-base with the default branch to the working tree,
including uncommitted changes. Find the base with `git merge-base HEAD origin/HEAD`
(fall back to `main`, then `master`). If the user names a PR, range or files, use that instead.

Read the surrounding code a change touches, not just the hunks: callers of a changed
function, the other side of a renamed field, the schema a query relies on. Bugs that block
merges usually live one layer away from the edited lines.

## What counts as blocking

Wrong results, crashes, data loss or corruption, security holes, broken API or schema
contracts with existing callers, race conditions, resource leaks on a hot path, a migration
that cannot be rolled back, tests that pass without exercising the change.

Not blocking: style, naming, missing comments, refactors you would have done differently,
speculative performance. Leave them out entirely; do not add a "nits" section.

## Each finding

```
path/to/file.ext:LINE — one-line statement of the defect
Why: what goes wrong, for which input or state.
Show it: a command, test or input that demonstrates the failure.
```

Before reporting, try to make "Show it" real: run the test, call the function, write a
three-line repro. If you cannot demonstrate it, either drop the finding or mark it
`(unconfirmed)` and say what you would need to check. Rank by severity.

If nothing blocks, say so in one line and stop. An empty review is a valid result.

## Gotchas

- A diff that renames or removes something looks clean in isolation. Grep for the old name
  across the repo, including config, SQL, templates and other languages.
- Generated files and lockfiles inflate the diff. Skim them for surprises (a major version
  bump, a new dependency) but do not review them line by line.
- Pre-existing bugs the diff did not introduce are not blockers for this merge. Mention one
  only if the change makes it reachable or worse.
- Tests in the diff that assert on mocks of the code under test prove nothing. Check that at
  least one test would fail if the change were reverted.
- On a large diff, reviewing it all in one pass misses things late in the list. Split by
  file or module (subagents if available) and check each report's evidence before merging them.
