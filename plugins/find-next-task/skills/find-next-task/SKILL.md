---
name: find-next-task
description: Find the next executable task from writing-plans-plus JSON plan files. Use this skill whenever you need to locate the next task to work on, check task status, or understand what to do next in a project with structured plans. Always use this when the user asks "what's next", "find the next task", "show pending tasks", or wants to continue working on a plan.
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
   - `**/*.json` (full project search, filter for files containing `tasks` array)

2. **Validate writing-plans-plus format** for each candidate file:
   - Must have a top-level `tasks` array
   - Each task must have: `id`, `title`, `description`, `steps`, `passes`
   - The `passes` field must be boolean (true/false)

3. **If no valid plan files found:**
   - Announce: "No writing-plans-plus compatible plan files found in this project."
   - Do NOT proceed further - this skill is not applicable.

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
   - Present the list to the user with progress percentages
   - Let the user select which plan to work on
   - Format:
     ```
     Found multiple plans with pending tasks:
     1. phase1-setup.json (5/10 tasks completed, 50%)
     2. phase2-core.json (0/15 tasks completed, 0%)
     3. phase3-testing.json (0/8 tasks completed, 0%)

     Which plan would you like to work on?
     ```

3. **If only one plan has pending tasks:**
   - Automatically select that plan

4. **If all plans are completed:**
   - Announce: "All plans are completed!"
   - Show summary of all plans and their completion status

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

### Find the Next Task

1. **Iterate through tasks in ID order**
2. **Find the FIRST task that is ready** (as defined above)
3. **If no tasks are ready but some are incomplete:**
   - This means there are tasks waiting on dependencies
   - Show a summary of which tasks are blocked and by what
   - Example:
     ```
     No tasks are ready to execute yet.
     Blocked tasks:
     - Task 2: "Database Setup" (depends on Task 1 which is not completed)
     - Task 3: "API Implementation" (depends on Task 2 which is not completed)
     ```

---

## Step 3: Output the Result

### Output Format

**Always output JSON format** as specified by the user. The output should be a JSON object with this structure:

```json
{
  "plan_file": "/absolute/path/to/plan.json",
  "plan_name": "User Authentication Implementation",
  "plan_progress": {
    "completed": 3,
    "total": 10,
    "percentage": 30
  },
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

### Field Explanations

- **plan_file**: Absolute path to the selected plan JSON file
- **plan_name**: The project name or description from the plan
- **plan_progress**: Statistics about overall plan completion
- **next_task**: The full task object of the next ready task (or null if none)
- **task_summary**: Brief status of all tasks in the plan

### Include All Task Fields

When outputting `next_task`, include ALL fields present in the original task, not just the ones shown in the example. This includes optional fields like `issue`, `completed_at`, `completed_by`, `notes`, `tags`, `estimated_time`, etc.

---

## Step 4: Present the Result to User

After outputting the JSON, also provide a human-readable summary:

```
Found next task!

📋 Plan: User Authentication Implementation (3/10 tasks, 30%)

🎯 Next Task: #4 - Login Page Implementation
   Description: Create the login page with email/password form and validation

📝 Steps:
   1. Create login page component
   2. Add form validation
   3. Connect to Supabase auth
   4. Add error handling

✅ Validation Criteria:
   - Login form renders without errors
   - Email validation works correctly
   - Successful login redirects to dashboard
   - Error messages are displayed properly

[JSON output shown above]
```

---

## Special Cases

### Tasks with Issues

If a task has an `issue` field (array of strings):
- Include it in the JSON output
- In the human-readable summary, highlight it:
  ```
  ⚠️ This task has issues that need to be fixed:
     - No unit tests for login form
     - Error handling doesn't cover network failures
  ```
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
- [ ] Also provided a human-readable summary

**Remember:** Output JSON FIRST, then the human-readable summary.
