# TODO

- When a single agent has finished working, whip wait for ALL agent to finish before restarting. This isn't the desired behavior. An agent done should be restarted immediately
- The README is outdated. It should be recreated from scrath and be KISS.
- Add a lean sanity test suite that the mickey script shoul pass before a patch is created
- When the agent exits with code 1 it probably indicates it run out of credits. wait 5min before retrying in whip
- Before picking up a TODO from a repo, check that no existing patch in `patch/` already addresses it (scan patch commit messages for the TODO text)
- When an agent claims a TODO, it should create a file in `patch/` (e.g. `TIMESTAMP-<repo>-<agent>-<short-name>.wip`) so other agents know it's already being worked on and skip it
- When accepting a patch into the merge queue, remove the corresponding TODO from the repo's TODO file
- Add a `whip` command that sends all existing agents to work on their default behavior (iterate `docker sandbox ls`, run `mickey work` for each). When agent are done they should work again.
- Add `--model <model>` flag to `mickey work` (and `whip`) to pass the model via `ANTHROPIC_MODEL` env var to `docker sandbox run`
- Warn on `work`/`whip` if repos under `~/src/repos/` are writable — only the prompt prevents agents from modifying them, so the recommendation is to `chmod -R a-w ~/src/repos/` before running agents
- Inline agent-rules.md content into the `mickey` script as a heredoc variable, and pass it to agents via `--append-system-prompt` instead of relying on ambient ~/src/CLAUDE.md discovery. This eliminates the manual `cp agent-rules.md ~/src/CLAUDE.md` step and prevents agent rules from leaking into interactive Claude Code sessions. Delete `agent-rules.md` after inlining.
- Update CLAUDE.md and README.md to remove all references to copying agent-rules.md to ~/src/CLAUDE.md. Document that rules are now inlined in the mickey script and injected via --append-system-prompt.
