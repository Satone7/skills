---
name: task-skills-creator
version: 1.2.0
description: >
  Unified task SKILL creator for both discovery capture (teammates during execution)
  and instance parameterization (Lead during Plan mode). Offloads file creation/editing
  to a forked subagent. Not triggered by user directly — invoked internally via
  Skill("task-skills-creator") by teammates who discover reusable knowledge, or by
  the Lead during Plan mode to create instance task SKILLs (e.g., guardian instance).
---

# Task SKILLs Creator

## Purpose

You create and maintain task SKILL files. You are invoked in two contexts:

1. **Teammates during execution** — when they discover reusable operational knowledge
2. **Lead during Plan mode** — when creating instance task SKILLs (parameterizing project skills for this session)

In both cases, you spawn a forked subagent to handle file work so the caller's context stays clean.

## Discovery Mode (Teammate Invocation)

The teammate calls `Skill("task-skills-creator")` when they discover something worth capturing. They should invoke **immediately** — not wait until work is done.

### Step 1 — Collect Discovery Details

Ask the teammate:
1. **What happened** — expected vs actual
2. **What they did** — concrete steps, commands, workarounds
3. **Context** — which phase/task
4. **Relevance** — one-time incident or recurring?

**Quick exit**: if the teammate says "one-time incident, not reusable" — skip. Report "Not reusable — no task SKILL created." This is fine; not every observation needs a file.

### Step 2 — Dispatch Subagent

Spawn a forked subagent with `INTENT: discovery` (see Subagent Prompt below).

### Step 3 — Relay Result

Report the subagent's result. The teammate notes created/edited SKILLs in `## Discoveries`.

**If the subagent fails** (no file created, file has remaining placeholders): re-dispatch once with a more explicit prompt — include the exact file path and the exact content to write. If it fails again, report the failure to the Lead and continue working. Do not let a task SKILL creation failure block task completion.

## Instance Mode (Lead Invocation during Plan Mode)

The Lead calls `Skill("task-skills-creator")` during Plan mode to create an instance task SKILL. The Lead provides:
1. **Base skill name** — the project skill to parameterize (e.g., `guardian`)
2. **Parameterization values** — all concrete values for this session
3. **Batch name** — the active batch

### Step 1 — Collect Parameters

Ask the Lead:
1. Which base skill to instantiate?
2. What are the concrete parameter values?

If the Lead already provided these, don't re-ask.

### Step 2 — Dispatch Subagent

Spawn a forked subagent with `INTENT: instance` (see below).

### Step 3 — Verify

After the subagent exits, verify the instance file exists and contains no `<...>` placeholders. If placeholders remain, the subagent failed — re-run once with more explicit parameter values. If it fails again, fill the placeholders directly and report what happened.

## Subagent Prompt

Use `INTENT: discovery` or `INTENT: instance` and fill the appropriate section:

```
Agent(
    description="Create/edit task SKILL",
    subagent_type="general-purpose",
    model="sonnet",
    mode="default",
    prompt="""
    Create or edit a task SKILL file.

    INTENT: <discovery | instance>
    Batch: <batch-name>
    Worktree or target directory: <path>

    ── DISCOVERY MODE ──
    DISCOVERY:
    - What: <description>
    - Concrete steps: <what was done>
    - Context: <phase/task>

    STEP 1 — Check for existing task SKILLs:
    Run: bash plugins/aitc-workflow/skills/find-task-skills/list-task-skills.sh <batch-name>
    Review the output.

    STEP 2 — Decide: merge or create?
    - Fills a gap in an EXISTING task SKILL → edit that file (Self-Maintenance)
    - Supplements a known PROJECT skill → create supplement task SKILL
    - Entirely new → create new task SKILL
    - One-time log entry (not reusable) → skip, report "Not reusable"

    ── INSTANCE MODE ──
    INSTANCE:
    - Base skill: <skill-name> (e.g., guardian)
    - Parameters:
      - team_name: <value>
      - batch_name: <value>
      - instance_skill_path: <value>
      - log_file_path: <value>
      - notes_file_path: <value>
      - plan_file_path: <value>
      - task_count: <value>
      - cron_interval: <value>
      (Add or remove parameters as needed for the specific base skill)

    STEP 1 — Invoke the base skill: Skill("<base-skill-name>")
    Read its full content. Identify EVERY placeholder (text in <angle-brackets>).

    STEP 2 — Fill all placeholders with the concrete parameter values provided.
    No placeholder may remain.

    STEP 3 — Create the instance file using the instance template format:

    ---
    name: <skill>-<batch>
    description: Instance of <skill> configured for batch <batch>
    type: task
    task-type: instance
    instance-of: <skill-name>
    batch: <batch-name>
    created: <today>
    status: active
    ---

    # <Skill Name> — Instance for `<batch>`

    ## Parameterization
    - <param-name>: <concrete-value>
    (List ALL parameters with their concrete values)

    ## Differences from Base Skill
    None — follows base skill exactly.
    (Or note any deviations)

    ## Discoveries
    (Empty — populated during execution)

    ## Self-Maintenance Rule

    If you loaded this SKILL and something is wrong — a parameter value is incorrect,
    the instance configuration doesn't match reality — fix it in this file immediately.
    Do not silently work around. Edit:
    1. Correct the outdated value(s) in ## Parameterization or ## Differences
    2. Append a dated entry to ## Discoveries
    3. No need to consult the Lead

    ── COMMON ──

    File location: skills/aitc-task-<batch>/<filename>.md

    NEW task SKILL format:
    ```markdown
    ---
    name: <descriptive-kebab-name>
    description: <one-line>
    type: task
    task-type: new
    batch: <batch-name>
    created: <today>
    status: active
    ---

    # <Name>

    ## What
    <What was discovered — expected vs actual>

    ## How
    <Concrete steps, commands with real values. Zero abstraction is fine.>

    ## Discoveries
    (Empty)

    ## Self-Maintenance Rule
    If you loaded this SKILL and something is wrong — fix it in this file
    immediately after completing your work. Do not silently work around.
    ```

    SUPPLEMENT task SKILL format:
    ```markdown
    ---
    name: <project-skill>-<brief>
    description: Supplements <project-skill> with <what this adds>
    type: task
    task-type: supplement
    supplements: <project-skill-name>
    batch: <batch-name>
    created: <today>
    status: active
    ---

    # Supplement to `<project-skill>`

    ## What
    <What was wrong/missing in the original>

    ## How
    <Corrected or additional content>

    ## Discoveries
    (Empty)

    ## Self-Maintenance Rule
    (Same as above)
    ```

    Report: what file was created/edited, why merge vs create was chosen, file path.
    """
)
```
