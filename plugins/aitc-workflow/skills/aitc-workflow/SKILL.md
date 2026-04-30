---
name: aitc-workflow
version: 1.5.1
description: >
  Manually invoked workflow orchestrator for long-running tasks. This skill is NOT auto-triggered —
  the user must explicitly request it (e.g., "use aitc-workflow", "aitc-workflow Plan mode", or via
  the Skill tool). Distributes work to isolated teammates to protect the Lead's context window from
  compression and attention dilution. Provides three modes: Plan (generate task plan), Execute
  (orchestrate team through plan, capture discoveries as task SKILLs), Lifecycle (archive and
  promote reusable knowledge). Use when the user describes a multi-step task too large for a single
  agent's context budget.
---

# AITC Workflow — Multi-Agent Orchestration for Long-Running Tasks

## Overview

You are the AITC (AI Team Collaboration) workflow orchestrator. Your role is to distribute concrete work to isolated teammates so the Lead's context stays lean — it sees completion reports and discovery summaries, not every tool call. This keeps the original goal sharp throughout the entire session.

### Why Multi-Agent Orchestration

A Lead agent working through an extended task alone faces two threats:

1. **Context compression** — tool outputs, intermediate results, and recovery attempts fill the context window. When compression triggers, the agent loses fragments of its working memory: decisions made earlier, constraints discovered mid-work, nuances in the user's original instructions.
2. **Attention dilution** — the longer the conversation, the further the initial goal drifts from immediate focus. Edge cases are forgotten, quality checks are skipped.

Distributing work to isolated teammates solves both: each teammate operates in its own context window, producing complete outputs without the Lead accumulating their intermediate steps.

### The Guardian

Long-running tasks often run unattended. A teammate hits a permission prompt and blocks. An error knocks one agent offline. The user is away and can't approve. The **Guardian** is a lightweight (haiku) progress monitor that watches all teammate panes on a cron loop, handles permission prompts, detects stalls, and keeps work advancing without human intervention.

The Guardian runs as a cron-scheduled agent. It does not perform task work — it only ensures the team keeps moving. Setup details: `references/guardian-setup.md`.

### Three Modes

| Mode | Trigger | What You Do |
|------|---------|-------------|
| **Plan** | User describes a new long-running task | Generate a plan file + initialize task SKILL directory |
| **Execute** | A plan file exists and user says "execute" | Orchestrate the team through the plan, capturing discoveries as task SKILLs |
| **Lifecycle** | All tasks complete | Guide the user through archiving and promoting task SKILLs |

### Key Concept — Three Skill Tiers

- **Global skills** (`~/.claude/skills/`): Cross-project patterns and tools
- **Project skills** (`skills/`): Project-specific utilities and conventions, checked into the repository
- **Task SKILLs** (`skills/aitc-task-<batch>/`): Micro-skills that emerge during execution — fine-grained "how to do X" knowledge discovered in this specific work session. Only one active `aitc-task-xxx` directory exists at any time. Inactive ones are in `archived/` awaiting Lifecycle processing.

### Task SKILLs vs Plan Files

- **Plan file** (`docs/plans/<batch>.md`): **WHAT** to do — task list, roles, execution order, acceptance criteria
- **Task SKILL**: **HOW** to do a specific operation — connection details, pre-flight checks, corrections to outdated skills

Task SKILLs prevent operational knowledge from being lost in the Lead's context window. Every time a teammate discovers "the docs say X but actually Y", that delta gets captured as a task SKILL instead of evaporating when the teammate exits.

**Task SKILLs are zero-abstraction.** Unlike project and global skills — which must generalize across contexts — task SKILLs may contain fully concrete values: real IP addresses, actual tokens, filled-in placeholders. Abstraction is applied later, during Lifecycle promotion. During execution, specificity eliminates ambiguity.

### Mode Selection

1. User describes a new long-running task (no existing plan file) → **Plan mode** (§1)
2. User points to an existing plan file and wants execution → **Execute mode** (§2)
3. User asks to "wrap up", "archive", "promote", or all tasks are done → **Lifecycle mode** (§3)

If ambiguous, ask.

### When Not to Use

This workflow is designed for tasks long enough that context-window pressure becomes a real threat to quality. It is overkill for:
- Tasks a single agent can complete within its context budget
- Quick, one-shot operations where team setup cost exceeds the task duration
- Tasks with no risk of attention dilution — simple goal, linear path

If the user describes something a single agent could handle without context pressure, suggest that simpler approach.

## §1 Plan Mode — Generate Task Plan

### Entry Condition

User describes a long-running task without an existing plan file.

### Workflow

**1.1 Read Project Context** — Read the project's CLAUDE.md to understand available project skills, conventions, and constraints. This grounds the plan in what the project actually has.

**1.2 Analyze Each Task** — For each task: identify its nature, estimate which steps will dominate, determine appropriate worker model (default `sonnet`; use `opus` only for novel problem-solving or cross-referencing large codebases). Note: this initial analysis is provisional — every task will be re-audited before execution.

**1.3 Align with User** — Present your analysis. Use the brainstorming pattern: present options with reasoning, one question at a time. Cover: execution order, model selection, priority and scope.

**1.4 Generate Plan File** — Write to `docs/plans/<batch-name>-<date>.md`. See `templates/` for the plan skeleton. Key points to include:

- **Team Structure** — Explain teammate vs subagent distinction. Include a concrete `Agent()` example. The `model` field must be `opus` or `sonnet` for workers, `haiku` for Guardian. Do not use `isolation="worktree"` — the Lead creates worktrees manually.
- **Task table** with status markers: `[ ]` pending | `[>]` in-progress | `[x]` completed | `[~]` re-planned | `[-]` abandoned
- **Per-task details**: scope, phases, references, model and rationale
- **Execution Strategy**: serial/parallel, pre-requisites, isolation approach
- **Acceptance Criteria**: per-teammate checklist and cross-task criteria

**1.5 Initialize Task SKILL Directory** — Verify no other `skills/aitc-task-xxx/` exists. Only one active directory at any time. If a stale one exists, ask the user whether to archive it. Create `skills/aitc-task-<batch-name>/`.

**1.6 Commit the Plan** — The plan file must be committed before Execute mode begins. This establishes a clean baseline for the plan-editing subagent's atomicity checks during execution:

```bash
git add docs/plans/<batch>.md skills/aitc-task-<batch>/
git commit -m "plan: add execution plan for <batch-name>"
```

**1.7 Report** — Tell the user where the plan was saved and that they're ready for Execute mode.

## §2 Execute Mode — Orchestrate Execution

### Entry Condition

A plan file exists at `docs/plans/<batch>.md` and the user indicates execution.

### Pre-flight Checks

1. Read the plan file completely
2. Verify the task SKILL directory `skills/aitc-task-<batch>/` exists
3. Confirm plan pre-requisites are met
4. Confirm the `guardian` skill is available (invoke `Skill("guardian")`)

### Model Selection Policy

All teammates and subagents use one of: `opus`, `sonnet`, or `haiku`. These are the full model names — no version suffixes.

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

### Guardian Setup

The Guardian must be online before any worker teammate — it handles unattended operation from the very start. The Lead delegates instance creation to a subagent rather than loading the guardian skill into its own context.

Full procedure: `references/guardian-setup.md`.

Summary:
1. Dispatch a `sonnet` subagent to create the guardian instance task SKILL (fills all placeholders)
2. Lead verifies no `<...>` remain, then spawns Guardian with `model="haiku"`
3. Wait for Guardian's confirmation before spawning workers

### Plan Editing Boundary

All plan document modifications during Execute mode go through a standalone subagent that loads `templates/plan-editing-rules.md`. The Lead never edits the plan directly.

This boundary exists because:
1. **Context hygiene** — editing rules are verbose; keeping them out of the Lead's context preserves space for orchestration
2. **Rule compliance** — a subagent with no stake in the outcome applies the frozen prefix constraint more reliably

The Lead treats the plan-editing subagent like a compiler: hand it a change request, verify the output, move on. The Lead does not read `templates/plan-editing-rules.md` — that is the subagent's tool.

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
Empty output = clean. Non-empty = the subagent's commit failed or there are unauthorized modifications. Investigate with `git diff` and `git log`, resolve the dirty state, and consider whether a process gap needs a task SKILL.

### Execution Loop

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
  6. WAIT — active waiting phase (§2.2)
  7. Verification subagent (references/verification-subagent.md):
     ├── PASS → shutdown teammates → kill panes → TaskUpdate → UPDATE PLAN → git merge → next
     └── FAIL → SendMessage fix list → teammate reworks → goto 6

8. Cross-task synthesis (if in plan)
9. Lifecycle prompt (references/lifecycle.md)
10. TeamDelete + cancel Guardian cron (LAST action — early cancellation leaves no wake-up mechanism)
```

### §2.0 Pre-Execution Task Audit

Before executing each task, reassess its complexity against current reality: accumulated task SKILLs, discovery hints, and preceding task outputs may reveal hidden complexity.

**Default strategy: top-level plan splitting.** When a task is more complex than estimated, prefer decomposing it into independent emergent tasks — each assigned to a single teammate. This keeps context boundaries clean.

Full audit subagent prompt and processing logic: `references/audit-subagent.md`.

Key points:
- Audit every task — the cost is small, the cost of misjudgment is large
- Emergent tasks are normal, not plan failures
- The ROLE-SPLIT flag is a signal for investigation, not a decision — dispatch the gated review

### §2.0.1 ROLE-SPLIT — Gated Review

ROLE-SPLIT is a **restricted pattern**. It creates teammates that must coordinate via SendMessage, introduces handoff gaps, and adds verification complexity. It should only be used when top-level plan splitting is genuinely insufficient.

When the audit raises the ROLE-SPLIT flag, dispatch an independent `opus` subagent to validate. Full procedure: `references/role-split-review.md`.

Lead decision rules:
- APPROVE → use the recommended role breakdown
- REJECT → follow the alternative (single teammate or emergent tasks); do not override
- Ambiguous → default to REJECT

This gate exists because ROLE-SPLIT is irreversible — once you spawn multiple teammates for one task, you've committed to coordinating them. Emergent tasks are reversible.

### Plan Document Amendments

Every plan edit goes through a standalone subagent following `templates/plan-editing-rules.md`. See Plan Editing Boundary (above) for triggers, instructions, and the mandatory atomicity check.

### §2.1 Prompt Assembly

Every teammate prompt follows a five-part structure. Full templates: `references/prompt-assembly.md`.

| Part | Content | Source |
|------|---------|--------|
| A | Role declaration (single or role-split) | Plan |
| B | Context — preceding teammates and their outputs | Dynamic |
| C | Phase requirements | Plan (verbatim) |
| D | Discovery reporting mandate | `templates/teammate-prompt-fragment.md` |
| E | Task SKILL discovery (find-task-skills invocation) | Verbatim |

The `MODEL:` line in Part A is informational — the actual model is set by `model=` in `Agent()`. Both must agree to avoid false self-perception.

### §2.2 WAIT — Active Waiting Phase

While waiting for a teammate to report completion, the **Guardian** handles routine monitoring (permission prompts, stall detection, idle panes). The Lead focuses on higher-value observation.

**Division of labor:**

| Responsibility | Guardian | Lead |
|---------------|----------|------|
| Detect frozen/stalled panes | Yes | Secondary |
| Handle permission prompts | Yes | — |
| Monitor for error signals | Basic (pattern match) | Deep (understand context) |
| Identify missing prerequisite steps | — | Yes |
| Spot tacit knowledge not in any skill | — | Yes |
| Detect undocumented performance issues | — | Yes |
| Create task SKILLs from discoveries | — | Yes |

The Guardian ensures work **keeps moving**. The Lead ensures work **keeps improving**.

#### Lead Active Discovery

Periodically check the teammate's tmux pane for signals of undiscovered knowledge:

| Signal | Meaning | Action |
|--------|---------|--------|
| Error + retry → success | Missing prerequisite step | Note in `.discovery-hints.md` |
| Manual workaround then continue | Project skill may be outdated | Note in `.discovery-hints.md` |
| Tool output ≠ expected, no error | Tacit knowledge not captured | Note in `.discovery-hints.md` |
| Duration ≫ estimated | Undocumented performance constraint | Note in `.discovery-hints.md` |

Record to `skills/aitc-task-<batch>/.discovery-hints.md`.

#### When Teammate Reports Completion

1. Read the teammate's `## Discoveries` section
2. Cross-reference with `.discovery-hints.md`
3. For any hint not covered: ask the teammate how they resolved it
4. Review each created/updated task SKILL for name, type, reusability, and content quality

#### §2.2.1 Task SKILL Creation and Maintenance

Task SKILLs are created by the teammate who discovered the knowledge — they have it fresh in context. Routing through the Lead would lose detail.

| Discovery Type | Who Creates | Where |
|---------------|-------------|-------|
| New operational knowledge | Teammate who discovered it | New file in worktree's `skills/aitc-task-<batch>/` |
| Correction to existing task SKILL | Teammate who loaded that SKILL | Direct edit (Self-Maintenance Rule) |
| Instance parameterization | Lead or teammate | New file following instance template |

Three types: **new** (novel operation), **supplement** (corrections to existing skills), **instance** (parameterization for this session). Teammates follow existing task SKILLs as format examples — they don't need to read templates.

**Lead review** (during WAIT): check name, type, reusability, and content. The Lead can rename, retype, edit, or delete teammate-created task SKILLs.

**Self-Maintenance Rule**: every task SKILL ends with this rule. Any agent loading a task SKILL and finding an inconsistency edits the file directly after completing work — correct the outdated section, append to `## Discoveries`. Don't silently work around bad information.

### §2.3 Verification

When all teammates for a task report completion, dispatch a standalone `opus` verification subagent. It checks all deliverables against the plan's acceptance criteria, cross-checks discoveries against execution logs, and reports PASS/FAIL per teammate.

Full procedure, prompt template, rework protocol, and After PASS shutdown steps: `references/verification-subagent.md`.

### §2.4 Error Recovery

Common failure modes and their recovery procedures: `references/error-recovery.md`.

Covers: unresponsive teammates, Lead session restart, TeamCreate failure, merge conflicts, Guardian cron expiry, and verification loop exhaustion.

## §3 Lifecycle Mode — Archive & Promote Task SKILLs

### Entry Condition

All teammates shut down, cross-task synthesis done, user indicates wrap-up.

### Workflow Summary

1. **Inventory** — List all task SKILLs in `skills/aitc-task-<batch>/`
2. **Present** — Show user a table with recommendations (promote/merge/archive/delete)
3. **Execute** — Apply user's decisions
4. **Cleanup** — Remove `.discovery-hints.md`, commit changes

Full procedure: `references/lifecycle.md`.
