---
name: aitc-workflow-execute
version: 1.0.0
description: >
  Manually invoked — NOT auto-triggered. Orchestrate a team through an existing plan file.
  User must explicitly request it (e.g., "use aitc-workflow-execute", "execute the plan",
  "run batch", "start"). Distributes work to isolated teammates, spawns a Guardian for
  unattended operation, captures operational discoveries as task SKILLs, and verifies
  deliverables. After all tasks complete, prompts the user to invoke aitc-workflow-lifecycle.
---

# AITC Workflow — Execute Mode

Orchestrate a team through an existing plan. This is the second of three workflow SKILLs:
Plan → **Execute** (this one) → Lifecycle.

## Why Multi-Agent Orchestration

A Lead agent working through an extended task alone faces two threats:

1. **Context compression** — tool outputs and intermediate results fill the context window. When compression triggers, the agent loses fragments of its working memory.
2. **Attention dilution** — the longer the conversation, the further the initial goal drifts from immediate focus.

Distributing work to isolated teammates solves both: each teammate operates in its own context window. The Lead's context stays lean — it only sees completion reports, not every tool call.

## The Guardian

Long-running tasks often run unattended. The **Guardian** is a lightweight (haiku) progress monitor that watches all teammate panes on a cron loop, handles permission prompts, detects stalls, and keeps work advancing without human intervention. Setup: `references/guardian-setup.md`.

## Pre-flight Checks

Before spawning any teammates:
1. Read the plan file completely — know every teammate's config, model, and settings
2. Verify the task SKILL directory `skills/aitc-task-<batch>/` exists
3. Confirm plan pre-requisites are met
4. Confirm the `guardian` skill is available (invoke `Skill("guardian")`)

## Model Selection Policy

All teammates and subagents use one of: `opus`, `sonnet`, or `haiku`. No version suffixes.

| Role | Model | Why |
|------|-------|-----|
| Audit subagent | `opus` | Complexity misjudgment causes cascading failures |
| ROLE-SPLIT review subagent | `opus` | Independent validation requires strongest judgment |
| Verification subagent | `opus` | Cross-referencing outputs, detecting subtle quality issues |
| Worker teammate (default) | `sonnet` | Balanced capability/cost for execution work |
| Worker teammate (complex/critical) | `opus` | When audit determines the task requires maximum capability |
| Plan-editing subagent | `sonnet` | Rule-following with known rules, procedural |
| Guardian instance subagent | `sonnet` | Template filling, procedural |
| Guardian | `haiku` | Monitoring is pattern-matching; cheapest model sufficient |

## Guardian Setup

The Guardian must be online before any worker teammate. The Lead delegates instance creation to a subagent. Full procedure: `references/guardian-setup.md`.

Summary:
1. Dispatch a `sonnet` subagent to create the guardian instance task SKILL (fills all placeholders)
2. Lead verifies no `<...>` remain, then spawns Guardian with `model="haiku"`
3. Wait for Guardian's confirmation before spawning workers

## Plan Editing Boundary

All plan document modifications go through a standalone subagent that loads `templates/plan-editing-rules.md`. The Lead never edits the plan directly.

This boundary exists because:
1. **Context hygiene** — editing rules are verbose; keeping them out of the Lead's context preserves space for orchestration
2. **Rule compliance** — a subagent with no stake in the outcome applies the frozen prefix constraint more reliably

The Lead treats the plan-editing subagent like a compiler: hand it a change request, verify the output. The Lead does not read `templates/plan-editing-rules.md`.

**When to trigger a plan edit:**

| Event | Instruction to Subagent |
|-------|------------------------|
| Teammate passes verification | Mark task `[x]` completed |
| Emergent task discovered | Insert new task with scope and classification |
| Task blocked/impossible | Mark `[~]` re-planned or `[-]` abandoned |

**Atomicity check** (after every plan edit):
```bash
git status --porcelain docs/plans/<batch>.md
```
Empty output = clean. Non-empty = the subagent's commit failed or there are unauthorized modifications. Investigate with `git diff` and `git log`, resolve the dirty state.

## Execution Loop

```
1. TeamCreate(team_name="<name>")
2. Guardian Setup → subagent creates instance → Lead verifies → spawn Guardian
3. Guardian must be online before any worker teammate

FOR EACH task IN plan.tasks (in plan order):
  4. PRE-EXECUTION AUDIT (references/audit-subagent.md):
     ├── Simple/moderate → single teammate, proceed to step 5
     ├── Emergent tasks found → amend plan, re-rank, each gets single teammate
     └── ROLE-SPLIT flag → gated review (references/role-split-review.md) → APPROVE or REJECT
  5. For each teammate:
     a. Assemble prompt (references/prompt-assembly.md)
     b. Create worktree: git worktree add --detach /tmp/worktrees/<team>-<task> main
     c. Agent(team_name, name, model=..., ...) spawn in background
     d. TaskCreate for tracking
     e. Post-spawn verify: check tmux status bar for worktree and model.
        Record pane ID for later shutdown. If wrong — tmux kill-pane -t %<id>, re-spawn.
  6. WAIT — active waiting phase (see below)
  7. Verification subagent (references/verification-subagent.md):
     ├── PASS → shutdown teammates → kill panes → TaskUpdate → UPDATE PLAN → git merge → next
     └── FAIL → SendMessage fix list → teammate reworks → goto 6

8. Cross-task synthesis (if in plan)
9. Prompt user to invoke aitc-workflow-lifecycle
10. TeamDelete + cancel Guardian cron (LAST action — early cancellation leaves no wake-up mechanism)
```

## Pre-Execution Task Audit (§2.0)

Before executing each task, reassess its complexity against current reality: accumulated task SKILLs, discovery hints, and preceding task outputs may reveal hidden complexity.

**Default strategy: top-level plan splitting.** When a task is more complex than estimated, prefer decomposing it into independent emergent tasks — each assigned to a single teammate.

Full audit subagent prompt and processing logic: `references/audit-subagent.md`.

Key points:
- Audit every task — the cost is small, the cost of misjudgment is large
- Emergent tasks are normal, not plan failures
- The ROLE-SPLIT flag is a signal for investigation, not a decision

## ROLE-SPLIT — Gated Review (§2.0.1)

ROLE-SPLIT is a **restricted pattern**. It creates teammates that must coordinate via SendMessage, introduces handoff gaps, and adds verification complexity. Only use when top-level plan splitting is genuinely insufficient.

When the audit raises the ROLE-SPLIT flag, dispatch an independent `opus` subagent to validate. Full procedure: `references/role-split-review.md`.

Lead decision rules:
- APPROVE → use the recommended role breakdown
- REJECT → follow the alternative; do not override
- Ambiguous → default to REJECT

This gate exists because ROLE-SPLIT is irreversible. Emergent tasks are reversible.

## Prompt Assembly (§2.1)

Every teammate prompt follows a six-part structure. Full templates: `references/prompt-assembly.md`.

| Part | Content | Source |
|------|---------|--------|
| A | Role declaration (single or role-split) | Plan |
| B | Context — preceding teammates and their outputs | Dynamic |
| C | Phase requirements | Plan (verbatim) |
| D | Discovery reporting mandate | `templates/teammate-prompt-fragment.md` |
| E | Task SKILL discovery (find-task-skills) | Verbatim |
| F | Real-time task SKILL creation (task-skills-creator) | Verbatim |

Part F is a **hard gate**: before reporting completion, the teammate must have invoked `task-skills-creator` for every discovery. The verification subagent cross-checks reported discoveries against the task SKILL directory. Missing files = FAIL.

## WAIT — Active Waiting Phase (§2.2)

While waiting for a teammate, the **Guardian** handles routine monitoring (permission prompts, stall detection, idle panes). The Lead focuses on higher-value observation.

**Division of labor:**

| Responsibility | Guardian | Lead |
|---------------|----------|------|
| Detect frozen/stalled panes | Yes | Secondary |
| Handle permission prompts | Yes | — |
| Monitor for error signals | Basic | Deep |
| Identify missing prerequisite steps | — | Yes |
| Spot tacit knowledge | — | Yes |
| Create task SKILLs from discoveries | — | Yes |

The Guardian ensures work **keeps moving**. The Lead ensures work **keeps improving**.

### Lead Active Discovery

Periodically check the teammate's tmux pane for signals of undiscovered knowledge. Record to `skills/aitc-task-<batch>/.discovery-hints.md`.

### When Teammate Reports Completion

1. Read the teammate's `## Discoveries` section
2. Cross-reference with `.discovery-hints.md`
3. For any hint not covered: ask the teammate
4. Review each created/updated task SKILL for name, type, reusability, and content quality

### Task SKILL Creation and Maintenance (§2.2.1)

Teammates invoke the `task-skills-creator` skill in real-time when they discover reusable knowledge. The skill spawns a forked subagent that handles file creation/editing — the teammate just describes what they found.

| Discovery Type | Mechanism | Where |
|---------------|-----------|-------|
| New operational knowledge | `Skill("task-skills-creator")` | New file in `skills/aitc-task-<batch>/` |
| Correction to existing task SKILL | Direct edit (Self-Maintenance Rule) | Edit the loaded SKILL file |
| Supplement to project skill | `Skill("task-skills-creator")` | New supplement file |
| Instance parameterization | Lead (pre-execution) | Instance template |

**Hard gate**: before reporting completion, the teammate verifies every discovery has a corresponding task SKILL file.

**Lead review** (during WAIT): check name, type, reusability, and content. The Lead can rename, retype, edit, or delete teammate-created task SKILLs.

**Self-Maintenance Rule**: every task SKILL ends with this rule. Any agent loading a task SKILL and finding an inconsistency edits the file directly — don't silently work around bad information.

## Verification (§2.3)

When all teammates for a task report completion, dispatch a standalone `opus` verification subagent. It checks all deliverables against the plan's acceptance criteria, cross-checks discoveries against execution logs, and reports PASS/FAIL per teammate.

Full procedure, prompt template, rework protocol, and After PASS shutdown steps: `references/verification-subagent.md`.

## Error Recovery (§2.4)

Common failure modes and their recovery procedures: `references/error-recovery.md`.

Covers: unresponsive teammates, Lead session restart, TeamCreate failure, merge conflicts, Guardian cron expiry, and verification loop exhaustion.

## After All Tasks Complete

When all plan tasks are done:
1. Complete cross-task synthesis (if specified in plan)
2. Shut down all remaining teammates
3. **Prompt the user**: "All tasks complete. Invoke `aitc-workflow-lifecycle` to archive task SKILLs and promote reusable knowledge."
4. Cancel Guardian cron and TeamDelete
