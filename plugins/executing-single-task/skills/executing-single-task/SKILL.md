---
name: executing-single-task
description: Execute exactly one writing-plans-plus task from find-next-task output in a low-context subagent, then update the plan JSON (passes only) and create exactly one git commit for that task. Use this whenever you are asked to run “the next task” or “a single task” and write back passes.
---

# Executing Single Task

## Overview

This skill is the execution counterpart to `find-next-task`. It takes a single task (via the full `find-next-task` output JSON), executes it with minimal context, verifies results with evidence, updates the plan JSON by setting only `passes`, and commits once.

**Announce at start:** "I'm using the executing-single-task skill to execute exactly one task and update passes."

## Required First Step

Invoke `using-superpowers` before any response or action. If any additional skill might apply (even 1%), invoke it before proceeding.

## Input

The input is the full JSON output of `find-next-task` (verbatim). Treat `plan_file` as the source of truth.

**Fail-fast conditions (no file changes):**
- `error != null`
- `selection_required == true`
- `next_task == null`
- `plan_file` missing or not an absolute path
- `next_task.id` missing

## Output

Output exactly one JSON object and nothing else (no prose, no markdown fences).

```json
{
  "plan_file": "/abs/path/to/plan.json",
  "task_id": 4,
  "result": "SUCCESS",
  "passes_written": true,
  "commit": {
    "created": true,
    "sha": "abc123",
    "message": "feat(task): 4 Login Page Implementation"
  },
  "verification_evidence": [
    {
      "kind": "command",
      "command": "npm test",
      "exit_code": 0,
      "summary": "PASS (all tests)"
    }
  ],
  "errors": []
}
```

`result` values:
- `SUCCESS`: Task executed, verified, `passes` set to `true`, commit created.
- `FAIL`: Task executed but verification failed or incomplete, `passes` kept/set to `false`, commit may or may not exist (see rules).
- `BLOCKED`: Cannot proceed (invalid input, missing task, parse failure). No changes made.

## Workflow

### 1. Validate input JSON

If fail-fast conditions match, output `result: "BLOCKED"` with an `errors[]` entry and stop.

### 2. Load plan and locate task

1. Read `plan_file` and parse JSON.
2. Locate the task whose `id` matches `next_task.id`.
3. If not found, output `result: "BLOCKED"` and stop.

### 3. Execute steps with strict boundaries

Execute `task.steps` in order.

**Boundaries:**
- Prefer `task.files.create/modify/test` as the only files you read/modify.
- Do not perform broad repo exploration unless a step explicitly requires it.
- If a step is ambiguous, invoke the most relevant skill before acting.

### 4. Verification and pass/fail decision

You may set `passes: true` ONLY with fresh, evidence-backed verification.

Verification priority:
1. Explicit verification commands in `task.steps`
2. Evidence-backed checks derived from `validation_criteria` (if present)
3. If still ambiguous: invoke `using-superpowers`, then invoke the most relevant verification skill(s) and follow them to obtain verification evidence

Record each verification as an entry in `verification_evidence`.

### 5. Update plan JSON (passes only)

Update only the located task’s `passes` field in `plan_file`.
- Write `passes: true` only when verification evidence supports success.
- Otherwise write or keep `passes: false`.
- Do not add/remove/reorder any other fields.

### 6. Git commit (exactly one)

Create exactly one commit for this task.

Commit must include:
- Any code changes made for the task
- The plan JSON change (the updated `passes`)

Commit message:
- `feat(task): <id> <title>` when implementing functionality
- `fix(task): <id> <title>` when fixing a bug
- Otherwise: `chore(task): <id> <title>`

If `result: "BLOCKED"`, do not commit.

### 7. Emit final JSON output

Return the JSON object matching the schema above. No additional text.
