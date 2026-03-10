---
name: find-next-task
description: Find the next executable task from writing-plans-plus JSON plan files. Use this skill whenever you need to locate the next task to work on, check task status, or understand what to do next in a project with structured plans. Always use this when the user asks "what's next", "find the next task", "show pending tasks", or wants to continue working on a plan.
context: fork
---

# Find Next Task

## Overview

This skill helps you find the next executable task from `writing-plans-plus` compatible JSON plan files. It understands task dependencies, status tracking, and plan file organization.

**Announce at start:** "I'm using the find-next-task skill to locate the next task."

---

## Prerequisite Check

First, verify that the project has compatible plan files:

1. **Look for plan files** in this priority order:
   - `docs/plans/*.json`
   - `*.json` (project root)
   - `**/*.json` (full project search) ONLY if the user explicitly asks for exhaustive search or the repo is known to be small

   If you do a full project search, apply safety limits:
   - Stop after finding 50 candidate JSON files
   - Skip JSON files larger than ~1MB
   - Prefer reading just enough to confirm a top-level `tasks` array exists before fully parsing

2. **Validate writing-plans-plus format** for each candidate file:
   - Must have a top-level `tasks` array
   - Each task must have: `id`, `title`, `description`, `steps`, `passes`
   - The `passes` field must be boolean (true/false)
   - If a candidate file is invalid JSON, skip it and record a warning

3. **If no valid plan files found:**
   - Output a JSON object with an `error` field and stop.

---

## Step 1: Find and Select Plan

### List Candidate Plans

For all valid plan files found:
- Read each file's content
- Calculate progress: (number of tasks with `passes: true`) / (total tasks)
- Group plans into categories:
  - **In progress**: Some tasks completed, some remaining
  - **Not started**: All tasks `passes: false`
  - **Completed**: All tasks `passes: true`

### Detect Plan Ordering

Check if plan filenames have obvious sequential patterns:
- Look for: `phase1`, `phase2`, `phase3`, etc.
- Look for: `part1`, `part2`, `step1`, `step2`, etc.
- Look for: `v1`, `v2`, `v1.1`, `v1.2`, etc.
- Look for numeric prefixes: `01-`, `02-`, etc.

### Plan Selection Logic

1. **If obvious sequential pattern exists:**
   - Process plans in that order
   - Find the first plan that is NOT fully completed
   - Use that plan

2. **If no obvious order AND multiple in-progress/not-started plans:**
   - Output JSON with `selection_required: true` and include candidates with progress
   - Do NOT output prose outside JSON

3. **If only one plan has pending tasks:**
   - Automatically select that plan

4. **If all plans are completed:**
   - Output JSON with `next_task: null` and a completed summary

---

## Step 2: Analyze Plan and Find Next Task

Once a plan is selected:

### Read and Parse the Plan

Read the JSON file content. You need to understand:
- The plan's overall goal/description
- All tasks with their full details
- Dependency relationships (`depends_on` field)

### Task Readiness Check

For each task in the plan (in ID order):

A task is **ready** if:
1. `passes: false` (not completed)
2. All dependencies (from `depends_on` array) are satisfied:
   - For each dependency ID in `depends_on`:
     - Find that task in the plan
     - Verify its `passes` is `true`
   - If no `depends_on` field or empty array, this condition is automatically satisfied

If a dependency ID is missing from the plan, treat the task as not ready and record it as blocked by missing dependencies in the output.

### Find the Next Task

1. **Iterate through tasks in ID order**
2. **Find the FIRST task that is ready** (as defined above)
3. **If no tasks are ready but some are incomplete:**
   - This means there are tasks waiting on dependencies
   - Output a JSON object with `next_task: null` and include blocked reasons in `task_summary`
   - If you detect a circular dependency, set `cycle_detected: true` and include a best-effort list of tasks involved

---

## Step 3: Output the Result

### Output Format
Always output a single JSON object and nothing else (no prose, no markdown fences). Use this structure:

```json
{
  "plan_file": "/absolute/path/to/plan.json",
  "plan_name": "User Authentication Implementation",
  "plan_progress": {
    "completed": 3,
    "total": 10,
    "percentage": 30
  },
  "selection_required": false,
  "plan_candidates": null,
  "cycle_detected": false,
  "warnings": [],
  "error": null,
  "next_task": {
    "id": 4,
    "title": "Login Page Implementation",
    "description": "Create the login page with email/password form and validation",
    "steps": [
      "Create login page component",
      "Add form validation",
      "Connect to Supabase auth",
      "Add error handling"
    ],
    "passes": false,
    "depends_on": [1, 2, 3],
    "validation_criteria": [
      "Login form renders without errors",
      "Email validation works correctly",
      "Successful login redirects to dashboard",
      "Error messages are displayed properly"
    ],
    "skills": ["using-superpowers", "test-driven-development"],
    "files": {
      "create": ["app/login/page.tsx", "app/login/components/LoginForm.tsx"],
      "modify": ["app/layout.tsx"],
      "test": ["app/login/login.test.tsx"]
    }
  },
  "task_summary": [
    { "id": 1, "title": "Project Setup", "passes": true },
    { "id": 2, "title": "Supabase Client Setup", "passes": true },
    { "id": 3, "title": "Database Schema", "passes": true },
    { "id": 4, "title": "Login Page Implementation", "passes": false, "ready": true },
    { "id": 5, "title": "Register Page", "passes": false, "ready": false, "blocked_by": [4] }
  ]
}
```

### Error and Warning Schemas

Use stable, machine-parseable structures:

```json
{
  "error": {
    "code": "NO_PLAN_FOUND",
    "message": "No writing-plans-plus compatible plan files found.",
    "details": {
      "searched": ["docs/plans/*.json", "*.json"]
    }
  },
  "warnings": [
    {
      "code": "INVALID_JSON_SKIPPED",
      "message": "Skipped invalid JSON candidate plan.",
      "file": "docs/plans/bad.json"
    }
  ]
}
```

- `error` MUST be either null or an object: `{ code, message, details? }`
- `warnings` MUST be an array of objects: `{ code, message, file? }`

Recommended `error.code` values:
- `NO_PLAN_FOUND`
- `PLAN_SELECTION_REQUIRED`
- `PLAN_PARSE_FAILED`
- `PLAN_SCHEMA_INVALID`

Recommended `warnings[].code` values:
- `INVALID_JSON_SKIPPED`
- `PLAN_SCHEMA_INVALID_SKIPPED`
- `MISSING_DEPENDENCY`
- `CYCLE_DETECTED`

### Field Explanations

- **plan_file**: Absolute path to the selected plan JSON file
- **plan_name**: The project name or description from the plan
- **plan_progress**: Statistics about overall plan completion
- **selection_required**: If true, `next_task` must be null and `plan_candidates` must be present
- **plan_candidates**: Array of candidate plans when selection is required, otherwise null
- **warnings**: Non-fatal issues encountered (invalid JSON candidates skipped, missing dependency IDs, etc.)
- **error**: Fatal error object or null
- **next_task**: The full task object of the next ready task (or null if none)
- **task_summary**: Brief status of all tasks in the plan

### Include All Task Fields

When outputting `next_task`, include ALL fields present in the original task, not just the ones shown in the example. This includes optional fields like `issue`, `completed_at`, `completed_by`, `notes`, `tags`, `estimated_time`, etc.

---

## Special Cases

### Tasks with Issues

If a task has an `issue` field (array of strings):
- Include it in the JSON output
- Include it as-is in `next_task.issue` and/or enrich the corresponding entry in `task_summary` with `issues` for visibility
- Still treat it as a normal task (follow user's instruction: "按正常顺序处理")

### Multiple Ready Tasks

If multiple tasks are ready (no dependencies or dependencies satisfied):
- Pick the one with the **smallest ID**
- The others are ready but not "next"
- In the task_summary, mark them as `"ready": true` but don't select them as `next_task`

---

## Quick Reference: Checklist

Before outputting the result, verify:

- [ ] Found at least one valid writing-plans-plus JSON file
- [ ] Selected the appropriate plan (sequential order or user-selected)
- [ ] Correctly identified task readiness (passes: false AND dependencies satisfied)
- [ ] Output is valid JSON with all required fields
- [ ] Included ALL task fields from the original plan
- [ ] Output contains no extra prose outside the JSON object
