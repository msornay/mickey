# TODO

- Before picking up a TODO from a repo, check that no existing patch in `patch/` already addresses it (scan patch commit messages for the TODO text)
- When an agent claims a TODO, it should create a file in `patch/` (e.g. `TIMESTAMP-<repo>-<agent>-<short-name>.wip`) so other agents know it's already being worked on and skip it
- When accepting a patch into the merge queue, remove the corresponding TODO from the repo's TODO file
- Add a `whip` command that sends all existing agents to work on their default behavior (iterate `docker sandbox ls`, run `mickey work` for each)
