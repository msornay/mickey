# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Mickey

Mickey is a CLI for hiring AI agents that write code in isolated Docker sandboxes sharing `~/src/`. Agents produce `git format-patch` output after passing sanity tests (`make test`), submitting patches directly to a merge queue organized by repo.

The entire CLI is a single bash script (`mickey`) wrapping `docker sandbox` commands.

## Architecture

- **`mickey`** — Bash CLI. Maps commands to `docker sandbox` subcommands: `hire`→`create`, `whip`→`run` (all agents), `sh`→`exec`, `ls`→`ls`, `fire`→`rm`. Agent rules are inlined as a heredoc variable and injected via `--append-system-prompt`.

### Patch workflow

```
Agent writes code → make test → git format-patch → ~/src/merge-queue/<repo>/
Human runs mickey am → verifies patches → applies with git am → optionally pushes
```

Agents claim TODOs by creating `.wip` lock files in `~/src/wip/`. TODOs are selected at random with a random delay to reduce collisions between agents.

### Workspace layout (inside sandboxes)

| Path | Purpose |
|------|---------|
| `$WORKSPACE_DIR/` (`~/src/`) | Synced to host. Agents must NOT modify directly (except wip/merge-queue). |
| `$WORKSPACE_DIR/repos/` | Git repos (read-only). Agents clone from here. |
| `~/work/` | Local workspace. Agents clone repos here. |
| `$WORKSPACE_DIR/wip/` | Work-in-progress lock files for TODO claims. |
| `$WORKSPACE_DIR/merge-queue/<repo>/` | Merge queue organized by repo (patches ready for human to apply). |

## Testing

Run the test suite with `./test_mickey`. Tests validate argument parsing, usage output, and script structure without requiring Docker.

## Making changes

Agent rules are defined in the `AGENT_RULES` variable at the top of the `mickey` script and injected into each agent session via `--append-system-prompt`. To change agent behavior, edit the heredoc in `mickey` directly.
