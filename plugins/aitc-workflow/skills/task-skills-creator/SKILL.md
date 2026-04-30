---
name: task-skills-creator
version: 1.0.0
description: >
  Lightweight task SKILL creator invoked by teammates in real-time when they discover
  reusable operational knowledge. Offloads file creation/editing to a forked subagent
  so the teammate's context stays lean. Not triggered by user directly — teammates
  invoke it during AITC workflow execution.
---

# Task SKILLs Creator

## Purpose

You are invoked by a teammate during AITC workflow execution when they discover something worth capturing as a task SKILL. Your job: spawn a forked subagent to handle the file work (check existing SKILLs, decide merge vs create, write files) so the teammate's context stays clean.

The teammate describes what they found. You do the rest.

## When a Teammate Invokes You

The teammate calls `Skill("task-skills-creator")` with a discovery description. They should invoke you **immediately** when they discover something — not wait until work is done. Real-time capture prevents loss from context compression.

## Procedure

### Step 1 — Collect Discovery Details

Ask the teammate for the minimum information needed:

1. **What happened** — what they expected vs what actually happened
2. **What they did** — concrete steps, commands, or workarounds
3. **Context** — which phase/task this was discovered during
4. **Relevance** — is this a one-time incident or could it recur?

If the teammate already described these in their message, don't re-ask. Extract what's there.

### Step 2 — Dispatch Forked Subagent

Spawn a standalone subagent (no `team_name`) to handle creation. This keeps the file work out of the teammate's context:

```
Agent(
    description="Capture task SKILL discovery",
    subagent_type="general-purpose",
    model="sonnet",
    mode="default",
    prompt="""
    Capture a discovery as a task SKILL file.

    DISCOVERY:
    - What: <teammate's description>
    - Concrete steps: <what they did>
    - Context: <phase/task>
    - Batch: <batch-name>
    - Worktree: <path>

    STEP 1 — Check for existing task SKILLs:
    Run: bash plugins/aitc-workflow/skills/find-task-skills/list-task-skills.sh <batch-name>
    Review the output. For each existing task SKILL, read its frontmatter and
    "## What" / "## Purpose" section.

    STEP 2 — Decide: merge or create?
    - If this discovery fills a gap in an EXISTING task SKILL → edit that file
      (append to "## How" or create a "## Discoveries" entry). This is
      Self-Maintenance.
    - If this discovery supplements a known PROJECT skill (skills/<name>/)
      → create a NEW supplement task SKILL in skills/aitc-task-<batch>/
    - If this is entirely new → create a NEW task SKILL
    - If it's a one-time log entry (not reusable) → skip creation, report "Not reusable"

    STEP 3 — Create or edit the file:
    Files go in: skills/aitc-task-<batch>/ in the worktree.

    NEW task SKILL format:
    ```markdown
    ---
    name: <descriptive-kebab-name>
    description: <one-line description>
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
    <Concrete steps, commands with real values, workaround procedure.
    Zero abstraction is fine here — use actual IPs, flags, paths.>

    ## Discoveries
    (Empty — populated by Self-Maintenance)

    ## Self-Maintenance Rule

    If you loaded this SKILL and something is wrong — a command changed, an IP unreachable,
    a step order incorrect — fix it in this file immediately after completing your work.
    Do not silently work around. Edit:
    1. Correct the outdated information
    2. Append to ## Discoveries with what was wrong and what you changed
    3. No need to consult the Lead
    ```

    SUPPLEMENT task SKILL (if correcting a project skill):
    ```markdown
    ---
    name: <project-skill>-<brief-description>
    description: Supplements <project-skill> with <what this adds/corrects>
    type: task
    task-type: supplement
    supplements: <project-skill-name>
    batch: <batch-name>
    created: <today>
    status: active
    ---

    # Supplement to `<project-skill>`

    ## What
    <What was wrong/missing in the original skill>

    ## How
    <Corrected or additional content. Structure by affected section.>

    ## Discoveries
    (Empty — populated by Self-Maintenance)

    ## Self-Maintenance Rule
    (Same as above)
    ```

    Note: "new" and "supplement" are the only two types you create.
    "instance" type is created only by the Lead or Guardian setup subagent.

    STEP 4 — Report:
    - What file was created or edited
    - Why merge vs create was chosen
    - The file path in the worktree
    """
)
```

### Step 3 — Relay Result to Teammate

Report the subagent's result back to the teammate. They should note the created/edited SKILL in their `## Discoveries` section when reporting completion.

### Step 4 — Teammate Verification

The teammate confirms: "Noted. Will report in Discoveries." This closes the loop.
