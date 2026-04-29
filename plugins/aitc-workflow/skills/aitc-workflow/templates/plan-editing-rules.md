---
name: plan-editing-rules
description: Formal editing rules for AITC workflow plan documents — status markers, frozen prefix constraint, and task reordering
type: task
task-type: instance
instance-of: aitc-workflow
created: 2026-04-29
status: active
---

# Plan Editing Rules

This document defines the formal rules for modifying an AITC workflow plan document (`docs/plans/<batch>.md`) during execution. Plan edits must follow these rules to prevent retroactive manipulation and ensure the plan remains a trustworthy record of what happened.

## Task Status Markers

Every task in the plan's `## Tasks` table and in individual task sections must carry exactly one status marker:

| Marker | Status | Meaning |
|--------|--------|---------|
| `[ ]` | pending | Not yet started. No teammate assigned. |
| `[>]` | in-progress | A teammate is actively working on this task. |
| `[x]` | completed | Teammate passed verification, worktree merged. |
| `[~]` | re-planned | Task cannot proceed as originally scoped. It has been split, reordered, or redefined elsewhere in the plan. The new location or form must be referenced. |
| `[-]` | abandoned | Task is no longer needed — either found to be unnecessary, impossible, or superseded by discoveries. Reason must be recorded in Amendments. |

A task without a marker is **invalid**. The plan must never contain unmarked tasks.

## Frozen Prefix Rule

This is the fundamental constraint on plan editing. It prevents retroactive modification of completed work.

### Definition

The **freeze point** is the position after the last `[x]` completed task. All tasks before the freeze point form the **frozen prefix**.

### Rules

1. **No insertion**: New tasks cannot be inserted into the frozen prefix.
2. **No unmarked tasks**: Every task in the frozen prefix must carry a status marker — `[ ]` (pending) is forbidden in the frozen prefix.
3. **Only terminal statuses**: Tasks in the frozen prefix can only be `[x]`, `[~]`, or `[-]`. `[>]` (in-progress) is not allowed — if a task was in-progress and the next task completed, something is wrong.
4. **No reordering within the frozen prefix**: The order of tasks in the frozen prefix is immutable.
5. **Freeze point only moves forward**: The freeze point can never retreat. Once a task is frozen, it stays frozen.

### Rationale

If task 1.5 is completed but 1.3 is still unmarked, the plan has a gap — work proceeded past an unresolved task. This either means 1.3 was implicitly abandoned (and should be marked `[-]`) or re-planned (and should be marked `[~]` with a reference to where it went). The frozen prefix rule forces these decisions to be made explicitly.

### Enforcement

When editing the plan:

1. Scan the task list from top to bottom.
2. Find the last task with `[x]`.
3. Everything before that point is frozen.
4. Verify every task in the frozen prefix has a terminal marker.
5. Verify no `[ ]` or `[>]` appear in the frozen prefix.

## Task Numbering

Use hierarchical numbering to express task decomposition:

```
Task 1: <name>                    # top-level task
├── Task 1.1: <name>              # sub-task
├── Task 1.2: <name>              # sub-task
│   ├── Task 1.2.1: <name>        # sub-sub-task (rare)
│   └── Task 1.2.2: <name>
└── Task 1.3: <name>              # sub-task
```

- Top-level tasks: `1`, `2`, `3`, ...
- Sub-tasks: `1.1`, `1.2`, `1.3`, ...
- Emergent tasks: `E1`, `E2`, ... (temporary — renumber into the hierarchy when assigned a position)

When a task is re-planned (`[~]`), it keeps its original number. The new task(s) that replace it get new numbers in the appropriate position.

## Task Table Format

The `## Tasks` table in the plan must use this format:

```markdown
## Tasks

| # | Status | Teammate | Scope | Model | Priority |
|---|--------|----------|-------|-------|----------|
| 1 | [x] | researcher | Analyze ONNX model structure | opus | high |
| 2.1 | [x] | implementer | Set up int8 calibration pipeline | sonnet | high |
| 2.2 | [~] | — | Run calibration on device | sonnet | high |
| 2.3 | [x] | implementer | Validate calibration accuracy | sonnet | medium |
| E1 | [>] | bug-fixer | Diagnose ONNX Runtime int8 bug | opus | blocker |
```

Status column is mandatory. A task with no status is invalid.

## Task Section Format

Each task's detailed section must show its status in the heading:

```markdown
### [x] Task 1: Analyze ONNX Model Structure
### [>] Task 2.1: Set Up Calibration Pipeline
### [~] Task 2.2: Run Calibration on Device
### [-] Task 2.4: Export to ONNX (abandoned — model uses ops not supported by ONNX export)
### [ ] Task 3: Generate Final Report
```

For `[~]` re-planned tasks, the section body must include a `**Re-planned as**:` line pointing to the new task(s).

For `[-]` abandoned tasks, the section body must include a `**Abandoned because**:` line with the reason.

## Editing the Plan

### Editing Procedure (must execute in this exact order)

#### Step 0 — Pre-Edit Dirty Check

**Before making any modification**, check whether the plan file has uncommitted changes:

```bash
git status --porcelain docs/plans/<batch>.md
```

If the output is **non-empty** — the file has uncommitted changes — **REJECT the edit immediately**. Do not read the file. Do not proceed. Report to the Lead:

```
PLAN EDIT REJECTED: Uncommitted changes detected in docs/plans/<batch>.md.

The file has been modified outside the plan-editing subagent. This is a
violation of the Plan Editing Boundary rule. Possible causes:
- The Lead or another agent edited the plan directly (forbidden)
- A previous plan-editing subagent crashed before committing
- A merge or rebase left the plan in a dirty state

The Lead must investigate: run `git diff docs/plans/<batch>.md` and
`git log --oneline docs/plans/<batch>.md` to identify what changed, when,
and by whom. After investigation, the Lead should run `git checkout` or
`git add && git commit` to resolve the dirty state before re-dispatching
the plan edit.
```

Only proceed to Step 1 if the dirty check passes (zero output from `git status`).

#### Step 1 — Read and Edit

Read the plan file, apply the requested change, enforce the frozen prefix constraint and all other rules in this document.

#### Step 2 — Commit

After editing, **immediately commit** the change:

```bash
git add docs/plans/<batch>.md
git commit -m "chore(plan): <brief description of change>"
```

The commit message must be specific: "mark task 2.1 as completed", "add emergent task E2: ONNX bug diagnosis", not "update plan".

Do NOT return to the Lead without committing. The edit is not complete until it is committed — this ensures atomicity.

#### Step 3 — Report

Report to the Lead:
1. What changed and why
2. The new freeze point (last `[x]` task)
3. Confirmation that all tasks before the freeze point have terminal markers
4. The commit SHA (from Step 2)

### Who Edits

Plan edits must be performed by a **standalone subagent** using these rules. The Lead never edits the plan directly — see the Plan Editing Boundary rule in the workflow SKILL.

### Amendment Recording

Every plan edit must be recorded in the `## Amendments` table:

```markdown
## Amendments
| Date | Task | Change | Reason |
|------|------|--------|--------|
| YYYY-MM-DD | 2.2 | Marked [~], re-planned as 2.5 | ONNX bug makes calibration impossible on current runtime |
| YYYY-MM-DD | E1 | Marked [x], merged | Bug root-caused and fixed |
```

### The "No Gaps" Rule

When marking a task as `[x]` completed, scan backward. If any earlier task is unmarked (`[ ]`) or in-progress (`[>]`), pause. That task must be resolved (completed, re-planned, or abandoned) before the freeze point advances. You cannot complete task 1.5 while 1.3 is still pending — this creates a gap that violates the frozen prefix constraint.

Resolve gaps by asking: was the task implicitly done as part of another? Mark it `[~]` with a reference. Was it found unnecessary? Mark it `[-]` with a reason. Is it actually still needed? Then it must be completed before later tasks can be marked done — reorder the plan accordingly.
