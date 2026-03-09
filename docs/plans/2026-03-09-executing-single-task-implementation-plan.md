# executing-single-task Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a new standalone plugin `executing-single-task` that executes one `writing-plans-plus` task from `find-next-task` output, updates `passes` in the plan JSON, and commits once per task.

**Architecture:** Implement as a single SKILL.md with a strict machine-parseable input/output contract, plus minimal helper guidance for JSON-safe updates and per-task git commits. Use `using-superpowers` at runtime to select verification skills when verification is unclear.

**Tech Stack:** Claude Code skills (`SKILL.md`), `.claude-plugin` plugin manifests, git

---

### Task 1: Create plugin skeleton and marketplace entry

**Files:**
- Create: `plugins/executing-single-task/.claude-plugin/plugin.json`
- Create: `plugins/executing-single-task/skills/executing-single-task/SKILL.md`
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Create plugin manifest**

Create `plugins/executing-single-task/.claude-plugin/plugin.json`:
```json
{
  "name": "executing-single-task",
  "description": "Execute exactly one writing-plans-plus task (from find-next-task output) in a low-context subagent, update the plan JSON task passes field, and create exactly one git commit for that task. Use this when you are executing tasks one-by-one downstream of find-next-task.",
  "version": "0.1.0"
}
```

**Step 2: Add plugin to marketplace**

Modify `.claude-plugin/marketplace.json` to append:
```json
{
  "name": "executing-single-task",
  "source": "./plugins/executing-single-task",
  "description": "Execute exactly one writing-plans-plus task (from find-next-task output) in a low-context subagent, update the plan JSON task passes field, and create exactly one git commit for that task."
}
```

**Step 3: Add SKILL.md placeholder**

Create `plugins/executing-single-task/skills/executing-single-task/SKILL.md` with YAML frontmatter and a minimal stub (name + description + empty sections) so the plugin is structurally valid.

**Step 4: Commit**

Run:
```bash
git add plugins/executing-single-task/.claude-plugin/plugin.json \
  plugins/executing-single-task/skills/executing-single-task/SKILL.md \
  .claude-plugin/marketplace.json
git commit -m "feat(executing-single-task): add plugin skeleton"
```

---

### Task 2: Implement executing-single-task SKILL contract and workflow

**Files:**
- Modify: `plugins/executing-single-task/skills/executing-single-task/SKILL.md`
- Reference: `plugins/find-next-task/skills/find-next-task/SKILL.md`
- Reference: `plugins/writing-plans-plus/skills/writing-plans-plus/SKILL.md`

**Step 1: Define strict input contract**

In SKILL.md, specify that the skill accepts the full `find-next-task` output JSON, and must fail-fast when:
- `error != null`
- `selection_required == true`
- `next_task == null`

**Step 2: Define strict output contract**

Specify “single JSON object only, no prose” output with fields:
- `plan_file`, `task_id`, `result`, `passes_written`, `commit`, `verification_evidence`, `errors`

**Step 3: Define execution boundaries**

Specify that the subagent should:
- Re-read `plan_file` and locate task by `next_task.id` (source of truth)
- Prefer `task.files` (create/modify/test) as the boundary for file discovery
- Avoid repository-wide exploration unless explicitly required by the task steps

**Step 4: Define verification decision rules**

Specify the verification decision priority:
1. Explicit verification commands in `task.steps`
2. Evidence-backed checks derived from `validation_criteria` (if present)
3. If still ambiguous: load `using-superpowers` and then the most relevant verification skill(s) and follow them to produce evidence-backed verification

**Step 5: Define plan update rules**

Specify that only `tasks[].passes` for the matching task is updated:
- `passes=true` only when verification evidence supports it
- `passes=false` otherwise
- No other fields are added/removed/reordered

**Step 6: Define git commit rules**

Specify exactly one commit per executed task:
- Commit includes both code changes and plan JSON changes for that task
- Commit message format based on task id/title (document the exact pattern)

**Step 7: Commit**

Run:
```bash
git add plugins/executing-single-task/skills/executing-single-task/SKILL.md
git commit -m "feat(executing-single-task): define execution and update protocol"
```

---

### Task 3: Add initial skill-creator eval prompts

**Files:**
- Create: `plugins/executing-single-task/evals/evals.json`

**Step 1: Create evals file**

Create `plugins/executing-single-task/evals/evals.json` with 3 prompts (no assertions yet):
- Happy path: clear steps + explicit verification, writes passes true, commits
- Ambiguous verification: requires loading verification skills to decide passes
- Blocked: invalid plan_file / missing task id → no modifications, structured error JSON

**Step 2: Commit**

Run:
```bash
git add plugins/executing-single-task/evals/evals.json
git commit -m "test(executing-single-task): add initial eval prompts"
```

---

### Task 4: Run iteration-1 evals (with-skill and without-skill) and review results

**Files:**
- Create (untracked): `plugins/executing-single-task/skills/executing-single-task-workspace/iteration-1/**`

**Step 1: Prepare workspace directory**

Create a workspace directory adjacent to the skill folder:
- `plugins/executing-single-task/skills/executing-single-task-workspace/iteration-1/`

Do not commit workspace outputs.

**Step 2: Spawn eval runs (with-skill and baseline)**

For each eval prompt:
- Run once with the skill path: `plugins/executing-single-task/skills/executing-single-task`
- Run once without any skill

Store each run’s outputs under:
- `.../with_skill/outputs/`
- `.../without_skill/outputs/`

**Step 3: Draft assertions and grade**

Add objective assertions for:
- Output is JSON-only (no prose)
- Plan JSON changes limited to `passes` for that task id
- Commit behavior matches spec (1 commit when applicable)

Record `grading.json` per run.

**Step 4: Aggregate and generate review**

Use skill-creator tooling to generate benchmark and a review artifact (viewer or static html depending on environment).

**Step 5: Iterate**

Based on review feedback:
- Tighten SKILL.md rules where the agent rationalizes or violates constraints
- Repeat iteration-2 as needed

---

### Task 5: Stabilize description triggering and finalize plugin versioning

**Files:**
- Modify: `plugins/executing-single-task/.claude-plugin/plugin.json`
- Modify: `plugins/executing-single-task/skills/executing-single-task/SKILL.md`

**Step 1: Optimize description**

Refine the SKILL.md frontmatter description so it reliably triggers when:
- User is executing a task returned by find-next-task
- User asks to “execute this single task and update plan json”

**Step 2: Bump version**

If the behavior changed meaningfully during iteration, bump plugin version to `0.1.1`.

**Step 3: Commit**

Run:
```bash
git add plugins/executing-single-task/.claude-plugin/plugin.json \
  plugins/executing-single-task/skills/executing-single-task/SKILL.md
git commit -m "chore(executing-single-task): refine description and bump version"
```

