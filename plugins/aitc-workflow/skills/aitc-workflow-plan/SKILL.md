---
name: aitc-workflow-plan
version: 1.0.0
description: >
  Manually invoked — NOT auto-triggered. Generate an execution plan for a long-running task.
  User must explicitly request it (e.g., "use aitc-workflow-plan", "create a plan", "plan this task").
  Analyzes tasks, aligns with user via brainstorming, generates a plan file with team structure
  and acceptance criteria, and initializes the task SKILL directory. After completion, prompts
  the user to invoke aitc-workflow-execute.
---

# AITC Workflow — Plan Mode

Generate an execution plan for a long-running task. This is the first of three workflow SKILLs:
**Plan** (this one) → **Execute** → **Lifecycle**.

## Why Plan Before Execute

A plan written with incomplete information produces wrong teammate assignments, missed dependencies, and unnecessary rework. The brainstorming step (§1.3) catches these before they become execution failures. The committed plan also provides the clean baseline that the plan-editing subagent's atomicity checks depend on.

## Workflow

### 1.1 Read Project Context

Read the project's CLAUDE.md to understand available project skills, conventions, and constraints. This grounds the plan in what the project actually has.

### 1.2 Analyze Each Task

For each task: identify its nature, estimate which steps will dominate, determine appropriate worker model (default `sonnet`; use `opus` only for novel problem-solving or cross-referencing large codebases). This initial analysis is provisional — every task will be re-audited before execution.

### 1.3 Align with User via Brainstorming

Present your analysis. Use the brainstorming pattern: present options with reasoning, one question at a time. Cover: execution order, model selection, priority and scope.

### 1.4 Generate Plan File

Write to `docs/plans/<batch-name>-<date>.md`. Use `templates/plan-template.md` as the skeleton.

Key points to include:
- **Team Structure** — Explain teammate vs subagent distinction. Include a concrete `Agent()` example. The `model` field must be `opus` or `sonnet` for workers, `haiku` for Guardian. Do not use `isolation="worktree"` — the Lead creates worktrees manually.
- **Task table** with status markers: `[ ]` pending | `[>]` in-progress | `[x]` completed | `[~]` re-planned | `[-]` abandoned
- **Per-task details**: scope, phases, references, model and rationale
- **Execution Strategy**: serial/parallel, pre-requisites, isolation approach
- **Acceptance Criteria**: per-teammate checklist and cross-task criteria

### 1.5 Initialize Task SKILL Directory

Verify no other `skills/aitc-task-xxx/` exists. Only one active directory at any time. If a stale one exists, ask the user whether to archive it. Create `skills/aitc-task-<batch-name>/`.

### 1.6 Commit the Plan

The plan file must be committed before Execute mode begins. This establishes a clean baseline for the plan-editing subagent's atomicity checks during execution:

```bash
git add docs/plans/<batch>.md skills/aitc-task-<batch>/
git commit -m "plan: add execution plan for <batch-name>"
```

### 1.7 Report and Hand Off

Tell the user:
- Plan saved to: `docs/plans/<file>.md`
- Task SKILL directory: `skills/aitc-task-<batch>/`
- **Next step**: invoke `aitc-workflow-execute` to run this plan
