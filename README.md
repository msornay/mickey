# Mickey

Hire AI agents that write code and review each other's patches — you just apply what lands in the merge queue.

Under the hood: each agent is a Docker sandbox sharing `~/src/`. They clone repos into `~/work/`, produce `git format-patch` output, and peer-review before anything reaches your merge queue.

## Files

| File | Purpose |
|------|---------|
| `mickey` | CLI wrapper — short commands for sandbox management |
| `agent-rules.md` | Agent rules — copy as `CLAUDE.md` into your `~/src/` directory |

## One-time setup

```bash
# Copy rules into your src directory
cp agent-rules.md ~/src/CLAUDE.md
mkdir -p ~/src/patch ~/src/merge-queue
# Put your repos under ~/src/repos/

# Create and auth agents
mickey hire alice
mickey hire bob
```

## Give a task

```bash
mickey work alice "In myproject: Add JWT auth with login/logout endpoints. Include tests."
```

Claude reads `~/src/CLAUDE.md`, clones `~/src/repos/myproject` to `~/work/myproject`, works there, and writes the patch to `~/src/patch/`.

Patch file: `20260213-143022-myproject-alice-jwt-auth.patch`

## Review patches

```bash
mickey work bob "Review alice's latest jwt-auth patch for myproject"
```

Bob applies the patch, reads code, runs tests, and writes a review file:
- `20260213-151500-myproject-alice-jwt-auth.review-bob.md`

If the verdict is **accept**, Bob also adds `Reviewed-by: bob` to the commit and produces the patch into `~/src/merge-queue/`.

If the verdict is **needs-work**, alice revises (see below).

## Revise patches

```bash
mickey work alice "Address bob's review feedback on jwt-auth for myproject"
```

Alice reads the review, fixes the issues, and produces a new patch with a new timestamp. The old patch stays as history.

Then bob re-reviews the latest version:

```bash
mickey work bob "Review alice's latest jwt-auth patch for myproject"
```

## Apply from merge queue

Every patch in `~/src/merge-queue/` has been reviewed and carries `Reviewed-by:` tags.

```bash
ls ~/src/merge-queue/
cd ~/src/repos/myproject && git am ~/src/merge-queue/20260213-163000-myproject-alice-jwt-auth.patch
```

## Full example

```
~/src/patch/
  20260213-143022-myproject-alice-jwt-auth.patch             # alice's v1
  20260213-151500-myproject-alice-jwt-auth.review-bob.md     # needs-work
  20260213-160000-myproject-alice-jwt-auth.patch             # alice's revision
  20260213-163000-myproject-alice-jwt-auth.review-bob.md     # accept

~/src/merge-queue/
  20260213-163000-myproject-alice-jwt-auth.patch             # has Reviewed-by: bob
```

`ls` shows the full chronological story.

## Multi-repo tasks

```bash
mickey work alice "Add auth across api-server and frontend. New /auth endpoint in api-server, login page in frontend."
```

Agent clones both repos, works on both, produces two patches.

## Persistent agents

```bash
# Agent already has the clone, just send new work
mickey work alice "In myproject: Add rate limiting to /auth."
```

Agents automatically pull latest from `~/src/repos/` before starting work or reviewing patches.

## State

| What | Where |
|------|-------|
| Agents | `mickey ls` |
| Rules | `~/src/CLAUDE.md` (synced into all sandboxes) |
| Repos | `~/src/repos/` (read-only source, agents clone from here) |
| Patches & reviews | `~/src/patch/` (the mailing list) |
| Merge queue | `~/src/merge-queue/` (accepted patches, ready to apply) |
| Agent work | `~/work/` inside each sandbox (not synced) |

## Quick reference

```bash
# One-time setup
cp agent-rules.md ~/src/CLAUDE.md
mkdir -p ~/src/patch ~/src/merge-queue ~/src/repos
mickey hire <agent>                                          # create + auth

# Daily workflow
mickey work <agent> "<task>"                                 # send task
mickey work <reviewer> "Review <agent>'s latest <name> patch for <repo>"
git am ~/src/merge-queue/<timestamp>-<repo>-<agent>-<name>.patch   # apply from merge queue

# Utilities
mickey sh <agent>                                            # shell into agent
mickey ls                                                    # list agents
mickey fire <agent>                                          # remove agent
```
