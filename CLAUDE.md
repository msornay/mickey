# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Mickey

Mickey is a CLI for hiring AI agents that write code and review each other's patches. Each agent runs in an isolated Docker sandbox sharing `~/src/`. Agents produce `git format-patch` output and peer-review before anything reaches a human's merge queue.

The entire CLI is a single bash script (`mickey`) wrapping `docker sandbox` commands.

## Architecture

- **`mickey`** — Bash CLI (~47 lines). Maps commands to `docker sandbox` subcommands: `hire`→`create`, `work`→`run`, `sh`→`exec`, `ls`→`ls`, `fire`→`rm`.
- **`agent-rules.md`** — Instructions copied to `~/src/CLAUDE.md` so agents inside sandboxes know the workflow. Defines workspace layout, patch production, review process, and revision cycle.

### Patch workflow

```
Agent writes code → git format-patch → ~/src/patches/
Reviewer applies patch → runs tests → writes .review-<name>.md
  Accept → amend with Reviewed-by: → copy to ~/src/queue/
  Needs-work → author revises → new patch → re-review
Human applies from ~/src/queue/ with git am
```

### Workspace layout (inside sandboxes)

| Path | Purpose |
|------|---------|
| `$WORKSPACE_DIR/` (`~/src/`) | Synced to host. Agents must NOT modify directly (except patches/queue). |
| `~/work/` | Local workspace. Agents clone repos here. |
| `$WORKSPACE_DIR/patches/` | Shared patch mailing list. |
| `$WORKSPACE_DIR/queue/` | Merge queue (reviewed patches with `Reviewed-by:` tags). |

## No build/test/lint

This project has no build step, test suite, or linter. It's a single bash script with a markdown rules file.

## Making changes

When modifying `agent-rules.md`, keep in mind it gets copied to `~/src/CLAUDE.md` and is the sole source of truth for agent behavior inside sandboxes. The copy in `~/src/CLAUDE.md` (the parent directory) is what agents actually read — changes to `agent-rules.md` require re-copying.
