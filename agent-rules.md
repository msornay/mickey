# Agent Rules

You are a developer agent working inside a Docker sandbox.

## Workspace layout
- ~/src/ is synced to the host. DO NOT modify files here directly.
- ~/work/ is your local workspace (not synced). Clone repos here and do all work here.
- ~/src/patches/ is the shared patch mailing list (submissions, reviews, revisions).
- ~/src/queue/ is the merge queue (accepted patches with `Reviewed-by:` tags, ready for the human to apply).

## Starting work
1. Clone the repo(s) you need from ~/src/ into ~/work/:
     git clone ~/src/<repo> ~/work/<repo>
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
git format-patch main --stdout > ~/src/patches/${TIMESTAMP}-<repo>-<agent>-<short-name>.patch
```

This writes the patch to the synced directory so the host can pick it up.

## Reviewing patches
When asked to review a patch:

1. Find the latest patch matching the name pattern in `~/src/patches/`.
2. Parse the repo name from the filename.
3. Clone the repo into `~/work/` if not already there, or reset to main:
   ```
   cd ~/work/<repo> && git checkout main && git reset --hard main
   ```
4. Apply the patch:
   ```
   git am ~/src/patches/<patch-file>
   ```
5. Read the code and run tests.
6. Get the HEAD commit hash:
   ```
   REVIEWED_COMMIT=$(git rev-parse HEAD)
   ```
7. Write a review file with a datetime prefix:
   ```
   TIMESTAMP=$(date +%Y%m%d-%H%M%S)
   ```
   File: `~/src/patches/${TIMESTAMP}-<repo>-<agent>-<short-name>.review-<reviewer>.md`

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
   git format-patch main --stdout > ~/src/queue/${TIMESTAMP}-<repo>-<agent>-<short-name>.patch
   ```
   The human applies patches from `~/src/queue/` — every patch there has `Reviewed-by:` tags.

## Revising patches
When asked to address review feedback:

1. Read the review file (verdict: needs-work) in `~/src/patches/`.
2. The `Reviewed-commit:` hash identifies which patch version was reviewed.
3. Fix the issues in `~/work/<repo>`, make new commits on your branch.
4. Produce a new patch with a new timestamp (the old patch stays as history):
   ```
   TIMESTAMP=$(date +%Y%m%d-%H%M%S)
   git checkout -b squash-tmp main
   git merge --squash <branch-name>
   git commit -m "<descriptive message>"
   git format-patch main --stdout > ~/src/patches/${TIMESTAMP}-<repo>-<agent>-<short-name>.patch
   ```

## Rules
- NEVER modify anything in ~/src/ except writing patch files to ~/src/patches/ and ~/src/queue/
- NEVER push to any remote
- NEVER create pull requests
- Always run tests before producing a patch
- Make clean, atomic commits with good messages
