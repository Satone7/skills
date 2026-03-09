---
name: writing-plans-plus
description: Enhanced planning with structured, machine-readable task format based on writing-plans. Use this skill whenever you need to create implementation plans with explicit completion tracking, cross-validation issue tracking, or machine-readable JSON output. Always use this when planning software development tasks, especially when tasks need to be executed by other agents or reviewed later.
---

# Writing Plans Plus

## Overview

This skill extends `superpowers:writing-plans` with **structured task definitions** that are machine-readable and provide explicit completion tracking. Use this when you want plans that can be easily parsed, executed programmatically, or tracked with explicit pass/fail status.

**Key additions over writing-plans:**
- Structured task format (JSON/YAML compatible)
- Required fields for each task (id, title, description, steps, passes)
- Explicit completion tracking via `passes` field
- Support for validation criteria per task (strongly recommended)

**Announce at start:** "I'm using the writing-plans-plus skill to create a structured implementation plan."

**Context:** This should be run in a dedicated worktree (created by brainstorming skill).

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.json`

**Note:** Only save `.md` file when user explicitly requests a human-readable plan document. Default to JSON-only. When Markdown format is requested, read `references/markdown-format.md` for format requirements and examples.

---

## Compatibility and Dependencies

This skill references other skills in the `superpowers:*` ecosystem.

- If `superpowers:writing-plans` is available, read and follow it first.
- If it is not available, proceed anyway and apply these principles directly:
  - Keep tasks small and verifiable
  - Use exact file paths
  - Prefer objective validation steps before marking tasks complete

This repository does not bundle `superpowers:*` skills. Install them separately if you want the full workflow.

---

## Required Reading First

If `superpowers:writing-plans` is available, read and follow it first.

This skill builds on top of writing-plans - all principles from that skill apply:
- Bite-sized tasks (2-5 minutes each)
- Exact file paths
- Complete code in plan
- TDD approach
- Frequent commits

The following sections ONLY document what is ADDED or CHANGED in writing-plans-plus.

---

## Structured Task Format

Each task MUST be defined with the following fields:

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | number/string | Unique identifier for the task (1, 2, 3... or "T1", "T2"...) |
| `title` | string | Brief, actionable title (imperative mood) |
| `description` | string | Clear description of what this task accomplishes |
| `steps` | array<string> | List of specific, verifiable steps to complete |
| `passes` | boolean | Completion status - `false` by default, `true` when done |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `files` | object | Files to create/modify: `{ create: [...], modify: [...], test: [...] }` |
| `depends_on` | array<number/string> | IDs of tasks that must complete before this one |
| `validation_criteria` | array<string> | Specific criteria to verify task completion (strongly recommended) |
| `skills` | array<string> | Skills the executing agent should load (see [Recommended Skills](#recommended-skills) below; default: `["using-superpowers"]`) |
| `issue` | array<string> | **Cross-validation issues**: List of problems found during task review (see [Task Cross-Validation Protocol](#task-cross-validation-protocol)) |
| `completed_at` | string | ISO timestamp when task was completed |
| `completed_by` | string | Who completed the task |
| `notes` | string | Additional notes about completion |

---

## Example Structured Task

### JSON Format (Machine-Readable, Recommended)

```json
{
  "id": 3,
  "title": "Supabase Client Setup",
  "description": "Create server-side and client-side Supabase clients with proper middleware",
  "steps": [
    "Create server client with service role",
    "Create browser client for components",
    "Create middleware for session refresh",
    "Update root middleware.ts to use Supabase middleware"
  ],
  "passes": false,
  "files": {
    "create": [
      "lib/supabase/server.ts",
      "lib/supabase/client.ts",
      "lib/supabase/middleware.ts"
    ],
    "modify": [
      "middleware.ts"
    ]
  },
  "validation_criteria": [
    "Server client can query database",
    "Browser client initializes without errors",
    "Middleware refreshes expired sessions"
  ],
  "skills": ["using-superpowers", "test-driven-development"]
}
```

---

## Complete Plan Example

### JSON Output (Default): `docs/plans/2024-01-15-user-auth.json`

```json
{
  "project": "User Authentication",
  "description": "Implement complete user authentication with email/password using Supabase",
  "goal": "Implement complete user authentication with email/password using Supabase",
  "architecture": "Use Supabase Auth with server-side sessions. Create reusable auth components and protect routes via middleware.",
  "tech_stack": ["Next.js 14", "Supabase Auth", "TypeScript", "Tailwind CSS"],
  "created_at": "2024-01-15",
  "tasks": [
    {
      "id": 1,
      "title": "Project Setup",
      "description": "Configure project dependencies and environment",
      "steps": [
        "Install Supabase packages: @supabase/supabase-js, @supabase/ssr",
        "Create .env.example with placeholder values (do not commit real secrets)"
      ],
      "passes": false,
      "files": {
        "create": [".env.example"],
        "modify": ["package.json"]
      },
      "validation_criteria": [
        "All packages installed without errors",
        "Environment variable placeholders are documented",
        "Can initialize Supabase client"
      ],
      "skills": ["using-superpowers"]
    }
    ... (additional tasks)
  ]
}
```

---

## Task Update Protocol

When updating task status during execution:

1. **Update JSON file** - Only update `.json` file by default
2. **Set `passes: true`** only when ALL validation criteria pass
3. **Add completion metadata:**
   ```json
   {
     "passes": true,
     "completed_at": "2024-01-15T10:30:00Z",
     "completed_by": "Claude",
     "notes": "All validation criteria passed"
   }
   ```

4. **Markdown only when requested:** If `.md` file exists (user requested it), keep it in sync with JSON. See `references/markdown-format.md` for Markdown format examples.

---

## Task Cross-Validation Protocol

When reviewing a task that was previously marked as completed (`passes: true`), you must validate the implementation and update the task status if issues are found.

### When to Perform Cross-Validation

Cross-validation should be performed:
- After task execution but before claiming completion
- When reviewing another agent's work
- When resuming work on a previously completed plan
- When verification-before-completion skill is used

### Common Issues to Check For

| Issue Category | Examples |
|----------------|----------|
| **Implementation mismatch** | Code doesn't match task description, missing functionality, incorrect approach |
| **Test coverage** | No unit tests, tests don't cover key scenarios, tests missing assertions |
| **Test failures** | Existing tests fail, new tests fail, flaky tests |
| **Quality issues** | Code doesn't follow standards, missing error handling, security vulnerabilities |

### When Issues Are Found

If any issues are discovered during review:

1. **Set `passes: false`** - Roll back the completion status
2. **Add `issue` field** - Array of strings describing each problem found
3. **Keep completion metadata** - Preserve `completed_at`, `completed_by` for audit trail (optional)
4. **Update task description if needed** - If task description was ambiguous or incorrect, update it to match what should have been implemented

**Example: Task with issues found during review**
```json
{
  "id": 3,
  "title": "Supabase Client Setup",
  "description": "Create server-side and client-side Supabase clients with proper middleware",
  "steps": [
    "Create server client with service role",
    "Create browser client for components",
    "Create middleware for session refresh",
    "Update root middleware.ts to use Supabase middleware"
  ],
  "passes": false,
  "issue": [
    "No unit tests for client initialization",
    "Middleware doesn't handle token refresh edge cases",
    "Server client is exposed to browser code",
    "Tests exist but have no assertions"
  ],
  "files": {
    "create": [
      "lib/supabase/server.ts",
      "lib/supabase/client.ts",
      "lib/supabase/middleware.ts"
    ],
    "modify": [
      "middleware.ts"
    ]
  },
  "validation_criteria": [
    "Server client can query database",
    "Browser client initializes without errors",
    "Middleware refreshes expired sessions"
  ],
  "completed_at": "2024-01-15T10:30:00Z",
  "completed_by": "Claude",
  "notes": "Initial implementation completed but issues found during review"
}
```

### When Issues Are Fixed

After the issues have been resolved:

1. **Remove the `issue` field** - Do NOT keep it with an empty array
2. **Set `passes: true`** - Mark the task as completed again
3. **Update task description if necessary** - Ensure description matches the actual implementation
4. **Update completion metadata** - Set new `completed_at` and `completed_by`
5. **Add notes about the fix** - Document what was changed

**Example: Task after issues are fixed**
```json
{
  "id": 3,
  "title": "Supabase Client Setup",
  "description": "Create server-side and client-side Supabase clients with proper middleware and test coverage",
  "steps": [
    "Create server client with service role",
    "Create browser client for components",
    "Create middleware for session refresh",
    "Update root middleware.ts to use Supabase middleware",
    "Add unit tests for all clients and middleware"
  ],
  "passes": true,
  "files": {
    "create": [
      "lib/supabase/server.ts",
      "lib/supabase/client.ts",
      "lib/supabase/middleware.ts",
      "lib/supabase/server.test.ts",
      "lib/supabase/client.test.ts",
      "lib/supabase/middleware.test.ts"
    ],
    "modify": [
      "middleware.ts"
    ]
  },
  "validation_criteria": [
    "Server client can query database",
    "Browser client initializes without errors",
    "Middleware refreshes expired sessions",
    "All unit tests pass with meaningful assertions"
  ],
  "completed_at": "2024-01-15T14:45:00Z",
  "completed_by": "Claude",
  "notes": "Fixed issues: Added comprehensive tests, secured server client, improved middleware error handling"
}
```

---

## Recommended Skills

When specifying the `skills` field, use this guide to select appropriate skills. When in doubt, use `["using-superpowers"]`.

### Core Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `using-superpowers` | Foundation skill that establishes skill usage workflow | **Always include this first** - it's the base for all other skills |
| `brainstorming` | Explore requirements and design before implementation | Tasks involving creative work, new features, or complex changes |
| `writing-plans` | Create implementation plans | Planning tasks, or when writing-plans-plus isn't available |
| `executing-plans` | Execute written plans task-by-task | When this plan is being executed step-by-step |
| `subagent-driven-development` | Execute independent tasks in parallel | Plans with multiple independent tasks that can run concurrently |

### Development Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `test-driven-development` | Write tests before implementation code | Any task involving code changes - especially new features |
| `systematic-debugging` | Debug issues systematically | Tasks involving bug fixes or investigating unexpected behavior |
| `verification-before-completion` | Verify work before claiming completion | Final review tasks, or when quality assurance is critical |

### Code Quality & Review

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `requesting-code-review` | Request review before merging | Completing major features or changes that need review |
| `receiving-code-review` | Process review feedback rigorously | When implementing code review suggestions |
| `simplify` | Review and improve code quality | Refactoring tasks or code cleanup |

### Git & Workflow

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `using-git-worktrees` | Create isolated worktrees for feature work | Starting new feature development that needs isolation |
| `finishing-a-development-branch` | Complete and integrate work | When implementation is complete and ready for merge |

### Skill Development

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `skill-creator` | Create and improve skills | Tasks involving skill creation or modification |
| `writing-skills` | Verify skills work before deployment | When creating or updating skills |

### Example Usage

```json
{
  "skills": ["using-superpowers", "test-driven-development"]
}
```

```json
{
  "skills": ["using-superpowers", "brainstorming", "writing-plans-plus"]
}
```

```json
{
  "skills": ["using-superpowers", "systematic-debugging", "verification-before-completion"]
}
```

---

## Validation Checklist

Before marking any plan complete, verify:

- [ ] Every task has all **Required Fields**
- [ ] Every task has `passes: false` initially
- [ ] Task IDs are unique and sequential
- [ ] File paths use exact relative paths
- [ ] Steps are specific and verifiable
- [ ] If present, validation criteria are objective (pass/fail)
- [ ] JSON output is saved

### Cross-Validation Checklist

When reviewing completed tasks:

- [ ] Implementation matches task description
- [ ] Tests exist and cover key scenarios
- [ ] All tests pass
- [ ] Tests have meaningful assertions (not just empty tests)
- [ ] If issues found: `passes` is `false` AND `issue` array exists with clear descriptions
- [ ] If issues fixed: `issue` field is REMOVED (not empty array) AND `passes` is `true`
- [ ] Task description updated if implementation differs from original plan

---

## Integration with Executing Plans

When this plan is executed via `superpowers:executing-plans`:

1. **Execution order** follows task IDs by default
2. **Dependency resolution:** Tasks with `depends_on` must wait for dependencies
3. **Status updates:** After each task, update `passes` in JSON file
4. **Validation:** Run validation criteria before marking `passes: true`
5. **Checkpointing:** Each completed task is a checkpoint - can resume from any point

---

## Summary of Differences from writing-plans

| Aspect | writing-plans | writing-plans-plus |
|--------|---------------|-------------------|
| Task format | Markdown free-form | Structured with required fields |
| Completion tracking | Implicit | Explicit via `passes` field |
| Machine readable | No | Yes (JSON output) |
| Validation criteria | Optional | Strongly recommended |
| File outputs | `.md` only | `.json` (default), `.md` (optional on request) |
| Dependencies | Implied | Explicit via `depends_on` |
| Skill guidance | No | Explicit via `skills` field |
| Issue tracking | No | Explicit via `issue` field for cross-validation |
| Audit trail | No | `completed_at`, `completed_by` for completion history |

---

## Quick Reference: Required Fields Checklist

For each task, ensure you have:

```yaml
id: number or string (unique)
title: string (imperative mood)
description: string (what it accomplishes)
steps: array of strings (specific actions)
passes: boolean (false by default)
# Plus optional fields as needed
```

**Remember:** Read `superpowers:writing-plans` SKILL first, then apply this structured format on top.
