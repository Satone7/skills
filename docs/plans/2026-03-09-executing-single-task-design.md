# executing-single-task Design

## Goal

Create a downstream skill for `find-next-task` that enables a low-context subagent to execute exactly one `writing-plans-plus` task end-to-end, update the plan JSON (`passes` only), and commit the code changes for that task.

## Non-Goals

- Multi-task execution, batching, or checkpoint workflows (belongs to `executing-plans` / `subagent-driven-development`).
- Plan selection or dependency resolution (belongs to `find-next-task`).
- Enriching task completion metadata (`completed_at`, `completed_by`, `notes`) or issue management (`issue`) for now.
- Owning branch/worktree setup (belongs to `using-git-worktrees` / upstream controller).

## Inputs

The skill receives as its sole input a JSON object that is the full output of `find-next-task`:

- `selection_required` MUST be `false`
- `error` MUST be `null`
- `next_task` MUST be a task object (not `null`)
- `plan_file` MUST be an absolute path to the plan JSON file

The skill MUST treat the `plan_file` as the source of truth and re-read it before writing updates.

## Outputs

The skill outputs a single JSON object and nothing else, intended for machine parsing by an upstream controller. Minimum fields:

- `plan_file`: string
- `task_id`: string|number
- `result`: `"SUCCESS"` | `"FAIL"` | `"BLOCKED"`
- `passes_written`: boolean
- `commit`: `{ "created": boolean, "sha": string|null, "message": string|null }`
- `verification_evidence`: array of `{ "kind": "command", "command": string, "exit_code": number|null, "summary": string }`
- `errors`: array of `{ "code": string, "message": string }`

## Execution Model (Scheme A)

### High-level Flow

1. Load `using-superpowers` and obey its rule: invoke relevant skills before responding or acting.
2. Validate input shape (fatal errors stop immediately, no file changes).
3. Read `plan_file`, parse JSON, locate the task by `next_task.id`.
4. Execute the task strictly according to `task.steps`, using `task.files` as the boundary for file reads/edits when present.
5. Determine pass/fail via verification evidence:
   - Prefer explicit verification commands inside `task.steps`.
   - If `validation_criteria` exists, convert each item into an evidence-backed check (tests/commands/repro steps).
   - If verification method is ambiguous, use `using-superpowers` to load the most relevant verification skill(s) and follow them.
6. Update the plan JSON in-place: set only `tasks[].passes` for this `task_id`.
7. Create exactly one git commit for this task.
8. Output the JSON report.

### Fail-fast and Safety

- If `next_task.passes` is already `true`, stop with `result: "BLOCKED"` and do not change files.
- If plan JSON cannot be parsed, stop with `result: "BLOCKED"` and do not change files.
- If task id cannot be found in the plan file, stop with `result: "BLOCKED"` and do not change files.
- If execution fails or verification fails, keep `passes: false`, still commit only if the task’s steps intentionally include partial progress; otherwise do not commit.

## Plan JSON Update Rules

- Update only `tasks[i].passes` for the matching `task_id`.
- Do not add, remove, or reorder fields.
- Do not write empty optional fields (no `issue: []`).

## Git Commit Rules

- Exactly one commit per executed task.
- Commit message format:
  - `feat(task): <id> <title>` for feature-like tasks
  - `fix(task): <id> <title>` for bugfix tasks
  - Fallback: `chore(task): <id> <title>`
- If no code changes occurred but `passes` is updated, commit the plan JSON update.

## Plugin Packaging

Ship `executing-single-task` as a standalone plugin:

- `plugins/executing-single-task/.claude-plugin/plugin.json`
- `plugins/executing-single-task/skills/executing-single-task/SKILL.md`
- Add plugin to `.claude-plugin/marketplace.json`

## Test & Evaluation Plan (skill-creator style)

Create 2-3 realistic eval prompts that exercise:

1. Happy path: task has clear steps + explicit verification, updates `passes: true`, commits.
2. Missing verification: task lacks clear verification, skill uses `using-superpowers` to choose a verification path, still produces evidence and decides pass/fail.
3. Blocked path: task id missing / plan parse failure, exits cleanly without modifications.

Use baseline runs with no skill and with-skill runs in parallel, then grade:

- Output is strict JSON only
- Updates only `passes`
- Does not mutate unrelated tasks
- Creates one commit (or explains why blocked)

