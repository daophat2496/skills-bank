# Reviewing a skill

What a skill must pass before it moves from `trial` to `approved`. Most of the quality bar
comes from Anthropic's [Lessons from building Claude Code: How we use skills](https://claude.dev/blog/lessons-from-building-claude-code-how-we-use-skills/)
and [The new rules of context engineering](https://claude.dev/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models/).

## Safety (any failure blocks approval)

- [ ] Read every file, not just `SKILL.md`. Scripts run on your machine.
- [ ] `hooks` in frontmatter: know exactly what fires and on which tool. Skill hooks stay
      active for the rest of the session once invoked.
- [ ] `allowed-tools`: grants run without a prompt. Nothing broader than the skill needs.
- [ ] No network calls, credential reads or writes outside the project that the skill
      doesn't plainly need and explain.
- [ ] Licence allows redistribution. No licence means no vendoring.

## Quality

- [ ] **Fits one category.** Skills that straddle several confuse the agent.
- [ ] **Description says when to trigger**, with the phrases a user would actually type,
      not a summary of features.
- [ ] **Doesn't state the obvious.** Content Claude would do anyway is context with no value.
- [ ] **Has gotchas**, or knowledge that pushes Claude off its default path. This is the
      highest-signal part of a skill.
- [ ] **Goal and constraints, not every step.** Over-prescribed steps break on the first
      situation the author didn't foresee.
- [ ] **Progressive disclosure.** Long material split into files the `SKILL.md` points to,
      loaded when needed.
- [ ] **Code over prose** where it fits: helper scripts let Claude compose instead of
      rebuilding boilerplate.

A skill can be useful and still miss some quality points. Approve it with a note in
`provider.yaml` saying what's weak, rather than editing the vendored copy.

## Don't

- Edit a vendored skill. Keep it byte-for-byte so `outdated.py` diffs stay meaningful. If it
  needs changes, fork the idea into a skill of your own under `providers/daophat2496/`.
- Approve a new upstream commit without reading its diff.
