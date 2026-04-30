# Guardian Setup

The Guardian is the first entity spawned after `TeamCreate` — before any worker teammate. Its full protocol is defined in the `guardian` skill (invoke it to read the complete specification).

The guardian instance task SKILL is created during **Plan mode** (`aitc-workflow-plan` §1.6), not during Execute mode. All parameter values are known at plan time — filling placeholders is preparatory work, not orchestration.

## Step 1 — Verify Existing Instance

Read the instance file at `skills/aitc-task-<batch>/guardian-<batch>.md`. Verify all placeholders are filled (no `<...>` remaining). If any placeholders remain, the Plan mode subagent failed — fill and commit before proceeding.

## Step 2 — Spawn the Guardian

Spawn the Guardian using the instance's parameterization:

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

The Guardian will self-configure: create its cron job, initialize log and notes files, and report online via SendMessage.

## Step 3 — Confirm

Wait for the Guardian's confirmation message ("Guardian online. Cron loop active.") before proceeding to spawn worker teammates.

## Why Guardian Must Be First

The Guardian handles unattended operation from the very beginning — permission prompts can appear during the first teammate's work, and without the Guardian there's no one to catch them if the user is away. It also ensures continuous progress monitoring throughout the entire work session, not just after the first teammate is spawned.

