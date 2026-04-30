---
name: aitc-workflow-execute
version: 1.1.0
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
| task-skills-creator subagent (instance mode) | `sonnet` | Template filling, procedural |
| Guardian | `haiku` | Monitoring is pattern-matching; cheapest model sufficient |

## Guardian Setup

The guardian instance task SKILL was created during Plan mode. Read it at `skills/aitc-task-<batch>/guardian-<batch>.md`.

1. Verify the instance file has no `<...>` placeholders remaining (if any found, the Plan mode subagent failed — fill and commit before proceeding)
2. Spawn the Guardian using the instance's parameterization:
   ```
   Agent(
       team_name="<team-name>",
       name="guardian",
       subagent_type="general-purpose",
       model="haiku",
       mode="auto",
       run_in_background=True,
       prompt="""<filled guardian prompt from instance task SKILL>"""
   )
   ```
3. The Guardian self-configures: creates cron job, initializes log/notes files, reports online via SendMessage
4. Wait for Guardian's confirmation before spawning workers

## Plan Editing Boundary

**HARD RULE: The Lead never edits the plan directly. Never. Not even for trivial status updates.** Every plan modification — including marking a single `[ ]` → `[x]` — goes through a standalone subagent. Direct edits corrupt the plan's integrity and the atomicity check will catch them.

This boundary exists because:
1. **Context hygiene** — editing rules are verbose; keeping them out of the Lead's context preserves space for orchestration
2. **Rule compliance** — a subagent with no stake in the outcome applies the frozen prefix constraint more reliably
3. **Atomicity** — the subagent runs the pre-edit dirty check, enforces all rules, and commits atomically; the Lead cannot accidentally skip these steps

The Lead treats the plan-editing subagent like a compiler: hand it a change request, verify the output. The Lead does not read `templates/plan-editing-rules.md`.

### Concrete Subagent Template

Use this exact template for every plan edit. Fill the `<>` placeholders and spawn:

```
Agent(
    description="Update plan: <brief>",
    subagent_type="general-purpose",
    model="sonnet",
    prompt="""
    Edit docs/plans/<batch>.md following every rule in
    plugins/aitc-workflow/skills/aitc-workflow/templates/plan-editing-rules.md.

    CHANGE REQUEST: <what to change and why>

    Procedure (from plan-editing-rules.md):
    1. Pre-edit dirty check: git status --porcelain docs/plans/<batch>.md
       If non-empty → REJECT, report to Lead, do not proceed
    2. Read the plan file, apply the change, enforce frozen prefix + all rules
    3. Commit: git add docs/plans/<batch>.md && git commit -m "chore(plan): <specific>"
    4. Report: what changed, new freeze point, commit SHA
    """
)
```

### When to Trigger

| Event | CHANGE REQUEST value |
|-------|---------------------|
| Teammate passes verification | "Mark task <ID> as [x] completed" |
| Emergent task discovered | "Insert emergent task <E#>: <name> with scope <scope>, model <model>, priority <priority>" |
| Task blocked/impossible | "Mark task <ID> as [~] re-planned (replaced by <new tasks>) / [-] abandoned (reason: <why>)" |

### After Every Plan Edit

Verify the subagent actually committed:
```bash
git status --porcelain docs/plans/<batch>.md
```
Empty output = clean. Non-empty = the subagent's commit failed or the Lead edited directly (forbidden). Investigate with `git diff` and `git log`, resolve the dirty state, then re-dispatch the edit through a subagent.

If you catch yourself editing the plan directly — stop immediately. See error recovery: `references/error-recovery.md` §"Lead Edited Plan Directly".

## Execution Loop

```
1. TeamCreate(team_name="<name>")
2. Guardian Setup → read instance created by Plan mode → verify → spawn Guardian
3. Guardian must be online before any worker teammate

FOR EACH task IN plan.tasks (in plan order):
  4. PRE-EXECUTION AUDIT (references/audit-subagent.md):
     ├── Simple/moderate → single teammate, proceed to step 5
     ├── Emergent tasks found → plan-edit subagent (§Plan Editing Boundary) to insert them, re-rank, each gets single teammate
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
     ├── PASS → shutdown teammates → kill panes → TaskUpdate → plan-edit subagent (§Plan Editing Boundary) → git merge → next
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
