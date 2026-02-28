
# Task: Merge Remote Changes with Local Uncommitted Work

## Situation

There are **uncommitted changes** on the local machine, and the remote `main` branch on GitHub has **newer commits** that were pushed from a different session. We need to safely combine both without losing any work.

## Method: Stash → Pull → Apply

This is the safest merge path. Local changes get temporarily shelved while remote updates come in, then local changes are re-applied on top.

## Execute These Steps In Order

### Step 1 — Stash local changes

Save all uncommitted local changes to the stash:

```bash
git stash
```

Verify stash was saved:

```bash
git stash list
```

You should see at least one entry like `stash@{0}: WIP on main: ...`

### Step 2 — Pull remote changes

Pull the latest commits from GitHub:

```bash
git pull origin main
```

### Step 3 — Re-apply stashed local changes

Apply the stashed changes on top of the updated main:

```bash
git stash pop
```

### Step 4 — Handle the result

**If Step 3 applies cleanly (no conflicts):**

```bash
git add .
git commit -m "merge local changes with remote updates"
git push origin main
```

**If Step 3 reports merge conflicts:**

```bash
# List which files have conflicts
git status

# Open each conflicting file and resolve the conflicts
# Look for these markers and keep the correct version:
#   <<<<<<< Updated upstream
#   (remote changes)
#   =======
#   (your local changes)
#   >>>>>>> Stashed changes

# After resolving ALL conflicts:
git add .
git commit -m "merge local changes with remote updates, resolved conflicts"
git push origin main
```

## Step 5 — Verify

After pushing, confirm everything looks correct:

```bash
git log --oneline -5
```

Report the last 5 commits so we can verify the merge was successful.

## Rules

- **Do NOT force push** (`--force`). If push is rejected, stop and report the error.
- **Do NOT discard** any local changes or remote changes. Both must be preserved.
- **If a conflict is ambiguous** (unclear which version to keep), stop and ask before resolving.
- **If `git stash pop` fails** with "CONFLICT", do NOT run `git stash drop` — the stash is still recoverable.
- **If anything unexpected happens** at any step, stop immediately and report what happened before proceeding.
