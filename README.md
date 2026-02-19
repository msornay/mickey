# Mickey

Hire AI agents that write code and review each other's patches.

## Setup

```bash
cp agent-rules.md ~/src/CLAUDE.md
mkdir -p ~/src/patch ~/src/merge-queue ~/src/repos
# Put your git repos under ~/src/repos/
mickey hire alice
mickey hire bob
```

## Send work

```bash
mickey work alice "Add JWT auth to api-server. Include tests."
mickey work bob                        # autonomous mode: reviews, TODOs
mickey whip                            # all agents work continuously
mickey whip --model claude-opus-4-6   # choose model
```

## Review cycle

Agents automatically review each other's patches and write `.review-*.md` files in `~/src/patch/`. Accepted patches land in `~/src/merge-queue/` with `Reviewed-by:` tags.

```bash
# Apply accepted patches
git am ~/src/merge-queue/<patch-file>
```

## Other commands

```bash
mickey ls              # list agents
mickey sh alice        # shell into agent
mickey fire alice      # remove agent
mickey reset           # clear patch/ and merge-queue/
```
