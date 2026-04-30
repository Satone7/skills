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

For each task, assess these dimensions:

| Dimension | Question | Affects |
|-----------|----------|---------|
| Complexity | How many distinct phases or sub-problems? | Teammate count, model selection |
| Dependencies | Does it require output from a prior task? | Execution order |
| Novelty | Is this a known pattern or an open-ended investigation? | Model: `opus` for novel, `sonnet` for known patterns |
| Risk | Could failure here block other tasks? | Priority, whether to assign `opus` |
| Scope clarity | Can the task be described in a single prompt? | Whether to split into emergent tasks now |

This initial analysis is provisional — every task will be re-audited before execution. Default model is `sonnet`; use `opus` only when novelty or risk demands it.

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

### 1.6 Create Instance Task SKILLs

Instance task SKILLs parameterize project skills with concrete values for this session. All placeholders are known after plan generation — fill them now so Execute mode can use them directly.

Use `Skill("task-skills-creator")` in instance mode. Provide all parameters in the invocation so the SKILL does not need to re-ask:

```
Skill("task-skills-creator")

Create an instance task SKILL for base skill "guardian" with these parameters (do not re-ask — all values are provided):
- team_name: <from plan>
- batch_name: <from plan>
- instance_skill_path: skills/aitc-task-<batch>/guardian-<batch>.md
- log_file_path: docs/plans/guardian-log-<batch>.md
- notes_file_path: /tmp/guardian-<team-name>-notes.txt
- plan_file_path: docs/plans/<batch>.md
- task_count: <from plan>
- cron_interval: "*/5 * * * *"
```

After the SKILL completes, verify the instance file exists and contains no `<...>` placeholders.

Instance task SKILLs — unlike discovery-based task SKILLs — are created by the Lead during Plan mode because all parameter values are known at plan time.

### 1.7 Commit the Plan

The plan file and instance task SKILLs must be committed before Execute mode begins:

```bash
git add docs/plans/<batch>.md skills/aitc-task-<batch>/
git commit -m "plan: add execution plan for <batch-name>"
```

### 1.8 Report and Hand Off

Tell the user:
- Plan saved to: `docs/plans/<file>.md`
- Task SKILL directory: `skills/aitc-task-<batch>/`
- Guardian instance created
- **Next step**: invoke `aitc-workflow-execute` to run this plan
