# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Mickey

Mickey is a CLI for hiring AI agents that write code and review each other's patches. Each agent runs in an isolated Docker sandbox sharing `~/src/`. Agents produce `git format-patch` output and peer-review before anything reaches a human's merge queue.

The entire CLI is a single bash script (`mickey`) wrapping `docker sandbox` commands.

## Architecture

- **`mickey`** — Bash CLI. Maps commands to `docker sandbox` subcommands: `hire`→`create`, `work`→`run`, `sh`→`exec`, `ls`→`ls`, `fire`→`rm`. Agent rules are inlined as a heredoc variable and injected via `--append-system-prompt`.

### Patch workflow

```
Agent writes code → git format-patch → ~/src/patch/
Reviewer applies patch → runs tests → writes .review-<name>.md
  Accept → amend with Reviewed-by: → copy to ~/src/merge-queue/
  Needs-work → author revises → new patch → re-review
Human applies from ~/src/merge-queue/ with git am
```

When given no specific task, agents automatically pick up work: review unreviewed patches by others (priority 1), or address review feedback on their own patches (priority 2). Agent identity is determined by `$HOSTNAME` matching the `<agent>` field in patch filenames.

### Workspace layout (inside sandboxes)

| Path | Purpose |
|------|---------|
| `$WORKSPACE_DIR/` (`~/src/`) | Synced to host. Agents must NOT modify directly (except patch/merge-queue). |
| `$WORKSPACE_DIR/repos/` | Git repos (read-only). Agents clone from here. |
| `~/work/` | Local workspace. Agents clone repos here. |
| `$WORKSPACE_DIR/patch/` | Shared patch mailing list. |
| `$WORKSPACE_DIR/merge-queue/` | Merge queue (reviewed patches with `Reviewed-by:` tags). |

## No build/test/lint

This project has no build step, test suite, or linter. It's a single bash script.

## Making changes

Agent rules are defined in the `AGENT_RULES` variable at the top of the `mickey` script and injected into each agent session via `--append-system-prompt`. To change agent behavior, edit the heredoc in `mickey` directly.
