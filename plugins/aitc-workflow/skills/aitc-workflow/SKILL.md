---
name: aitc-workflow
version: 1.0.0
description: >
  Manually invoked workflow orchestrator for long-running multi-agent batch tasks. This skill is NOT auto-triggered — the user must explicitly request it by name (e.g., "use aitc-workflow", "aitc-workflow Plan mode", or via the Skill tool). Provides three modes: Plan (generate a task plan file), Execute (orchestrate a team through the plan, capturing operational discoveries as task-level SKILLs), and Lifecycle (archive completed task SKILLs and promote reusable knowledge into project or global skills).
---

# AITC Workflow — Multi-Agent Batch Orchestration

## Overview

You are the AITC (AI Team Collaboration) workflow orchestrator. You operate in one of three modes, selected based on the user's request:

| Mode | Trigger | What You Do |
|------|---------|-------------|
| **Plan** | User describes a new batch task | Generate a plan file + initialize task SKILL directory |
| **Execute** | A plan file exists and user says "execute" | Orchestrate the team through the plan, capturing discoveries as task SKILLs |
| **Lifecycle** | All tasks complete | Guide the user through archiving and promoting task SKILLs |

### Key Concept — Three Skill Tiers

- **Global skills** (`~/.claude/skills/`): Cross-project patterns and tools (this skill lives here)
- **Project skills** (`.claude/skills/` → `skills/`): Project-specific utilities and conventions
- **Task SKILLs** (`.claude/skills/aitc-task-<batch>/`): Micro-skills that emerge during execution — fine-grained "how to do X" knowledge discovered in this specific batch

### Task SKILLs vs Plan Files

- **Plan file** (`docs/plans/<batch>.md`): **WHAT** to do — task list, roles, execution order, acceptance criteria
- **Task SKILL**: **HOW** to do a specific operation — connection details for a dev board, pre-flight checks before a profiling run, corrections to an outdated project skill

Task SKILLs are the mechanism that prevents operational knowledge from being lost in the Lead's context window. Every time a teammate discovers "the docs say X but actually Y", that delta gets captured as a task SKILL instead of evaporating when the teammate exits.

### Mode Selection

When invoked, determine the mode:

1. If the user describes a new batch task (no existing plan file) → **Plan mode** (§1)
2. If the user points to an existing plan file and wants execution → **Execute mode** (§2)
3. If the user asks to "wrap up", "archive", "promote", or all tasks are done → **Lifecycle mode** (§3)

If ambiguous, ask the user which mode they want.

### When Not to Use

This skill is designed for batch orchestration of multiple tasks with inter-task coordination. It is overkill for:
- Single, self-contained tasks that one agent can complete independently
- Tasks that don't benefit from team coordination (no progress monitor, no discovery capture)
- Quick, one-shot operations where the setup cost of team creation exceeds the task duration

If the user describes something that could be done by dispatching one or two standalone subagents, suggest that simpler approach instead of invoking the full workflow.

## §1 Plan Mode — Generate Task Plan

### Entry Condition

User describes a batch task without an existing plan file.

### Workflow

#### 1.1 Read Project Context

Read the project's CLAUDE.md to understand:
- Available project skills (list `.claude/skills/` if not documented in CLAUDE.md)
- Project conventions (merge policy, directory structure, resource constraints)
- Any project-specific hardware, build systems, or external services

This ensures the generated plan is grounded in what the project actually has, not what a generic workflow might assume.

#### 1.2 Analyze Each Task

For each task in the user's list:
- Identify the task's nature (build? analysis? migration? profiling?)
- Estimate which steps will dominate execution time
- Determine appropriate worker model (use the standard model for established patterns; reserve the most capable model for tasks with genuinely novel challenges)
- Identify which existing project skills will be needed at each stage

The goal is to match model capability to task difficulty — over-provisioning wastes resources, under-provisioning produces unreliable results.

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
    isolation="worktree",
    model="<model>",
    mode="auto",
    run_in_background=True,
    prompt="""..."""
)
```

Without `team_name`, the agent is a standalone subagent — invisible to the team, unreachable via SendMessage, unable to coordinate via the shared task list. Every worker in the batch must be a teammate (with `team_name`), not a subagent.

Start the plan file with this skeleton, then fill in each section:

```markdown
# [Batch Name] — Execution Plan
**Date**: YYYY-MM-DD | **Team**: <team-name>

## Team Structure
[Teammate vs subagent table + Agent() example]

## Tasks
| # | Teammate | Scope | Model | Priority |
|---|----------|-------|-------|----------|

### Task 1: <name>
**Scope**: ...
**Phases**: ...
**References**: ...

## Execution Strategy
Serial or parallel, pre-requisites, isolation approach

## Acceptance Criteria
- [ ] Per-teammate checklist
- [ ] Cross-batch criteria

## Risk & Timeline
```

**Application Tasks** — For each teammate:
- Task description and scope
- Estimated effort profile (which steps dominate)
- Phase-by-phase requirements (tailored to the project's pipeline)
- References to existing code, reports, or analyses they should consult
- Model selection and rationale

**Execution Plan** — Serial vs parallel strategy, pre-requisites (e.g., models to pre-download), isolation strategy (shared vs independent resources per worktree).

**Acceptance Criteria** — Per-teammate checklist and cross-batch criteria.

**Risk and Timeline** — Risk mitigation table and time estimates per task.

#### 1.5 Initialize Task SKILL Directory

Create `.claude/skills/aitc-task-<batch-name>/` (empty initially, or containing only instance-class SKILLs if a Guardian or equivalent needs batch-specific parameters before execution starts).

#### 1.6 Report

Tell the user:
- Plan saved to: `docs/plans/<file>.md`
- Task SKILL directory: `.claude/skills/aitc-task-<batch>/`
- Ready for Execute mode when the user says "execute"

## §2 Execute Mode — Orchestrate Batch Execution

### Entry Condition

A plan file exists at `docs/plans/<batch>.md` and the user indicates execution ("execute the plan", "run batch2", "start").

### Pre-flight Checks

Before spawning any teammates:
1. Read the plan file completely — know every teammate's config, model, and isolation settings
2. Verify the task SKILL directory `.claude/skills/aitc-task-<batch>/` exists (create if missing)
3. Confirm pre-requisites from the plan are met (e.g., pre-downloaded models, pre-exported artifacts)
4. Verify the project has a `guardian` skill (or equivalent progress monitor) available

### Execution Loop

```
1. TeamCreate(team_name="<name>")
2. Generate instance-class task SKILLs needed before spawn
   (e.g., guardian-<batch>.md with batch-specific parameters)
3. Spawn Guardian (or equivalent progress monitor)

FOR EACH task IN plan.tasks (in the order specified by the plan):
  4. Read teammate config from plan (model, isolation, type)
  5. Assemble teammate prompt (see §2.1 Prompt Assembly)
  6. Agent(team_name, name, ...) spawn teammate in background
  7. TaskCreate for tracking
  8. WAIT — the active waiting phase (see §2.2)
  9. Verification subagent (see §2.3)
     ├── PASS → shutdown_request → wait exit → kill tmux pane
     │         → TaskUpdate(completed) → git merge --no-ff → next
     └── FAIL → SendMessage with fix list → teammate reworks → goto 8

10. Cross-task synthesis (if specified in plan)
11. Lifecycle prompt — guide user to archive + promote task SKILLs
12. TeamDelete + cancel Guardian cron (this must be the LAST action —
    canceling Guardian early means no one can wake a stuck Lead)
```

### §2.1 Prompt Assembly

Every teammate prompt is assembled from these parts, in order:

**Part A — Role declaration** (from plan):

```
You are the <task-name> worker in the <team-name> team.
Your task: Execute the full pipeline for <task-description>.
TARGET DIRECTORY: <path>
MODEL: <model>
MODE: auto
```

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

**Part E — Task SKILL references** (dynamically populated):

```
TASK SKILLS AVAILABLE:
- <name>: <one-line description> (use when <trigger condition>)
```

Populated from `.claude/skills/aitc-task-<batch>/` listing. Read each task SKILL's frontmatter to extract the description and usage guidance. Update this list as new task SKILLs are created during execution — new discoveries become immediately available to subsequent teammates.

### §2.2 WAIT — Active Waiting Phase

While waiting for a teammate to report completion, the Lead uses this time productively.

#### Lead Active Discovery

Periodically check the teammate's tmux pane for these signals:

| Signal | Meaning | Action |
|--------|---------|--------|
| Error + retry → success | Missing prerequisite step | Note in .discovery-hints.md |
| Manual workaround then continue | Project skill may have bug or outdated info | Note in .discovery-hints.md |
| Tool output ≠ expected, no error | Tacit knowledge not captured in any skill | Note in .discovery-hints.md |
| Duration ≫ estimated | Undocumented performance constraint | Note in .discovery-hints.md |

Record observations to `.claude/skills/aitc-task-<batch>/.discovery-hints.md`:

```markdown
# Discovery Hints
## <teammate-name> — <timestamp>
- **Observed**: <what you saw in tmux>
- **Signal type**: <error-retry | workaround | tacit | perf>
- **Question to ask**: <what to ask the teammate>
```

#### When Teammate Reports Completion

1. Read the teammate's `## Discoveries` section
2. Cross-reference with `.discovery-hints.md`
3. For any hint not covered in teammate's report:
   - Send a message asking: "I noticed you did X when Y happened. How did you resolve it?"
4. For each Discovery the teammate reported:
   - Judge: is this reusable knowledge or a one-time incident?
   - If reusable → create or update a task SKILL (see §2.2.1)
   - If one-time → note in the plan's execution log only

#### §2.2.1 Creating Task SKILLs

Three types, matching the three templates in `templates/`. Read the relevant template before creating.

**Type: new** — A completely new operation with no existing skill coverage.
Read `templates/task-skill-new.md` for the template.
Example: discovering the SSH credentials and hardware specs for a development board.

**Type: supplement** — Corrections or additions to an existing project skill.
Read `templates/task-skill-supplement.md` for the template.
Must declare `supplements: <project-skill-name>` in frontmatter.
Example: adding pre-flight disk/cpu checks to a profiling skill.

**Type: instance** — Task-specific parameterization of a project skill.
Read `templates/task-skill-instance.md` for the template.
Must declare `instance-of: <project-skill-name>` in frontmatter.
Example: guardian configuration for this specific batch.

Before creating any task SKILL, verify the knowledge is genuinely reusable. A one-time log entry ("the build took 5 minutes longer than expected") is not a skill. A checklist that prevents future teammates from hitting the same issue is.

Name task SKILLs descriptively. If a skill's scope expands during iteration, rename it to reflect the broader scope.

### §2.3 Verification

When a teammate reports all phases complete, dispatch a standalone verification subagent (no `team_name` — verification is one-shot and stateless, it doesn't need team membership or SendMessage):

```
Agent(
    description="Verify <teammate-name> deliverables",
    subagent_type="general-purpose",
    model="<most-capable-model>",
    mode="default",
    prompt="""
    Verify ALL deliverables for <teammate-name> in worktree <path>.

    PHASE-BY-PHASE CHECKLIST:
    [Checklist items from the plan's acceptance criteria, expanded
     with concrete file paths and expected outputs]

    DISCOVERY CHECK:
    - [ ] Teammate reported Discoveries for each phase
    - [ ] Cross-check: any error-recovery pattern in execution log
          that was not reported as a Discovery → FAIL

    Report: PASS/FAIL with detailed issue list for each failed item.
    If FAIL: provide specific, actionable fix instructions.
    """
)
```

Use the most capable model available for verification because it requires:
- Cross-referencing multiple output files for consistency (e.g., profiling data → gap analysis → consolidated report)
- Judging whether an empty output is a methodology error or a genuine result
- Identifying subtle quality issues like incomplete analysis or unsupported claims

Use a standalone subagent (no `team_name`) because verification is fire-and-forget — it checks, reports, and exits. It doesn't need the shared task list or inter-agent messaging.

#### Rework Protocol

1. Extract the specific fix list from the verification output
2. Send to teammate: "Verification found N issues. Fix each one: 1. ... 2. ..."
3. Teammate fixes and re-reports completion
4. Dispatch a fresh verification subagent (new instance, same checklist)
5. Repeat until PASS
6. If a teammate fails verification 3 times, the Lead intervenes directly — the issue is likely beyond what the teammate can self-correct

#### After PASS

1. Send shutdown_request to the teammate via SendMessage
2. Wait for teammate to confirm exit
3. Kill the teammate's tmux pane (keep total panes manageable — the Guardian reads panes via tmux capture-pane and too many causes output truncation)
4. Mark the task completed via TaskUpdate
5. Merge the worktree to the main branch:
   ```bash
   git merge --no-ff <worktree-branch>
   ```
6. Proceed to the next teammate

### §2.4 Error Recovery

Long-running batches encounter failures. Handle common cases without losing progress.

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
   - The `.discovery-hints.md` and task SKILLs on disk are intact

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

Recurring cron jobs auto-expire after 7 days (session lifetime bound). For batches longer than 7 days:
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
7. Record the outcome and reasoning in the plan's execution log — this is valuable data for improving future batch plans

## §3 Lifecycle Mode — Archive & Promote Task SKILLs

### Entry Condition

- All teammates have completed and been shut down
- Cross-task synthesis (if specified in plan) is done
- User indicates "wrap up", "archive", "promote", or batch completion is detected

### Workflow

#### 3.1 Inventory Task SKILLs

List all files in `.claude/skills/aitc-task-<batch>/` (excluding `.discovery-hints.md`).

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
- **new + project-specific** → promote to project skill (`.claude/skills/`)
- **supplement with still-valid corrections** → merge into the target project skill
- **supplement already absorbed** (e.g., target skill was already updated during the batch) → delete
- **instance** → archive as reference for future batches

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
1. Move to `.claude/skills/archived/aitc-task-<batch>/`
2. Keep as read-only reference — no further action needed

**Delete**:
1. Remove the file
2. Appropriate when: the knowledge was a false lead, or has been fully absorbed into another skill

#### 3.4 Cleanup

1. Remove `.discovery-hints.md` (transient Lead scratchpad)
2. If `.claude/skills/aitc-task-<batch>/` is empty, remove the directory
3. Commit all changes:
   ```bash
   git add docs/plans/<batch>.md
   git add .claude/skills/aitc-task-<batch>/   # or archived/
   git add .claude/skills/<any-updated-project-skills>/
   git commit -m "chore: archive batch <name> task SKILLs, promote discoveries"
   ```
4. Report summary: "Batch <name> complete. N task SKILLs processed: X merged, Y promoted, Z archived, W deleted."
