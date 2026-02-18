# TODO

- Make sure all reference to queue are removed. The merge queue folder is called merge-queue
- Before picking up a TODO from a repo, check that no existing patch in `patch/` already addresses it (scan patch commit messages for the TODO text)
- When an agent claims a TODO, it should create a file in `patch/` (e.g. `TIMESTAMP-<repo>-<agent>-<short-name>.wip`) so other agents know it's already being worked on and skip it
- When accepting a patch into the merge queue, remove the corresponding TODO from the repo's TODO file
- Add a `whip` command that sends all existing agents to work on their default behavior (iterate `docker sandbox ls`, run `mickey work` for each). When agent are done they should work again.
- Reviewer should try to apply the patch they just put in the merge queue before calling it done.
- mickey reset command should empty the patch and the merge queue (with yN confirmation)
- Add `--model <model>` flag to `mickey work` (and `whip`) to pass the model via `ANTHROPIC_MODEL` env var to `docker sandbox run`
- Warn on `work`/`whip` if repos under `~/src/repos/` are writable — only the prompt prevents agents from modifying them, so the recommendation is to `chmod -R a-w ~/src/repos/` before running agents
