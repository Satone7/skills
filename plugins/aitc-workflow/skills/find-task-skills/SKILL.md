---
name: find-task-skills
version: 1.1.0
description: >
  Discover and load relevant task SKILLs from the active task SKILL directory. Used by
  teammates during AITC workflow execution to find operational knowledge without the Lead
  manually listing every task SKILL in the prompt. Invoke via Skill("find-task-skills")
  at the start of every teammate task, and again when encountering a problem that existing
  task SKILLs might address. Also invoked internally by task-skills-creator subagents.
---

# Find Task SKILLs

## Purpose

You are a teammate in an AITC workflow execution. Task SKILLs — concrete operational knowledge discovered during this work session — exist as markdown files in `skills/aitc-task-<batch>/`. Your job is to find and load the ones relevant to your task before you begin work.

This skill replaces the Lead manually listing task SKILL references in your prompt. You discover them yourself.

## When to Use

Invoke this skill at these points during your work:

| When | Why |
|------|-----|
| **Before starting any task phase** | Load known pitfalls and procedures before you hit them |
| **Encountering an error or unexpected behavior** | A previous teammate may have already solved this |
| **About to use a tool or system you haven't worked with** | Someone may have documented quirks |
| **After task-skills-creator creates a new task SKILL** | Verify it appears in the directory listing |

## Procedure

### Step 1 — Identify the Active Task SKILL Directory

Your prompt should specify the batch name. If it doesn't, ask the Lead: "Which task SKILL directory should I search?"

The directory is at `skills/aitc-task-<batch>/`.

Note: `skills/` contains only ONE active `aitc-task-xxx` directory at a time — the one matching the batch name in your prompt. Inactive task SKILL directories from past sessions are in `archived/`. Do NOT load task SKILLs from `archived/`; they belong to different work sessions and their information may be stale.

### Step 2 — List Available Task SKILLs

Run the listing script to get a structured overview of all task SKILLs in the active directory:

```bash
bash plugins/aitc-workflow/skills/find-task-skills/list-task-skills.sh <batch-name>
```

Or for machine-parseable output:

```bash
bash plugins/aitc-workflow/skills/find-task-skills/list-task-skills.sh --json <batch-name>
```

The script handles these cases automatically:

| Scenario | Script Behavior |
|----------|----------------|
| One `aitc-task-xxx` directory matches the batch name | Lists all SKILL.md files with frontmatter extracted |
| Multiple `aitc-task-xxx` directories | Reports ALL directories with creation/modified times and skill counts. Exits with code 1. Asks the agent to identify the active one. |
| No `aitc-task-xxx` directory | Reports empty, exits 0 |
| Batch name given, directory not found | Reports not found, exits 1 |

If the script reports multiple directories, this is an anomaly — `skills/` should only contain one active task SKILL directory. Ask the Lead: "Multiple aitc-task directories found. Which is active? Should the others be moved to archived/?"

If the directory is empty (no `.md` files), report: "No task SKILLs available yet." and proceed with your task using only the knowledge in your prompt.

### Step 3 — Judge Relevance

The script already extracts `name`, `description`, `task-type`, `status`, `supplements`/`instance-of` from each SKILL's frontmatter. Review the output:

- Skip any file with `status: superseded` or `status: merged` — these have already been absorbed.
- For each active task SKILL, judge: **does this relate to my assigned task?** Read the description. If the task SKILL covers a tool, system, or operation you'll be working with, it's relevant. If it's about an unrelated domain, skip it.

### Step 4 — Load Relevant Task SKILLs

For each task SKILL you judged relevant, read the ENTIRE file. Pay special attention to:
- `## Prerequisites` — what must be true before you can use this knowledge
- `## Procedure` — step-by-step instructions; values are CONCRETE and REAL, not placeholders
- `## Parameterization` (instance type) — actual parameters for this session
- `## Corrections / Additions` (supplement type) — what the original skill got wrong

Follow the procedure exactly. Do not second-guess concrete values — they were placed there by someone who discovered them through direct experience.

### Step 5 — Apply Self-Maintenance Rule

Each task SKILL ends with a `## Self-Maintenance Rule`. If you find any information in a loaded task SKILL that doesn't match reality:

1. **Edit the file directly** — correct the outdated section
2. **Append to `## Discoveries`** — record what you found and what you changed
3. **Report in your completion message** — under `## Discoveries > Self-Maintenance`

Do not silently work around incorrect information. Fix it.

### Step 6 — Report

In your first completion message to the Lead, include:

```
Task SKILLs loaded:
- <name>: <one-line summary> (relevant because: <reason>)
- <name>: <one-line summary> (relevant because: <reason>)
- None (if no relevant task SKILLs found)
```

This lets the Lead verify you found and loaded the right knowledge.
