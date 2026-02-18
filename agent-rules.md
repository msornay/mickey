# Agent Rules

You are a developer agent working inside a Docker sandbox.

## Workspace layout
- $WORKSPACE_DIR/ is synced to the host. **NEVER modify files here directly** — only write to patch/ and queue/.
- $WORKSPACE_DIR/repos/ contains git repos. **NEVER write to this directory or any repo inside it.** Only use it as a clone source.
- ~/work/ is your local workspace (not synced). Clone repos here and do all work here.
- $WORKSPACE_DIR/patch/ is the shared patch mailing list (submissions, reviews, revisions).
- $WORKSPACE_DIR/queue/ is the merge queue (accepted patches with `Reviewed-by:` tags, ready for the human to apply).

## Default behavior

If you are given no specific task (empty or missing instructions), pick up useful work automatically using this priority order:

### Priority 1: Review an unreviewed patch by someone else

Your agent name is `$HOSTNAME`. Look in `$WORKSPACE_DIR/patch/` for `.patch` files where the `<agent>` field in the filename does NOT match `$HOSTNAME`.

Patch filenames follow the convention: `TIMESTAMP-<repo>-<agent>-<short-name>.patch`

For each unique `<repo>-<agent>-<short-name>` group, only the latest patch (highest timestamp) matters — earlier versions are superseded.

A patch is **unreviewed** if no file matching `*-<repo>-<agent>-<short-name>.review-*.md` exists with a timestamp >= the patch's timestamp.

Pick the oldest unreviewed patch by someone else and review it using the "Reviewing patches" process below.

### Priority 2: Address review feedback on your own patch

Look for `.review-*.md` files in `$WORKSPACE_DIR/patch/` that reference one of your patches (where `<agent>` matches `$HOSTNAME`) and contain `Verdict: needs-work`.

A review needs addressing if you haven't produced a newer patch revision — i.e., no `.patch` file for the same `<repo>-<agent>-<short-name>` group has a timestamp newer than the review file.

Pick the oldest such review and revise your patch using the "Revising patches" process below.

### Priority 3: Pick up a TODO from a repo

If there are no patches to review and no review feedback to address, look for TODOs in the repos.

1. Search all repos in `$WORKSPACE_DIR/repos/` for TODO/FIXME/HACK/XXX comments:
   ```
   grep -rn 'TODO\|FIXME\|HACK\|XXX' $WORKSPACE_DIR/repos/
   ```
2. Also check for a `TODO.md` or `TODO` file in each repo root.
3. Pick one actionable TODO — prefer ones that are small, self-contained, and have clear intent.
4. Skip TODOs that are vague, require external context you don't have, or would need architectural decisions.
5. Work on it using the normal "Starting work" and "Producing output" process. Use the TODO text as the basis for your `<short-name>` in the patch filename.
6. In your commit message, reference the original TODO (file and line number) so reviewers can trace it back.

### If there's nothing to do

If there are no unreviewed patches by others, no pending review feedback on your patches, and no actionable TODOs in the repos, say so and stop.

## Starting work
1. Get the repo(s) you need. If ~/work/<repo> doesn't exist, clone it:
     git clone $WORKSPACE_DIR/repos/<repo> ~/work/<repo>
   If it already exists, pull latest:
     cd ~/work/<repo> && git checkout main && git pull $WORKSPACE_DIR/repos/<repo> main
2. Work on a descriptive branch:
     cd ~/work/<repo> && git checkout -b <branch-name>

## Producing output
When your task is complete and tests pass, squash to a single commit with a datetime-prefixed patch:
```
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
cd ~/work/<repo>
git checkout -b squash-tmp main
git merge --squash <branch-name>
git commit -m "<descriptive message>"
git format-patch main --stdout > $WORKSPACE_DIR/patch/${TIMESTAMP}-<repo>-<agent>-<short-name>.patch
```

Verify the patch applies cleanly before moving on:
```
cd ~/work/<repo>
git checkout main
git am --check $WORKSPACE_DIR/patch/${TIMESTAMP}-<repo>-<agent>-<short-name>.patch
```

If it fails, fix your branch and regenerate the patch.

## Reviewing patches
When asked to review a patch:

1. Find the latest patch matching the name pattern in `$WORKSPACE_DIR/patch/`.
2. Parse the repo name from the filename.
3. Clone the repo into ~/work/ if not already there, or sync to latest main:
   git clone $WORKSPACE_DIR/repos/<repo> ~/work/<repo>  # if new
   cd ~/work/<repo> && git checkout main && git pull $WORKSPACE_DIR/repos/<repo> main
4. Apply the patch:
   ```
   git am $WORKSPACE_DIR/patch/<patch-file>
   ```
5. Read the code and run tests. Be opinionated — challenge the patch on simplicity, UNIX philosophy, KISS, and security. Mark `needs-work` if any are lacking.
6. Get the HEAD commit hash:
   ```
   REVIEWED_COMMIT=$(git rev-parse HEAD)
   ```
7. Write a review file with a datetime prefix:
   ```
   TIMESTAMP=$(date +%Y%m%d-%H%M%S)
   ```
   File: `$WORKSPACE_DIR/patch/${TIMESTAMP}-<repo>-<agent>-<short-name>.review-<reviewer>.md`

   Format:
   ```
   Reviewed-commit: <hash>
   Verdict: accept | needs-work

   ## Summary
   ...

   ## Comments
   ...

   ## Test results
   ...
   ```

8. **If accepting**: amend the commit to add `Reviewed-by:`, then produce the accepted patch into the merge queue:
   ```
   git commit --amend -m "$(git log -1 --format=%B)

   Reviewed-by: <reviewer>"
   TIMESTAMP=$(date +%Y%m%d-%H%M%S)
   git format-patch main --stdout > $WORKSPACE_DIR/queue/${TIMESTAMP}-<repo>-<agent>-<short-name>.patch
   ```
   The human applies patches from `$WORKSPACE_DIR/queue/` — every patch there has `Reviewed-by:` tags.

## Revising patches
When asked to address review feedback:

1. Read the review file (verdict: needs-work) in `$WORKSPACE_DIR/patch/`.
2. The `Reviewed-commit:` hash identifies which patch version was reviewed.
3. Fix the issues in `~/work/<repo>`, make new commits on your branch.
4. Produce a new patch with a new timestamp (the old patch stays as history):
   ```
   TIMESTAMP=$(date +%Y%m%d-%H%M%S)
   git checkout -b squash-tmp main
   git merge --squash <branch-name>
   git commit -m "<descriptive message>"
   git format-patch main --stdout > $WORKSPACE_DIR/patch/${TIMESTAMP}-<repo>-<agent>-<short-name>.patch
   ```

## Rules
- NEVER write to $WORKSPACE_DIR/ except $WORKSPACE_DIR/patch/ and $WORKSPACE_DIR/queue/. In particular, NEVER modify, create, or delete files under $WORKSPACE_DIR/repos/. Corrupting host repos is unrecoverable.
- NEVER enter plan mode. Do the work directly and produce a patch.
- NEVER push to any remote
- NEVER create pull requests
- Always run tests before producing a patch
- Make clean, atomic commits with good messages
