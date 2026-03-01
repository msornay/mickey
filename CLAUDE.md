# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Mickey

Mickey is a CLI for hiring AI agents that write code in isolated QEMU microVMs sharing `~/src/` via 9p filesystem. Agents produce `git format-patch` output after passing sanity tests (`make test`), submitting patches directly to a merge queue organized by repo.

The entire CLI is a single Python script (`mickey`) managing QEMU VMs via SSH.

## Architecture

- **`mickey`** — Python CLI (stdlib only, no dependencies). Manages QEMU aarch64 microVMs with Apple HVF acceleration. Commands: `hire` (create VM + CoW overlay disk), `whip` (send agents to work via SSH), `sh` (SSH shell), `ls` (scan `~/.mickey/vms/`), `fire` (shutdown + cleanup), `mkimage` (build golden base image), `cleanup` (remove orphans). Agent rules are inlined as a string constant and injected via `--append-system-prompt` over SSH.

### VM isolation

Each agent runs in its own QEMU microVM with:
- **CoW overlay disk** from a shared golden base image (`~/.mickey/base.qcow2`)
- **9p filesystem sharing** for `$WORKSPACE_DIR` (mount tag: `workspace`, `security_model=none`)
- **SSH access** via user-mode networking with port forwarding (ports start at 10022)
- **4 GB RAM / 2 vCPUs** by default (configurable via `MICKEY_VM_RAM` / `MICKEY_VM_CPUS`)

State lives in `~/.mickey/vms/<name>/` (disk overlay, UEFI vars, PID file, SSH port, monitor socket).

### Prerequisites

```
brew install qemu
mickey mkimage  # one-time: builds golden base image with Ubuntu 24.04 + Docker + Claude Code
```

### Task model

Tasks live as plain text files in `~/src/todos/`. Each `.txt` file is one task. The `whip` command picks tasks with a 10/90 split:
- 10% of the time: **rules audit** — verify a random repo follows its RULES.md conventions and file findings as todos (QA mode, no patches).
- 90% of the time: random pick from all `todos/*.txt` files plus one synthetic **QA** entry. This means QA probability is 1/(N+1) where N is the number of todos — when todos are empty, QA is guaranteed; when many todos exist, QA is rare.

When an agent finishes without producing a patch, its wip file is returned to `todos/` so the task is not lost.

```
todos/foo.txt  →  whip picks, moves to wip/foo.txt  →  agent works  →  patch in merge-queue/
                                                              ↓                     ↓
                                                    no patch: wip/foo.txt    mickey am applies patch
                                                    returned to todos/       → success: deletes wip/foo.txt
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

### Workspace layout (inside VMs)

| Path | Purpose |
|------|---------|
| `/home/agent/src/` (`$WORKSPACE_DIR`) | 9p mount from host `~/src/`. Agents must NOT modify directly (except merge-queue/). |
| `/home/agent/src/repos/` | Git repos (read-only). Agents clone from here. |
| `~/work/` | Local workspace. Agents clone repos here. |
| `/home/agent/src/todos/` | Task files. One `.txt` per task, picked by whip. |
| `/home/agent/src/wip/` | Tasks in progress (moved from todos/ by whip). |
| `/home/agent/src/merge-queue/<repo>/` | Merge queue organized by repo (patches ready for human to apply). |

## Testing

Run the unit tests with `python3 test_mickey` (or `pytest test_mickey` if available). Tests validate argument parsing, usage output, script structure, QEMU helper functions, and E2E behavior with temp workspaces. No QEMU required for unit tests.

For end-to-end VM lifecycle testing, run `./test_qemu_e2e` (requires `qemu-system-aarch64` and `mickey mkimage` to have been run first).

## Making changes

Agent rules are defined in the `AGENT_RULES` (developer) and `QA_RULES` (QA tester) constants at the top of the `mickey` script and injected into each agent session via `--append-system-prompt` over SSH. Agents read `$WORKSPACE_DIR/CLAUDE.md` + `RULES.md` and the repo's own `CLAUDE.md` + `RULES.md` (if they exist) at the start of each run. To change agent behavior, edit the strings in `mickey` directly.
