# Mickey

Hire AI agents that write code in isolated Docker sandboxes.

Agents share `~/src/` with the host. Given a prompt they work on it; given nothing they scan repos for TODOs and pick one at random. They clone repos locally, work on a branch, run `make test`, and submit `git format-patch` output to a merge queue. You review and apply with `mickey am`.

## Setup

```bash
mkdir -p ~/src/wip ~/src/merge-queue ~/src/repos
# Put your git repos under ~/src/repos/
# Each repo should have a Makefile with test and deploy targets
mickey hire alice
mickey hire bob
```

## Send work

```bash
mickey whip                                          # all agents work continuously
mickey whip --model claude-opus-4-6                 # choose model
mickey whip -j 2                                     # run 2 agents
mickey whip -j 2 "Add JWT auth" "Fix logging bug"   # 2 agents with specific tasks
mickey whip "Add JWT auth:Fix logging bug"           # same, colon-separated
```

## Patch workflow

Agents run `make test`, then submit patches directly to `~/src/merge-queue/<repo>/`.

```bash
# Verify and apply all patches
mickey am

# Verify, apply, and push
mickey am --push
```

## Other commands

```bash
mickey ls              # list agents
mickey sh alice        # shell into agent
mickey fire alice      # remove agent
mickey reset           # clear wip/ and merge-queue/
```
