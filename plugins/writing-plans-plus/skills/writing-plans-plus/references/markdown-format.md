# Markdown Format Reference

Read this file **only when the user explicitly requests a Markdown plan document**.

## Markdown Format (Human-Readable)

### Single Task Example

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

### Complete Plan Example: `docs/plans/2024-01-15-user-auth.md`

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
- Create: `.env.example`
- Modify: `package.json`

**Steps:**
1. Install Supabase packages: `@supabase/supabase-js`, `@supabase/ssr`
2. Create `.env.example` with placeholder values (do not commit real secrets)

**Validation Criteria:**
- [ ] All packages installed without errors
- [ ] Environment variable placeholders are documented
- [ ] Can initialize Supabase client

---

### Task 2: Database Schema

**ID:** 2 | **Status:** ⬜ Not Started | **Passes:** `false`

... (additional tasks)
```

## Task Status Update in Markdown

### Completed Task

```markdown
**ID:** 1 | **Status:** ✅ Completed | **Passes:** `true`
```

### Task with Issues Found

When issues are discovered during review:

```markdown
**ID:** 3 | **Status:** ❌ Issues Found | **Passes:** `false`

**Issues Found:**
- [ ] No unit tests for client initialization
- [ ] Middleware doesn't handle token refresh edge cases
- [ ] Server client is exposed to browser code
- [ ] Tests exist but have no assertions
```

### After Issues Are Fixed

```markdown
**ID:** 3 | **Status:** ✅ Completed | **Passes:** `true`
```
