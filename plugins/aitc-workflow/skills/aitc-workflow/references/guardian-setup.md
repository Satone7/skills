# Guardian Setup

The Guardian is the first entity spawned after `TeamCreate` — before any worker teammate. Its full protocol is defined in the `guardian` skill (invoke it to read the complete specification). The Lead does not load the guardian skill into its own context. Instead, a subagent handles instance creation.

## Step 1 — Dispatch Guardian Instance Subagent

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
         log path, notes path, plan path, task count)
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

## Step 2 — Lead Verifies and Spawns

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

## Step 3 — Confirm

Wait for the Guardian's confirmation message ("Guardian online. Cron loop active.") before proceeding to spawn worker teammates.

## Why Guardian Must Be First

The Guardian handles unattended operation from the very beginning — permission prompts can appear during the first teammate's work, and without the Guardian there's no one to catch them if the user is away. It also ensures continuous progress monitoring throughout the entire work session, not just after the first teammate is spawned.
