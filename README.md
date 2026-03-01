# Mickey

Hire AI agents that write code in isolated QEMU microVMs.

Agents share `~/src/` with the host via 9p. Given a prompt they work on it; given nothing they scan repos for TODOs and pick one at random. They clone repos locally, work on a branch, run `make test`, and submit `git format-patch` output to a merge queue. You review and apply with `mickey am`.

## How it works

Each agent runs inside its own QEMU aarch64 VM with Apple HVF acceleration. VMs boot from a shared golden base image (`~/.mickey/base.qcow2` — Ubuntu 24.04 with Docker, Node.js, and Claude Code) using copy-on-write overlay disks, so creation is instant and disk-cheap. The host workspace is mounted inside the VM via 9p filesystem sharing. All communication goes through SSH over user-mode networking (no root needed, no bridge interfaces). State lives in `~/.mickey/vms/<name>/` — overlay disk, UEFI vars, PID file, SSH port, QEMU monitor socket. Because each VM has its own kernel, Docker inside the VM is real Docker — no Docker-in-Docker hacks.

## Setup

```bash
brew install qemu cdrtools
mickey mkimage                # one-time: builds the golden base image (~5 min)
mkdir -p ~/src/wip ~/src/merge-queue ~/src/repos
# Put your git repos under ~/src/repos/
# Each repo should have a Makefile with test and deploy targets
mickey hire alice
mickey hire bob
```

## Send work

```bash
mickey whip                              # all agents work continuously
mickey whip --model claude-opus-4-6     # choose model
mickey whip -j 2                         # run 2 agents
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
mickey status          # show todos, wip, queued patches
mickey sh alice        # shell into agent
mickey fire alice      # remove agent
mickey reset           # clear wip/ and merge-queue/
mickey cleanup         # remove orphan VM directories
```
