---
name: aitc-workflow
version: 1.4.0
description: >
  Manually invoked workflow orchestrator for any long-running task. This skill is NOT auto-triggered — the user must explicitly request it by name (e.g., "use aitc-workflow", "aitc-workflow Plan mode", or via the Skill tool). By distributing work to isolated teammates, the Lead preserves its context window and avoids attention dilution over extended sessions. Provides three modes: Plan (generate a task plan file), Execute (orchestrate a team through the plan, capturing operational discoveries as task-level SKILLs), and Lifecycle (archive completed task SKILLs and promote reusable knowledge into project or global skills).
---

# AITC Workflow — Multi-Agent Orchestration for Long-Running Tasks

## Overview

You are the AITC (AI Team Collaboration) workflow orchestrator for long-running tasks.

### Why Multi-Agent Orchestration

A Lead agent working through an extended task alone faces two threats:

1. **Context compression** — tool outputs, intermediate results, and recovery attempts fill the context window. When compression triggers, the agent loses fragments of its working memory: decisions made earlier, constraints discovered mid-work, nuances in the user's original instructions.
2. **Attention dilution** — the longer the conversation, the further the initial goal drifts from immediate focus. Edge cases are forgotten, quality checks are skipped, and the output converges toward "done fast" rather than "done right."

Distributing concrete work to isolated teammates solves both: each teammate operates in its own context window, producing complete outputs without the Lead accumulating their intermediate steps. The Lead's context stays lean — it only sees completion reports and discovery summaries, not every tool call. This keeps the original goal sharp and quality high throughout the entire session.

### The Guardian

Long-running tasks often run unattended. A teammate hits a permission prompt and blocks. An error knocks one agent offline. The user is away and can't approve. The **Guardian** is a lightweight progress monitor that:

- Detects stalled teammates (frozen spinner, no output) and intervenes
- Handles permission prompts that would otherwise block progress
- Monitors tmux panes for error signals and recovery patterns
- Keeps the work advancing without human intervention

The Guardian runs as a cron-scheduled agent that periodically checks all teammate panes. It does not perform task work — it only ensures the team keeps moving.

### Three Modes

You operate in one of three modes, selected based on the user's request:

| Mode | Trigger | What You Do |
|------|---------|-------------|
| **Plan** | User describes a new long-running task | Generate a plan file + initialize task SKILL directory |
| **Execute** | A plan file exists and user says "execute" | Orchestrate the team through the plan, capturing discoveries as task SKILLs |
| **Lifecycle** | All tasks complete | Guide the user through archiving and promoting task SKILLs |

### Key Concept — Three Skill Tiers

- **Global skills** (`~/.claude/skills/`): Cross-project patterns and tools (this skill lives here)
- **Project skills** (`skills/`): Project-specific utilities and conventions, checked into the repository
- **Task SKILLs** (`skills/aitc-task-<batch>/`): Micro-skills that emerge during execution — fine-grained "how to do X" knowledge discovered in this specific work session. Only ONE active `aitc-task-xxx` directory exists in `skills/` at any time. Inactive ones are in `archived/` awaiting Lifecycle processing.

### Task SKILLs vs Plan Files

- **Plan file** (`docs/plans/<batch>.md`): **WHAT** to do — task list, roles, execution order, acceptance criteria
- **Task SKILL**: **HOW** to do a specific operation — connection details for a dev board, pre-flight checks before a profiling run, corrections to an outdated project skill

Task SKILLs are the mechanism that prevents operational knowledge from being lost in the Lead's context window. Every time a teammate discovers "the docs say X but actually Y", that delta gets captured as a task SKILL instead of evaporating when the teammate exits.

**Task SKILLs are zero-abstraction.** Unlike project and global skills — which must generalize across contexts — task SKILLs are permitted to be fully concrete and specific. A RISC-V board connection task SKILL may contain the real IP address, username, and password. A guardian instance task SKILL has every placeholder filled with the actual values for this work session. Abstraction is applied later, during Lifecycle promotion, when the task SKILL is converted into a reusable project or global skill by replacing concrete values with placeholders. During execution, specificity is a feature — it eliminates ambiguity for the teammate who needs to use that knowledge right now.

### Mode Selection

When invoked, determine the mode:

1. If the user describes a new long-running task (no existing plan file) → **Plan mode** (§1)
2. If the user points to an existing plan file and wants execution → **Execute mode** (§2)
3. If the user asks to "wrap up", "archive", "promote", or all tasks are done → **Lifecycle mode** (§3)

If ambiguous, ask the user which mode they want.

### When Not to Use

This skill is designed for tasks long enough that context-window pressure becomes a real threat to quality. It is overkill for:
- Tasks that a single agent can complete within its context budget without compression risk
- Quick, one-shot operations where the setup cost of team creation exceeds the task duration
- Tasks with no risk of attention dilution — the goal is simple and the path is linear

If the user describes something that could be done by a single agent without context pressure, suggest that simpler approach instead of invoking the full workflow.

## §1 Plan Mode — Generate Task Plan

### Entry Condition

User describes a long-running task without an existing plan file.

### Workflow

#### 1.1 Read Project Context

Read the project's CLAUDE.md to understand:
- Available project skills (list `skills/` if not documented in CLAUDE.md)
- Project conventions (merge policy, directory structure, resource constraints)
- Any project-specific hardware, build systems, or external services

This ensures the generated plan is grounded in what the project actually has, not what a generic workflow might assume.

#### 1.2 Analyze Each Task

For each task in the user's list:
- Identify the task's nature (build? analysis? migration? profiling?)
- Estimate which steps will dominate execution time
- Determine appropriate worker model: default to `sonnet` for established patterns; use `opus` only when the task requires novel problem-solving or cross-referencing large codebases
- Identify which existing project skills will be needed at each stage

The goal is to match model capability to task difficulty — over-provisioning wastes resources, under-provisioning produces unreliable results.

Note: this initial analysis is provisional. Every task will be re-audited before execution (§2.0) against accumulated task SKILLs and discovery hints. The plan's complexity estimates are a starting point, not a final verdict.

#### 1.3 Align with User via Brainstorming

Present your analysis and ask clarifying questions one at a time:
- Execution order: are there dependencies between tasks? does complexity order matter?
- Model selection for each worker (present your recommendation with reasoning, let user confirm or adjust)
- Priority and scope: should any tasks be deferred or split?

Use the brainstorming pattern: present options with reasoning, one question at a time.

#### 1.4 Generate Plan File

Write to `docs/plans/<batch-name>-<date>.md`. The plan file describes **what** to do (not detailed how-to — that belongs in task SKILLs). It must contain these sections:

**Team Structure** — Explain the teammate vs subagent distinction. Agents frequently confuse these two concepts, so include a concrete code example:

```
Agent(
    team_name="<team>",    # team_name is what makes this a teammate
    name="<name>",         # human-readable name, used for SendMessage
    subagent_type="general-purpose",
    model="<opus-or-sonnet>",
    mode="auto",
    run_in_background=True,
    prompt="""..."""
)
```

The `model` field must be `opus` or `sonnet` for worker teammates (see Model Selection Policy in §2). `haiku` is reserved for the Guardian. **The model must be set as an Agent() call parameter — prompt text alone does NOT control model selection.** Writing `MODEL: sonnet` in the prompt body has no effect on which model the system assigns.

**Do NOT use `isolation="worktree"` in the Agent() call.** It has proven unreliable — in some invocations it creates an isolated worktree, in others the teammate ends up in the main repository. Instead, the Lead creates the worktree manually before spawning (see Execution Loop step 5).

Without `team_name`, the agent is a standalone subagent — invisible to the team, unreachable via SendMessage, unable to coordinate via the shared task list. Every worker must be a teammate (with `team_name`), not a subagent.

Start the plan file with this skeleton, then fill in each section:

```markdown
# [Work Name] — Execution Plan
**Date**: YYYY-MM-DD | **Team**: <team-name> | **Freeze point**: (none yet)

## Team Structure
[Teammate vs subagent table + Agent() example]

## Tasks

| # | Status | Teammate | Scope | Model (opus\|sonnet) | Priority |
|---|--------|----------|-------|-------|----------|
| 1 | [ ] | ... | ... | ... | ... |

Status markers: `[ ]` pending | `[>]` in-progress | `[x]` completed | `[~]` re-planned | `[-]` abandoned

### [ ] Task 1: <name>
**Scope**: ...
**Phases**: ...
**References**: ...

## Execution Strategy
Serial or parallel, pre-requisites, isolation approach

## Acceptance Criteria
- [ ] Per-teammate checklist
- [ ] Cross-task criteria

## Amendments
(Empty initially — populated during execution)

## Risk & Timeline
```

**Application Tasks** — For each teammate:
- Task description and scope
- Estimated effort profile (which steps dominate)
- Phase-by-phase requirements (tailored to the project's pipeline)
- References to existing code, reports, or analyses they should consult
- Model selection and rationale

**Execution Plan** — Serial vs parallel strategy, pre-requisites (e.g., models to pre-download), isolation strategy (shared vs independent resources per worktree).

**Acceptance Criteria** — Per-teammate checklist and cross-task criteria.

**Risk and Timeline** — Risk mitigation table and time estimates per task.

#### 1.5 Initialize Task SKILL Directory

Before creating the new task SKILL directory, verify no other `skills/aitc-task-xxx/` exists. Only ONE active task SKILL directory is allowed at any time. If an existing one is found:

- It belongs to a prior session that was never completed or archived
- Check with the user: was that session abandoned? Should it be moved to `archived/`?
- Once resolved, create `skills/aitc-task-<batch-name>/` (empty initially, or containing only instance-class SKILLs if a Guardian or equivalent needs batch-specific parameters before execution starts)

#### 1.6 Report

Tell the user:
- Plan saved to: `docs/plans/<file>.md`
- Task SKILL directory: `skills/aitc-task-<batch>/`
- Ready for Execute mode when the user says "execute"

## §2 Execute Mode — Orchestrate Execution

### Entry Condition

A plan file exists at `docs/plans/<batch>.md` and the user indicates execution ("execute the plan", "run batch2", "start").

### Pre-flight Checks

Before spawning any teammates:
1. Read the plan file completely — know every teammate's config, model, and isolation settings
2. Verify the task SKILL directory `skills/aitc-task-<batch>/` exists (create if missing)
3. Confirm pre-requisites from the plan are met (e.g., pre-downloaded models, pre-exported artifacts)
4. Verify the `guardian` skill is available (invoke `Skill("guardian")` to confirm). The Guardian is essential for unattended operation: it handles permission prompts, detects stalled teammates, and ensures continuous progress when the user is away

### Model Selection Policy

All teammates and subagents use one of exactly three models: `opus`, `sonnet`, or `haiku`. These are the full model names — no version suffixes. The Lead must never invent or guess model names.

| Role | Model | Why |
|------|-------|-----|
| Audit subagent (§2.0) | `opus` | Complexity misjudgment causes cascading failures |
| ROLE-SPLIT review subagent (§2.0.1) | `opus` | Independent validation requires strongest judgment |
| Verification subagent (§2.3) | `opus` | Cross-referencing outputs, detecting subtleties, catching handoff gaps |
| Worker teammate (default) | `sonnet` | Balanced capability/cost for execution work |
| Worker teammate (complex/critical task) | `opus` | When audit determines the task requires maximum capability |
| Plan-editing subagent | `sonnet` | Rule-following with known rules, procedural |
| Guardian instance subagent | `sonnet` | Template filling, procedural |
| Guardian | `haiku` | Monitoring is pattern-matching; cheapest model sufficient |

The Lead selects the model for each spawn according to this table. There is no discretion to use a model outside `{opus, sonnet, haiku}` and no reason to specify version numbers.

### Guardian Setup

The Guardian is the first entity spawned after `TeamCreate` — before any worker teammate. Its full protocol is defined in the `guardian` skill (invoke it to read the complete specification). The Lead does NOT load the guardian skill into its own context. Instead:

#### Step 1 — Dispatch Guardian Instance Subagent

Dispatch a standalone subagent to create the guardian instance task SKILL:

```
Agent(
    description="Create guardian instance for <batch>",
    subagent_type="general-purpose",
    model="sonnet",
    mode="default",
    prompt="""
    Create a guardian instance task SKILL for batch "<batch-name>".

    1. Invoke the guardian skill: Skill("guardian")
    2. Read the plan at docs/plans/<batch>.md to extract:
       - team-name
       - task-count
       - batch-name
    3. Identify EVERY placeholder in the guardian skill's prompt template.
       Fill each one with the concrete value for this batch.
    4. Create the instance task SKILL at:
       skills/aitc-task-<batch>/guardian-<batch>.md
       Use template: plugins/aitc-workflow/skills/aitc-workflow/templates/task-skill-instance.md
       - instance-of: guardian
       - Parameterization: ALL filled placeholders (cron interval, team name,
         log path, notes path, plan path, task count, monitored panes list)
       - Differences from Base Skill: "None — follows base skill exactly"
         (or note any deviations)
    5. The parameterization MUST include these concrete values:
       - team_name: from plan
       - batch_name: from plan
       - instance_skill_path: skills/aitc-task-<batch>/guardian-<batch>.md
       - log_file_path: docs/plans/guardian-log-<batch>.md
       - notes_file_path: /tmp/guardian-<team-name>-notes.txt
       - plan_file_path: docs/plans/<batch>.md
       - task_count: from plan
       - cron_interval: "*/5 * * * *"  (default; adjust if the work requires different cadence)

    Report the created file path and a summary of filled parameters.
    """
)
```

#### Step 2 — Lead Verifies and Spawns

After the subagent creates the instance task SKILL:

1. Read the instance file to verify all placeholders are filled (no `<...>` remaining)
2. Spawn the Guardian using the guardian skill's spawn pattern, filling the prompt template from the instance's parameterization:
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
3. The Guardian will self-configure: create its cron job, initialize log and notes files, and report online via SendMessage

#### Step 3 — Confirm

Wait for the Guardian's confirmation message ("Guardian online. Cron loop active.") before proceeding to spawn worker teammates.

### Plan Editing Boundary (hard rule)

**All plan document modifications during Execute mode must go through a standalone subagent.** The subagent loads `templates/plan-editing-rules.md` and applies the editing rules. The Lead never edits the plan directly.

**The Lead does NOT read `templates/plan-editing-rules.md`.** That template is the subagent's tool, not the Lead's. Loading it into the Lead's context would consume context window space for rules the Lead never executes. The Lead only needs to know:

- **When** a plan edit is needed (task done, emergent task found, task re-planned or abandoned)
- **What** to tell the subagent (which task, what change, current freeze point)
- **How** to read the subagent's report (confirm freeze point advanced, no gaps remain)
- **Atomicity check**: after the subagent exits, verify the plan file has no uncommitted changes (see below)

The Lead treats the plan-editing subagent like a compiler: hand it a change request, verify the output, move on. The internal rules are the subagent's problem.

#### Post-Subagent Atomicity Check

After every plan-editing subagent completes, the Lead MUST verify the plan file is clean:

```bash
git status --porcelain docs/plans/<batch>.md
```

- **Empty output** → the subagent committed its changes correctly. Proceed.
- **Non-empty output** → something is wrong. Two possibilities:

  1. **The subagent's commit failed** (crash, hook rejection, etc.) — the changes are legitimate but uncommitted. Run `git diff docs/plans/<batch>.md` to verify the changes look correct, then `git add && git commit` them.

  2. **Unrelated modifications** — someone (Lead, another agent, merge artifact) modified the plan outside the subagent. This is a violation. Investigate:
     - `git diff docs/plans/<batch>.md` — what changed?
     - `git log --oneline docs/plans/<batch>.md` — when and by whom?
     - Determine whether the changes are benign (stale editor buffer) or malicious (a teammate editing the plan directly)
     - Resolve the dirty state: `git checkout docs/plans/<batch>.md` to discard unauthorized changes, or `git add && git commit` if they are legitimate but were left uncommitted

After investigation, the Lead must consider: **is this a one-time incident, or could it happen again?** If the root cause is a process gap (e.g., a teammate was never told not to edit the plan, or a hook rejected a commit and no one noticed), use **claudeception** to create a task-level SKILL that codifies the preventive measure. For example: "teammate-prompt-must-state-plan-is-read-only" or "pre-commit-hook-verification-check".

This boundary exists for two reasons:
1. **Context hygiene**: editing rules are verbose — keeping them out of the Lead's context preserves space for orchestration decisions
2. **Rule compliance**: a subagent with no stake in the outcome applies the frozen prefix constraint more reliably than the Lead applying rules to its own plan

### Execution Loop

```
1. TeamCreate(team_name="<name>")
2. Guardian Setup (§2 Guardian Setup) — subagent creates guardian instance
   task SKILL → Lead verifies → Lead spawns Guardian → confirm online
3. Guardian must be online before any worker teammate — it handles unattended
   operation: permission prompts, stall detection, continuous progress

FOR EACH task IN plan.tasks (in the order specified by the plan):
  4. PRE-EXECUTION AUDIT (§2.0) — dispatch an audit subagent to reassess
     the task against current reality (accumulated task SKILLs, discovery
     hints, preceding task outputs):
     ├── Simple/moderate → single teammate, proceed to step 5
     ├── Emergent tasks found → amend plan, re-rank, each gets single teammate
     └── ROLE-SPLIT flag set → §2.0.1 gated review → APPROVE or REJECT
  5. For each teammate the task requires (one for single-teammate or emergent;
     multiple only if ROLE-SPLIT was approved):
     a. Assemble role-specific prompt (§2.1)
     b. Create isolated worktree manually (do NOT rely on Agent isolation="worktree"):
        git worktree add --detach /tmp/worktrees/<team>-<task> main
        Include TARGET DIRECTORY: /tmp/worktrees/<team>-<task> in the prompt
     c. Agent(team_name, name, model=..., ...) spawn in background
     d. TaskCreate for tracking
     e. Post-spawn verify: check tmux status bar to confirm worktree (⎇ branch)
        and model. If wrong — kill pane, re-spawn.
  6. WAIT — the active waiting phase (§2.2)
  7. Verification subagent (§2.3) — verify ALL teammates for this task
     ├── PASS → shutdown each → kill panes → TaskUpdate → UPDATE PLAN
     │         (mark [x], advance freeze point, resolve gaps) → git merge → next task
     └── FAIL → SendMessage with fix list → teammate reworks → goto 6

8. Cross-task synthesis (if specified in plan)
9. Lifecycle prompt — guide user to archive + promote task SKILLs
10. TeamDelete + cancel Guardian cron (this must be the LAST action —
    canceling Guardian early means no one can wake a stuck Lead)
```

### §2.0 Pre-Execution Task Audit

The initial plan's complexity estimate is a guess made with incomplete information. Before executing each task, re-assess it against the current reality: accumulated task SKILLs, discovery hints from preceding tasks, and outputs that may reveal hidden complexity.

**Default strategy: top-level plan splitting.** When a task turns out to be more complex than estimated, the preferred response is to decompose it into independent emergent tasks in the plan, each assigned to a single teammate. This keeps context boundaries clean and task ownership unambiguous. ROLE-SPLIT (multiple teammates collaborating on one task) is a special-case fallback that requires independent justification — see §2.0.1.

#### When to Audit

Audit every task before spawning its teammate(s). The cost of the audit is small; the cost of assigning a complex task to a single overloaded teammate — or discovering mid-execution that the task is twice the expected scope — is large.

#### Audit Subagent

Dispatch a **standalone subagent** (no `team_name` — the audit is read-only analysis, not team work):

```
Agent(
    description="Audit task <task-name> before execution",
    subagent_type="general-purpose",
    model="opus",
    mode="default",
    prompt="""
    Audit task "<task-name>" before execution. Your job is to reassess
    complexity against current reality, not the initial plan.

    READ:
    1. The task description and phases in docs/plans/<batch>.md
    2. All task SKILLs in skills/aitc-task-<batch>/
    3. skills/aitc-task-<batch>/.discovery-hints.md
    4. Outputs from preceding completed tasks (merged to main branch)

    REPORT:

    A. COMPLEXITY REASSESSMENT
    - Original estimate: <from plan>
    - Current assessment: simple | moderate | complex | critical
    - Rationale: <what changed, what was underestimated>

    B. EMERGENT TASKS (primary mechanism for handling complexity)
    New tasks discovered from accumulated knowledge that are NOT in
    the current plan. For each:
    - Task name and description
    - Why it emerged (which discovery or output revealed it)
    - Estimated complexity and model recommendation
    - Whether it BLOCKS the current task or can run in parallel
    - Whether it should absorb the current task (if the discovery
      fundamentally changes what needs to be done)

    If the task is more complex than estimated, PREFER decomposing it
    into emergent tasks rather than recommending ROLE-SPLIT. Emergent
    tasks keep context boundaries clean — each teammate owns a complete,
    verifiable deliverable.

    C. ROLE-SPLIT FLAG (only if you see strong evidence)
    Set this flag ONLY if ALL of the following are true:
    1. The task CANNOT be meaningfully decomposed into sequential
       independent sub-tasks (the phases are tightly coupled)
    2. There is evidence of bidirectional dependency between roles
       (not just speculation — the discovery hints or task SKILLs
       must show that handoff gaps are likely without live iteration)
    3. The task's context volume plausibly exceeds a single context
       window (e.g., multiple large codebases, extensive logs)

    If the flag is set, briefly state which conditions were met and
    what evidence supports them. Do NOT recommend a specific role
    breakdown — that belongs to a separate review (§2.0.1).

    DEFAULT: single teammate for the task as currently scoped in the plan.
    """
)
```

Use `opus` for audits — misjudging complexity causes cascading failures downstream. (This is consistent with the Model Selection Policy above; repeated here because the audit subagent prompt template is copied verbatim into Agent() calls.)

#### Processing Audit Results

**Task is simple/moderate → single teammate:**
Proceed to §2.1 Prompt Assembly with the original task scope.

**Emergent tasks discovered:**
1. Classify each:
   - **Blocker** — must be done before the current task can proceed
   - **Parallel** — can run alongside the current task
   - **Absorbing** — fundamentally changes the current task's scope; the original task should be redefined
2. **Dispatch the plan-editing subagent** (see Plan Document Amendments) to insert emergent tasks into the plan. Provide: task name, scope, blocker/parallel/absorbing classification, and the current freeze point. The subagent handles numbering, status marking, and frozen prefix validation.
3. Re-rank priorities: an emergent blocker jumps ahead of non-blocked tasks
4. For absorbing tasks: the subagent updates the original task description to reflect the new scope
5. If the emergent task fundamentally changes the work's direction, pause and inform the user before proceeding
6. Create corresponding task SKILL(s) to capture what triggered the emergent task
7. The original task and emergent tasks each get a single teammate — proceed to §2.1 for each

**Audit raised the ROLE-SPLIT flag:**
Do NOT act on it immediately. Instead, proceed to §2.0.1 — dispatch an independent review subagent to validate whether ROLE-SPLIT is truly necessary. The audit's flag is a signal for further investigation, not a decision.

Emergent tasks are normal — they are not plan failures. The initial plan is a best-guess with incomplete information. Discovering new work is evidence that the audit is functioning correctly.

### §2.0.1 ROLE-SPLIT — Gated Review

ROLE-SPLIT is a **restricted pattern**. It creates teammates that must coordinate via SendMessage, introduces handoff gaps between roles, and adds verification complexity. It should only be used when top-level plan splitting is genuinely insufficient.

#### Gate: Independent Review Subagent

When the audit subagent sets the ROLE-SPLIT flag, dispatch a **second, independent subagent** to validate the necessity. This subagent must have no prior exposure to the task — it provides a cold-eyed assessment:

```
Agent(
    description="Review ROLE-SPLIT necessity for task <task-name>",
    subagent_type="general-purpose",
    model="opus",
    mode="default",
    prompt="""
    An audit of task "<task-name>" flagged it as a potential candidate
    for ROLE-SPLIT (multiple teammates collaborating on one task).

    Your job: independently validate whether ROLE-SPLIT is truly
    necessary, or whether top-level plan splitting is sufficient.

    READ:
    1. The audit subagent's report (especially the ROLE-SPLIT flag
       evidence)
    2. The task description and phases in docs/plans/<batch>.md
    3. All task SKILLs and discovery hints in skills/aitc-task-<batch>/
    4. Outputs from preceding completed tasks

    VALIDATE EACH CONDITION independently:

    1. NON-DECOMPOSABLE?
       Can the task be broken into sequential independent sub-tasks?
       - If YES → REJECT ROLE-SPLIT. Recommend emergent tasks instead.
       - If NO → explain why decomposition fails (what makes the phases
         inseparable?)

    2. BIDIRECTIONAL DEPENDENCY?
       Is there concrete evidence that roles would need live iteration?
       - Look for: discovery hints showing handoff failures, task SKILLs
         documenting integration issues, preceding task outputs with
         cross-cutting concerns
       - If evidence is only speculative ("might need iteration") →
         REJECT. Require demonstrated need, not hypothetical.

    3. CONTEXT VOLUME?
       Would a single context window plausibly overflow?
       - Estimate: number of codebases, log volume, reference docs
       - If under ~80% of a typical context budget → REJECT.
         Single-agent context is large; "this feels big" is not evidence.

    REPORT:
    - Verdict: APPROVE or REJECT ROLE-SPLIT
    - For each condition: MET / NOT MET with reasoning
    - If APPROVE: recommended role breakdown with specific scope per role,
      convergence criteria (when does iteration stop?), and model per role
    - If REJECT: concrete alternative — either "single teammate suffices"
      or "decompose into these N emergent plan tasks"

    DEFAULT VERDICT: REJECT. Override only when all three conditions
    are independently confirmed with concrete evidence.
    """
)
```

#### Lead Decision

- **Review APPROVES** → use the recommended role breakdown. Spawn role-teammates in dependency order. Document the decision and evidence in the plan's Amendments section.
- **Review REJECTS** → follow the review's alternative recommendation (single teammate or emergent tasks). Do not override a rejection — if two independent subagents disagree, neither has a strong enough case.
- **Review is ambiguous** (approves with weak evidence) → default to REJECT. Weak evidence is weak ROLE-SPLIT.

This gate exists because ROLE-SPLIT is irreversible — once you spawn multiple teammates for one task, you've committed to coordinating them. Emergent tasks are reversible — you can always split further later.

### Plan Document Amendments

Every plan edit — task completion, emergent task insertion, re-plan, abandonment — must be performed by a standalone subagent following `templates/plan-editing-rules.md`. The Lead never edits the plan directly (see Plan Editing Boundary, above).

##### When to Trigger a Plan Edit

| Event | Instruction to Subagent |
|-------|------------------------|
| Teammate passes verification | "Mark task `<N>` as `[x]` completed" |
| Emergent task discovered (§2.0 audit) | "Add emergent task `<name>` with scope `<...>`, blocker/parallel/absorbing `<type>`" |
| Task cannot proceed (blocked, impossible) | "Mark task `<N>` as `[~]` re-planned, reference `<new-task>`" or "Mark task `<N>` as `[-]` abandoned, reason: `<...>`" |
| Task reordered | "Mark task `<N>` as `[~]`, insert re-planned version at position after `<last-frozen>`" |

##### What to Tell the Subagent

Give it: (1) the change needed, (2) the current freeze point, (3) the path to `docs/plans/<batch>.md` and `templates/plan-editing-rules.md`. The subagent loads the rules, performs the dirty check, applies the change, commits, and reports back.

##### What to Read from the Subagent's Report

1. What changed (confirm it matches the request)
2. New freeze point (must have advanced if a task was completed)
3. Gap report — if any unmarked tasks remain before the freeze point, those must be resolved before proceeding
4. Commit SHA — confirms the change was committed atomically

##### Lead Atomicity Check (mandatory after every plan edit)

After the subagent exits, run:

```bash
git status --porcelain docs/plans/<batch>.md
```

Empty output = subagent committed correctly. Non-empty = a problem — see Plan Editing Boundary for the full investigation procedure.

##### Status Update Protocol (After PASS)

1. Dispatch the plan-editing subagent with: "Mark task `<N>` as `[x]` completed. Current freeze point: `<last-frozen>`."
2. The subagent scans for gaps — any `[ ]` or `[>]` before the new freeze point
3. If gaps exist: resolve each (mark `[~]`, `[-]`, or reorder) before the freeze point advances
4. Run the atomicity check — confirm no uncommitted changes remain
5. Only after both the plan is updated and the atomicity check passes does the Lead proceed to the next task's audit

The plan is always the authoritative record of what happened. No completed work exists outside the plan's frozen prefix.

### §2.1 Prompt Assembly

Every teammate prompt is assembled from the following parts, in order. For the rare case where ROLE-SPLIT was approved via the §2.0.1 gate, use the role-specific variants in Part A and Part C.

**Part A — Role declaration** (from plan; for ROLE-SPLIT, from the gated review's role breakdown):

The `MODEL:` line in the prompt body is informational only — it tells the teammate what model it is running on, but does NOT control the actual model. The model is set by the `model=` parameter in the `Agent()` call. Both must agree: if `Agent(model="sonnet")` writes `MODEL: opus`, the teammate works with a false self-perception that can distort its judgment.

Single-teammate:
```
You are the <task-name> worker in the <team-name> team.
Your task: Execute the full pipeline for <task-description>.
TARGET DIRECTORY: <path>
MODEL: <model>
MODE: auto
```

Role-split (one teammate per role):
```
You are the <role-name> for task <task-name> in the <team-name> team.
Your role: <role-description — what this role is responsible for>.
Your scope is LIMITED TO: <specific phases this role handles>.
You depend on: <preceding role outputs, if any>.
Other roles on this task: <list other roles and what they handle>.
TARGET DIRECTORY: <path>
MODEL: <model>
MODE: auto
```

The role-split declaration gives each teammate clear boundaries — they know exactly what they own and what they don't, and who to wait for before starting.

**Part B — Context** (from plan, dynamically populated based on execution order):

```
You are the <Nth> active teammate. Previous teammates (<list>) have
completed and their code is merged to the main branch. Reference their
output in <report-paths>.
```

This gives each teammate awareness of what came before, enabling cross-referencing without the Lead having to manually relay findings.

**Part C — Phase requirements** (from plan, per-task):

Each phase with specific instructions and skill references. Extract verbatim from the plan's task description section.

**Part D — Discovery reporting mandate** (include verbatim in every teammate prompt):

Read `templates/teammate-prompt-fragment.md` and copy its full content as Part D of the teammate prompt. The template contains the mandatory discovery reporting format.

The rationale: discoveries are the raw material for task SKILLs. If teammates silently fix issues, that knowledge is lost forever when the teammate exits. The verification step (§2.3) cross-checks reported discoveries against execution logs to catch omissions.

**Part E — Task SKILL discovery** (include verbatim in every teammate prompt):

```
TASK SKILL DISCOVERY:
Invoke the find-task-skills skill at the start of your work. It will guide
you to discover and load relevant task SKILLs from skills/aitc-task-<batch>/.

Do NOT rely on the Lead to list available task SKILLs — you are responsible
for finding the ones relevant to your task. The task SKILL directory is:
skills/aitc-task-<batch>/
```

The `find-task-skills` skill handles listing, relevance judgment, loading, and self-maintenance. The Lead no longer manually populates this section — the teammate discovers task SKILLs independently.

### §2.2 WAIT — Active Waiting Phase

While waiting for a teammate to report completion, the Lead uses this time productively. The **Guardian** handles the routine monitoring — permission prompts, stall detection, idle panes — so the Lead can focus on higher-value observation.

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

The Guardian ensures the work **keeps moving**. The Lead ensures the work **keeps improving**.

#### Lead Active Discovery

Periodically check the teammate's tmux pane for these signals:

| Signal | Meaning | Action |
|--------|---------|--------|
| Error + retry → success | Missing prerequisite step | Note in skills/aitc-task-<batch>/.discovery-hints.md |
| Manual workaround then continue | Project skill may have bug or outdated info | Note in skills/aitc-task-<batch>/.discovery-hints.md |
| Tool output ≠ expected, no error | Tacit knowledge not captured in any skill | Note in skills/aitc-task-<batch>/.discovery-hints.md |
| Duration ≫ estimated | Undocumented performance constraint | Note in skills/aitc-task-<batch>/.discovery-hints.md |

Record observations to `skills/aitc-task-<batch>/.discovery-hints.md`:

```markdown
# Discovery Hints
## <teammate-name> — <timestamp>
- **Observed**: <what you saw in tmux>
- **Signal type**: <error-retry | workaround | tacit | perf>
- **Question to ask**: <what to ask the teammate>
```

#### When Teammate Reports Completion

1. Read the teammate's `## Discoveries` section
2. Cross-reference with `skills/aitc-task-<batch>/.discovery-hints.md`
3. For any hint not covered in teammate's report:
   - Send a message asking: "I noticed you did X when Y happened. How did you resolve it?"
4. For each Discovery the teammate reported:
   - The teammate should have already created or updated task SKILLs for reusable discoveries (see §2.2.1). If they didn't, ask them to.
   - Lead reviews each created/updated task SKILL: name appropriate? type correct? genuinely reusable?
   - If the Lead disagrees with a creation decision: modify or delete the task SKILL, note in execution log

#### §2.2.1 Task SKILL Creation and Maintenance

**Task SKILLs are created by the teammate who discovered the knowledge, not by the Lead.** The teammate has the knowledge fresh in context — routing through the Lead would lose detail and create a bottleneck.

##### Who Creates What

| Discovery Type | Who Creates | Where |
|---------------|-------------|-------|
| New operational knowledge | Teammate who discovered it | New file in worktree's `skills/aitc-task-<batch>/` |
| Correction to existing task SKILL | Teammate who loaded that SKILL | Direct edit to the SKILL file (Self-Maintenance Rule) |
| Instance parameterization | Lead (pre-execution) or teammate (mid-execution) | New file following instance template |

##### How Teammates Create Task SKILLs

Teammates create task SKILLs directly in their worktree. The prompt's Part E lists existing task SKILLs — these serve as format examples. Teammates do not need to read the templates; they follow the structure of existing SKILLs.

Three types:

**Type: new** — A completely new operation with no existing skill coverage.
Example: discovering the SSH credentials and hardware specs for a development board.
Structure: `## Purpose`, `## Prerequisites`, `## Procedure`, `## Discoveries`, `## Self-Maintenance Rule`.

**Type: supplement** — Corrections or additions to an existing project skill.
Must declare `supplements: <project-skill-name>` in frontmatter.
Example: adding pre-flight disk/cpu checks to a profiling skill.
Structure: `## Supplemented Skill`, `## Issues Found`, `## Corrections / Additions`, `## Discoveries`, `## Self-Maintenance Rule`.

**Type: instance** — Task-specific parameterization of a project skill.
Must declare `instance-of: <project-skill-name>` in frontmatter.
Example: guardian configuration for this specific work session.
Structure: `## Parameterization` (all values concrete), `## Differences from Base Skill`, `## Discoveries`, `## Self-Maintenance Rule`.

##### Lead Review (during WAIT)

When a teammate reports completion, the Lead reviews the task SKILLs they created:

1. **Name check**: descriptive? reflects actual scope?
2. **Type check**: new / supplement / instance correct?
3. **Reusability check**: is this genuinely reusable, or a one-time log entry?
4. **Content check**: concrete values filled? procedure actionable?

The Lead can rename, retype, edit, or (rarely) delete a teammate-created task SKILL. The Lead's review is the quality gate.

##### Self-Maintenance (by any loading agent)

Every task SKILL includes a `## Self-Maintenance Rule` section. Any agent that loads a task SKILL and finds an inconsistency — wrong value, missing step, outdated info — must edit the SKILL file directly after completing their work. Correct the outdated section, append to `## Discoveries`. Do not silently work around. Do not wait for the Lead.

This keeps task SKILLs accurate without Lead involvement. Maintenance is not creation — the SKILL already exists, it just needs a correction.

### §2.3 Verification

When all teammates for a task report completion, dispatch a standalone verification subagent. The verification covers all teammates assigned to this task — for role-split tasks, verify the integrated output of all roles together, not each role in isolation.

```
Agent(
    description="Verify task <task-name> deliverables",
    subagent_type="general-purpose",
    model="opus",
    mode="default",
    prompt="""
    Verify ALL deliverables for task <task-name> in worktree <path>.

    TEAMMATES ON THIS TASK:
    - <name> (<role>): <scope>
    - <name> (<role>): <scope>

    PHASE-BY-PHASE CHECKLIST (across all teammates):
    [Checklist items from the plan's acceptance criteria, expanded
     with concrete file paths and expected outputs. For role-split
     tasks, verify integration points between roles — does the
     implementer's output match the researcher's spec?]

    DISCOVERY CHECK:
    - [ ] Each teammate reported Discoveries for their phases
    - [ ] Cross-check: any error-recovery pattern in execution logs
          that was not reported as a Discovery → FAIL
    - [ ] For role-split tasks: any handoff gap between roles
          (researcher described X but implementer built Y) → FAIL

    Report: PASS/FAIL with detailed issue list per teammate.
    If FAIL: specify which teammate(s) need to fix what.
    """
)
```

Use `opus` for verification because it requires:
- Cross-referencing multiple output files for consistency (e.g., profiling data → gap analysis → consolidated report)
- Judging whether an empty output is a methodology error or a genuine result
- Identifying subtle quality issues like incomplete analysis or unsupported claims
- For role-split tasks: detecting integration gaps between independently-working teammates

Use a standalone subagent (no `team_name`) because verification is fire-and-forget — it checks, reports, and exits. It doesn't need the shared task list or inter-agent messaging.

#### Rework Protocol

1. Extract the specific fix list from the verification output, routed per teammate
2. Send to each teammate that had failures: "Verification found N issues in your scope. Fix each one: 1. ... 2. ..."
3. Teammates fix and re-report completion
4. When all teammates for the task have re-reported, dispatch a fresh verification subagent (new instance, same checklist)
5. Repeat until PASS for all teammates
6. If a teammate fails verification 3 times, the Lead intervenes directly — the issue is likely beyond what the teammate can self-correct

#### After PASS

1. Send shutdown_request to each teammate via SendMessage
2. Wait for all teammates to confirm exit
3. Kill each teammate's tmux pane — completed teammates MUST be fully shut down before moving on. Do not leave inactive teammates lingering: they consume tmux panes, clutter the Guardian's monitoring surface, and create ambiguity about who is still working. The only active panes at any moment should belong to the current task's teammates plus the Guardian.
4. Mark all teammates' tasks completed via TaskUpdate
5. **Update the plan** — dispatch the plan-editing subagent (§2.0, Plan Document Amendments) to mark the task `[x]`, advance the freeze point, and resolve any gaps. Do NOT proceed until the plan is updated.
6. Merge all worktrees for this task to the main branch:
   ```bash
   git merge --no-ff <worktree-branch-1> <worktree-branch-2> ...
   ```
7. Proceed to the next task (audit → spawn → ...)

### §2.4 Error Recovery

Long-running tasks encounter failures. Handle common cases without losing progress.

#### Teammate Becomes Unresponsive

If a teammate's tmux pane shows no activity for an extended period (significantly beyond the task's estimated duration):

1. Check if the spinner is still animating (active work) vs frozen (stuck)
2. If frozen: send Ctrl-C via tmux, then diagnose via SendMessage
3. If the teammate doesn't respond to SendMessage within a reasonable time:
   - The agent process may have died; check `ps aux | grep agent`
   - Re-spawn the teammate with the same prompt; it will pick up from where it left off (worktree state is preserved)
   - Log the incident in the plan's execution log

#### Lead Session Restart

If the Lead's session terminates and later restarts (power loss, crash, network drop):

1. The worktrees persist on disk — no work is lost
2. The Guardian cron is session-only (durable=false) and dies with the session
3. Recovery steps:
   - Check `git worktree list` to identify active worktrees
   - Read the Guardian log at `docs/plans/guardian-log-<batch>.md` for last-known state
   - Re-create the team: `TeamCreate(team_name="<name>")`
   - Re-spawn Guardian with the same parameters
   - Resume from the last completed teammate (check which worktrees have been merged)
   - The `skills/aitc-task-<batch>/.discovery-hints.md` and task SKILLs on disk are intact

#### TeamCreate Failure

If TeamCreate returns an error (team name conflict from a prior run):

1. Check if the team still has active members: read `~/.claude/teams/<name>/config.json`
2. If all members are dead/defunct, delete the team: `TeamDelete`
3. Re-create with the same name
4. If members are still active, use a suffixed name: `<name>-v2`

#### Merge Conflict During Worktree Merge

1. Conflicts should be rare (each teammate writes to isolated paths)
2. If a conflict occurs: resolve manually — teammate outputs (reports, patches) take priority
3. If in doubt, keep both versions and note in the plan log

#### Guardian Cron Expiry

Recurring cron jobs auto-expire after 7 days (session lifetime bound). For tasks longer than 7 days:
- Set `durable: true` when creating the Guardian cron (if supported)
- Or re-create the Guardian cron at day 6

#### Verification Loop Exhaustion

If a teammate fails verification 3 times (the rework limit defined in §2.3):

1. Do not shut down the teammate — instead, read their worktree to understand what state it's in
2. Classify each failure as critical (missing or incorrect deliverable) or cosmetic (formatting, naming)
3. Fix critical issues directly in the worktree (the Lead has filesystem access)
4. Document any cosmetic issues that will be accepted as-is in the plan's execution log
5. Run a final verification subagent on the repaired worktree
6. If it still fails, choose one of these paths:
   - **Accept with known issues**: if failures are minor and don't affect conclusions, document them and proceed
   - **Re-assign**: abandon the task, refine the teammate prompt based on what was learned, and spawn a new teammate to redo it
   - **Escalate**: present the situation to the user for a decision
7. Record the outcome and reasoning in the plan's execution log — this is valuable data for improving future plans

## §3 Lifecycle Mode — Archive & Promote Task SKILLs

### Entry Condition

- All teammates have completed and been shut down
- Cross-task synthesis (if specified in plan) is done
- User indicates "wrap up", "archive", "promote", or all tasks have been marked complete

### Workflow

#### 3.1 Inventory Task SKILLs

List all files in `skills/aitc-task-<batch>/` (excluding `.discovery-hints.md`).

For each, read the frontmatter to determine type:
- `task-type: new` — entirely new operational knowledge
- `task-type: supplement` with `supplements: <skill>` — corrections or additions to existing skill
- `task-type: instance` with `instance-of: <skill>` — parameterized instance

#### 3.2 Present Summary to User

Present a table of all task SKILLs with preliminary recommendations:

| Task SKILL | Type | Supplements / Instance-Of | Content Summary | Recommendation |
|------------|------|---------------------------|-----------------|----------------|
| ... | new | — | ... | Promote to project/global skill |
| ... | supplement | some-skill | ... | Merge into some-skill |
| ... | instance | some-skill | ... | Archive as reference |

Recommendation logic:
- **new + cross-project applicable** → promote to global skill (`~/.claude/skills/`)
- **new + project-specific** → promote to project skill (`skills/`)
- **supplement with still-valid corrections** → merge into the target project skill
- **supplement already absorbed** (e.g., target skill was already updated during execution) → delete
- **instance** → archive as reference for future work sessions

Ask the user to confirm or override each recommendation, one at a time.

#### 3.3 Execute User's Decisions

**Merge** (supplement type):
1. Read both the task SKILL and the original project skill
2. Generate the merged version — fold the task SKILL's corrections into the original
3. Show the user the diff before applying
4. On confirmation, update the project skill
5. Delete the task SKILL (its content now lives in the project skill)

**Promote** (new type):
1. Determine target tier (project vs global) based on domain specificity
2. Copy to the target location with frontmatter cleanup:
   - Remove `task-type`, `batch`, `supplements`, `instance-of` fields
   - Set `type: project` or `type: global`
   - Keep `created` date, add `promoted: <YYYY-MM-DD>`
3. Use the final skill name (respecting any renames that happened during execution)

**Archive** (instance type, or user preference):
1. Move to `archived/aitc-task-<batch>/`
2. Keep as read-only reference — no further action needed

**Delete**:
1. Remove the file
2. Appropriate when: the knowledge was a false lead, or has been fully absorbed into another skill

#### 3.4 Cleanup

1. Remove `.discovery-hints.md` (transient Lead scratchpad)
2. If `skills/aitc-task-<batch>/` is empty, remove the directory
3. Commit all changes:
   ```bash
   git add docs/plans/<batch>.md
   git add skills/aitc-task-<batch>/   # or archived/
   git add skills/<any-updated-project-skills>/
   git commit -m "chore: archive <name> task SKILLs, promote discoveries"
   ```
4. Report summary: "Work <name> complete. N task SKILLs processed: X merged, Y promoted, Z archived, W deleted."
