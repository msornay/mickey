# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Mickey

Mickey is a CLI for hiring AI agents that write code in isolated Docker sandboxes sharing `~/src/`. Agents produce `git format-patch` output after passing sanity tests (`make test`), submitting patches directly to a merge queue organized by repo.

The entire CLI is a single Python script (`mickey`) wrapping `docker sandbox` commands.

## Architecture

- **`mickey`** — Python CLI (stdlib only, no dependencies). Maps commands to `docker sandbox` subcommands: `hire`→`create`, `whip`→`run` (all agents), `sh`→`exec`, `ls`→`ls`, `fire`→`rm`. Agent rules are inlined as a string constant and injected via `--append-system-prompt`.

### Task model

Tasks live as plain text files in `~/src/todos/`. Each `.txt` file is one task. The `whip` command picks tasks programmatically with a 70/20/10 split:
- 70% of the time: pick a random file from `todos/`, move it to `wip/`, and assign its content as the agent's prompt (developer mode).
- 20% of the time: **QA tester** — pick a random repo and test it from a user's perspective. The QA agent reads only documentation (never source code), installs and tests the software, cleans up `~/work/` when done, and files bug reports as `.txt` files in `todos/`.
- 10% of the time: **rules audit** — verify a random repo follows its RULES.md conventions and fix violations (developer mode).

```
todos/foo.txt  →  whip picks, moves to wip/foo.txt  →  agent works  →  patch in merge-queue/
                                                                            ↓
                                                            mickey am applies patch
                                                            → success: deletes wip/foo.txt
                                                            → failure: creates todos/fix-foo.txt
```

### Conflict-aware whip

`whip` keeps agents busy while monitoring merge-queue/ for conflict risk. When any repo accumulates >2 patches, whip joins all agents, runs `am --push` to flush the queue, then restarts.

### Patch workflow

```
Agent writes code → make test → git format-patch → ~/src/merge-queue/<repo>/
Human runs mickey am → applies with git am → optionally pushes
```

`mickey am` is pure Python/git — no Claude verification step. Failed patches create a fix todo in `todos/`.

### Workspace layout (inside sandboxes)

| Path | Purpose |
|------|---------|
| `$WORKSPACE_DIR/` (`~/src/`) | Synced to host. Agents must NOT modify directly (except merge-queue/). |
| `$WORKSPACE_DIR/repos/` | Git repos (read-only). Agents clone from here. |
| `~/work/` | Local workspace. Agents clone repos here. |
| `$WORKSPACE_DIR/todos/` | Task files. One `.txt` per task, picked by whip. |
| `$WORKSPACE_DIR/wip/` | Tasks in progress (moved from todos/ by whip). |
| `$WORKSPACE_DIR/merge-queue/<repo>/` | Merge queue organized by repo (patches ready for human to apply). |

## Testing

Run the test suite with `python3 test_mickey` (or `pytest test_mickey` if available). Tests validate argument parsing, usage output, script structure, and E2E behavior with temp workspaces. No Docker required.

## Making changes

Agent rules are defined in the `AGENT_RULES` (developer) and `QA_RULES` (QA tester) constants at the top of the `mickey` script and injected into each agent session via `--append-system-prompt`. Agents read `$WORKSPACE_DIR/CLAUDE.md` + `RULES.md` and the repo's own `CLAUDE.md` + `RULES.md` (if they exist) at the start of each run. To change agent behavior, edit the strings in `mickey` directly.
