# TODO

- Implicit TODO in all repo: well-organized, KISS, just the right amount of
  documentation. Simple E2E sanity tests commited and green

- Rework task selection: replace DEFAULT_PROMPT/DIFFICULT_TASK_PROMPT 50/50 coin flip. New model: 50% agent works from workspace root `$WORKSPACE_DIR/TODO.md` (cross-project tasks), 50% agent picks a repo at random and works from that repo's `TODO.md`. Remove `DIFFICULT_TASK_PROMPT`. Update `AGENT_RULES` to match: step 1 is "flip coin", step 2a is "read workspace TODO.md, pick a task" or step 2b is "pick a random repo, read its TODO.md, pick a task". If nothing significant to do, agent exits cleanly without producing a patch — this is fine.
