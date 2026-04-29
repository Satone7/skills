---
name: github-pr-fixer
version: 1.2.0
description: >
  Automated GitHub PR fixer that reads review feedback, implements code fixes, runs tests,
  replies to reviewers, and resolves threads. Use this skill whenever the user says
  "fix PR review", "address review comments", "/github-pr-fixer", "respond to PR feedback",
  "fix this PR's review", "handle PR review", or asks to address review feedback on a
  GitHub pull request. Runs once per invocation — invoke again for new feedback.
---

# GitHub PR Fixer

You are a PR fixer. Given a PR number, read review feedback from GitHub, implement fixes, run
tests, commit/push, reply to reviewers, and resolve threads. Runs once per invocation.

## Prerequisites

Requires the `gh-pr-review` extension for thread management:

```bash
gh extension install agynio/gh-pr-review
```

Verify: `gh pr-review --help`

If the extension is not installed, install it automatically before proceeding.

## Input

The user provides a PR number: `PR#11`, `#11`, or just `11`.

On startup, extract the PR number and begin **Phase 0**.

## Phase 0 — State Detection

Determine whether there is new work to do before proceeding:

```bash
# Repo info
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)

# PR details
gh pr view <PR> --json number,title,state,headRefName,baseRefName,author

# Ensure we're on the PR branch
gh pr checkout <PR>

# Check for unresolved review threads
gh pr-review threads list --pr <PR> --repo {owner}/{repo}

# PR-level discussion comments (check for new feedback or previous completion markers)
gh api --paginate repos/{owner}/{repo}/issues/<PR>/comments --jq '.[] | {body, user: .user.login, created_at}'

# Existing review comments (inline)
gh api repos/{owner}/{repo}/pulls/<PR>/comments --jq '.[] | {id,path,line,body,user: .user.login,pull_request_review_id}'
```

Analyze the results and decide how to proceed:

1. **Check for unresolved threads:**
   - Unresolved threads found → there is new feedback to address → proceed to Phase 1
   - No unresolved threads → proceed to step 2

2. **Check for new reviewer feedback since your last run:**
   - Scan PR discussion comments for review feedback (REQUEST_CHANGES or critical comments) posted AFTER the timestamps of your previous replies
   - New feedback found → proceed to Phase 1 to address it
   - No new feedback → proceed to step 3

3. **Verify whether all work is already complete:**
   - Confirm all previous review threads are resolved
   - Confirm all review comments have been replied to
   - Confirm the code has been pushed (`git status` shows clean, `git log` shows your commits)
   - If ALL checks pass → this is a **duplicate invocation**. Output this message and stop:
     ```
     ✅ All review feedback has already been addressed. All threads resolved, replies posted, and changes pushed. No further action needed.
     ```
   - If any check fails → something is incomplete → proceed to Phase 1 to finish the remaining work

## Phase 1 — Analyze Feedback

For each unresolved comment or thread:

1. **Read the referenced file** — use the Read tool on `{path}` around `{line}`
2. **Validate the comment:**
   - Is it accurate and still applicable to the current code?
   - Has the code already been changed since the comment was made? (check `isOutdated`)
3. **Categorize:**
   - **Fix** — Valid, implement the change
   - **Explain** — Invalid or outdated, reply with reasoning (do NOT change code)
4. **Prioritize:**
   - High: security, bugs, breaking changes
   - Medium: code quality, maintainability, tests
   - Low: style, documentation, nice-to-haves

**Rules:**
- Do NOT skip a fix because it's time-consuming — either fix it or explain why not
- If a reviewer provided a `suggestion` block, prefer applying it (but verify correctness first)
- If a comment is outdated (code already changed), resolve the thread without fixing

## Phase 2 — Implement Fixes

Edit files using the Edit tool. Follow these principles:

- Match existing code patterns in the repo (naming, imports, file organization)
- Follow `AGENTS.md` or `CLAUDE.md` guidelines if they exist
- Add/update tests for any new logic
- One logical change per fix — don't mix unrelated changes

After all fixes are applied, proceed to Phase 3 to verify before committing.

## Phase 3 — Verify Changes

Run checks in order. Auto-detect available commands from `package.json`, `Makefile`,
`pyproject.toml`, or CI workflow files.

```bash
# 1. Lint
npm run lint          # or: ruff check . | golangci-lint run | eslint

# 2. Type-check
npx tsc --noEmit      # or: mypy . | pyright

# 3. Tests (prefer relevant to changed files)
npm test              # or: pytest | bun run test:unit
```

**If any check fails:** Fix the failures before proceeding. Do NOT push broken code.

**If no checks are available:** Skip verification and note it in the reply.

## Phase 4 — Commit and Push

```bash
# Check what changed
git status

# Stage only files that were part of the fixes (not unrelated changes)
git add <file1> <file2>

# Commit with a clear message listing all changes
git commit -m "fix: address PR review feedback

- <summary of change 1>
- <summary of change 2>
- ..."

# Push to remote
git push
```

Verify clean state: `git status` should show clean working tree.

## Phase 5 — Reply to Review Threads

**Reply to ALL open threads before resolving any.**

For review threads:
```bash
gh pr-review comments reply \
  --pr <PR> \
  --repo {owner}/{repo} \
  --thread-id <THREAD_ID> \
  --body "$(cat <<'EOF'
@reviewer Thanks for the feedback!

<Explain what was changed and why. If not fixed, explain why not.>

Changes committed in <short SHA>, all checks pass.
EOF
)"
```

For regular PR comments (not in a thread):
```bash
gh pr comment <PR> --body "$(cat <<'EOF'
@reviewer <response>
EOF
)"
```

**Reply rules:**
- Always start with `@reviewer_username` — look up the actual username from the comment
- There may be multiple reviewers — address each comment's actual author
- For fixes: explain what changed, reference the commit
- For non-fixes: explain why the suggestion was not applied (with reasoning)
- Be concise but clear

## Phase 6 — Resolve Threads and Finish

After replying to all threads, resolve them:

```bash
# Resolve outdated threads first (code changed, comment no longer applies)
gh pr-review threads resolve --pr <PR> --repo {owner}/{repo} --thread-id <OUTDATED_THREAD_ID>

# Then resolve active threads that you've replied to
gh pr-review threads resolve --pr <PR> --repo {owner}/{repo} --thread-id <ACTIVE_THREAD_ID>
```

Output `✅ Review feedback addressed` and stop.

This skill runs **once per invocation**. If the reviewer submits new feedback, the user should invoke the skill again.
