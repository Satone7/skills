---
name: writing-plans-plus
description: Enhanced planning with structured, machine-readable task format based on writing-plans
---

# Writing Plans Plus

## Overview

This skill extends `superpowers:writing-plans` with **structured task definitions** that are machine-readable and provide explicit completion tracking. Use this when you want plans that can be easily parsed, executed programmatically, or tracked with explicit pass/fail status.

**Key additions over writing-plans:**
- Structured task format (JSON/YAML compatible)
- Required fields for each task (id, title, description, steps, passes)
- Explicit completion tracking via `passes` field
- Validation criteria for each task

**Announce at start:** "I'm using the writing-plans-plus skill to create a structured implementation plan."

**Context:** This should be run in a dedicated worktree (created by brainstorming skill).

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.json`

**Note:** Only save `.md` file when user explicitly requests a human-readable plan document. Default to JSON-only.

---

## Required Reading First

**You MUST read and follow `superpowers:writing-plans` SKILL first.**

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
| `validation_criteria` | array<string> | Specific criteria to verify task completion |
| `estimated_time` | string | Estimated time (e.g., "10m", "1h") |
| `tags` | array<string> | Categories (e.g., ["api", "ui", "test"]) |

---

## Example Structured Task

### Markdown Format (Human-Readable)

```markdown
### Task 3: Supabase Client Setup

**ID:** 3
**Title:** Supabase Client Setup
**Description:** Create server-side and client-side Supabase clients with proper middleware

**Files:**
- Create: `lib/supabase/server.ts`
- Create: `lib/supabase/client.ts`
- Create: `lib/supabase/middleware.ts`

**Steps:**
1. Create server client with service role
2. Create browser client for components
3. Create middleware for session refresh
4. Update root middleware.ts to use Supabase middleware

**Validation Criteria:**
- [ ] Server client can query database
- [ ] Browser client initializes without errors
- [ ] Middleware refreshes expired sessions

**Status:** ⬜ Not Started | Passes: `false`
```

### JSON Format (Machine-Readable)

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
  "estimated_time": "20m",
  "tags": ["setup", "supabase", "auth"]
}
```

---

## Complete Plan Example

### Markdown Output: `docs/plans/2024-01-15-user-auth.md`

```markdown
# User Authentication Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
> **Task Format:** Structured (writing-plans-plus)

**Goal:** Implement complete user authentication with email/password using Supabase

**Architecture:** Use Supabase Auth with server-side sessions. Create reusable auth components and protect routes via middleware.

**Tech Stack:** Next.js 14, Supabase Auth, TypeScript, Tailwind CSS

---

## Task Summary

| ID | Title | Status | Passes |
|----|-------|--------|--------|
| 1 | Project Setup | Not Started | false |
| 2 | Database Schema | Not Started | false |
| 3 | Supabase Client Setup | Not Started | false |
| 4 | Login Page | Not Started | false |
| 5 | Register Page | Not Started | false |
| 6 | Logout Function | Not Started | false |
| 7 | Auth Middleware | Not Started | false |

---

### Task 1: Project Setup

**ID:** 1 | **Status:** ⬜ Not Started | **Passes:** `false`

**Description:** Configure project dependencies and environment

**Files:**
- Create: `.env.local`
- Modify: `package.json`

**Steps:**
1. Install Supabase packages: `@supabase/supabase-js`, `@supabase/ssr`
2. Create `.env.local` with `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. Add `SUPABASE_SERVICE_ROLE_KEY` for server operations

**Validation Criteria:**
- [ ] All packages installed without errors
- [ ] Environment variables are accessible in application
- [ ] Can initialize Supabase client

---

### Task 2: Database Schema

**ID:** 2 | **Status:** ⬜ Not Started | **Passes:** `false`

... (additional tasks)
```

### JSON Output: `docs/plans/2024-01-15-user-auth.json`

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
        "Create .env.local with NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY",
        "Add SUPABASE_SERVICE_ROLE_KEY for server operations"
      ],
      "passes": false,
      "files": {
        "create": [".env.local"],
        "modify": ["package.json"]
      },
      "validation_criteria": [
        "All packages installed without errors",
        "Environment variables are accessible in application",
        "Can initialize Supabase client"
      ],
      "estimated_time": "10m",
      "tags": ["setup", "dependencies"]
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

4. **Markdown only when requested:** If `.md` file exists (user requested it), keep it in sync with JSON
   ```markdown
   **ID:** 1 | **Status:** ✅ Completed | **Passes:** `true`
   ```

---

## Validation Checklist

Before marking any plan complete, verify:

- [ ] Every task has all **Required Fields**
- [ ] Every task has `passes: false` initially
- [ ] Task IDs are unique and sequential
- [ ] File paths use exact relative paths
- [ ] Steps are specific and verifiable
- [ ] Validation criteria are objective (pass/fail)
- [ ] JSON output is saved

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
| Validation criteria | Optional | Required |
| File outputs | `.md` only | `.json` (default), `.md` (optional on request) |
| Dependencies | Implied | Explicit via `depends_on` |

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
