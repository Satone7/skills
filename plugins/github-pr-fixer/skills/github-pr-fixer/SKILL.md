---
name: github-pr-fixer
description: >
  Automated GitHub PR fixer that reads review feedback, implements code fixes, runs tests, and
  replies to reviewers until all review threads are resolved. Use this skill whenever the user says
  "fix PR review", "address review comments", "/github-pr-fixer", "respond to PR feedback",
  "fix this PR's review", "handle PR review", or asks to start an automated fix cycle on a
  GitHub pull request that has received review feedback.
---

# GitHub PR Fixer

You are a PR fixer. Given a PR number, read review feedback from GitHub, implement fixes, run
tests, commit/push, reply to reviewers, and resolve threads. Loop until all feedback is addressed.

## Prerequisites

Requires the `gh-pr-review` extension for thread management:

```bash
gh extension install agynio/gh-pr-review
```

Verify: `gh pr-review --help`

If the extension is not installed, install it automatically before proceeding.

## Input

The user provides a PR number: `PR#11`, `#11`, or just `11`.

On startup, extract the PR number and begin Phase 1.

## Phase 1 — Get PR Context

```bash
# Repo info
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)

# PR details
gh pr view <PR> --json number,title,state,headRefName,baseRefName,author

# Ensure we're on the PR branch
gh pr checkout <PR>
```

## Phase 2 — Check for Unresolved Feedback

### Review threads (primary)

```bash
gh pr-review threads list --pr <PR> --repo {owner}/{repo}
```

### PR comments (fallback)

If no review threads exist, check for regular PR comments:

```bash
gh pr view <PR> --comments --json comments --jq '.comments[] | {body, author: .author.login, createdAt: .createdAt}'
```

### Existing review comments

```bash
gh api repos/{owner}/{repo}/pulls/<PR>/comments --jq '.[] | {id,path,line,body,user: .user.login,pull_request_review_id}'
```

### Decision

- **No unresolved threads and no new comments** → wait 2 minutes, re-check (up to 3 consecutive
  empty checks). If still clean → output `✅ All review feedback addressed` and **stop**
- **Unresolved threads or new comments found** → proceed to Phase 3

## Phase 3 — Analyze Feedback

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

## Phase 4 — Implement Fixes

Edit files using the Edit tool. Follow these principles:

- Match existing code patterns in the repo (naming, imports, file organization)
- Follow `AGENTS.md` or `CLAUDE.md` guidelines if they exist
- Add/update tests for any new logic
- One logical change per fix — don't mix unrelated changes

After all fixes are applied, proceed to Phase 5 to verify before committing.

## Phase 5 — Verify Changes

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

## Phase 6 — Commit and Push

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

## Phase 7 — Reply to Review Threads

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

## Phase 8 — Wait and Resolve

1. After replying to ALL threads, wait 2 minutes for possible follow-ups
2. Re-check threads: `gh pr-review threads list --pr <PR> --repo {owner}/{repo}`
3. **If new replies found** → go back to Phase 3 (analyze new feedback)
4. **If no new replies** → resolve threads:

```bash
# Resolve outdated threads first (code changed, comment no longer applies)
gh pr-review threads resolve --pr <PR> --repo {owner}/{repo} --thread-id <OUTDATED_THREAD_ID>

# Then resolve active threads that you've replied to
gh pr-review threads resolve --pr <PR> --repo {owner}/{repo} --thread-id <ACTIVE_THREAD_ID>
```

## Phase 9 — Loop

After resolving threads:

1. Go back to **Phase 2** to check for any new review activity
2. If the reviewer has submitted an **APPROVE** review → output `✅ Reviewer approved — all done`
   and **stop**
3. Continue until no unresolved threads remain

**Stop conditions:**
- All threads resolved AND no new feedback after waiting
- Reviewer has explicitly approved the PR
- 5 consecutive rounds where no new feedback appears → output summary and stop

## Round Tracking

At the start of each round, announce: `--- Fix Round N ---`

Keep a concise log of what was fixed each round so you don't re-do work.
