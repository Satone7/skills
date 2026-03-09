# Task Checker Skill Compliance Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the task-checker plugin conform to repository structure conventions and make its evals reproducible and self-contained.

**Architecture:** Restructure the plugin to match `plugins/<plugin>/.claude-plugin/plugin.json` + `plugins/<plugin>/skills/<skill>/SKILL.md`. Replace eval inputs with repo-local sample plans and adjust the skill text to be framework-agnostic.

**Tech Stack:** Markdown + JSON skill definitions, repository `.claude-plugin` marketplace manifests.

---

### Task 1: Align task-checker plugin directory layout

**Files:**
- Create: `plugins/task-checker/.claude-plugin/plugin.json`
- Create: `plugins/task-checker/skills/task-checker/SKILL.md`
- Modify: `plugins/task-checker/evals/evals.json`
- Delete: `plugins/task-checker/SKILL.md`

**Step 1: Validate current plugin layout**

Run: `python -c "import os; assert os.path.exists('plugins/task-checker/SKILL.md')"`
Expected: exit code 0

**Step 2: Add plugin manifest**

Create `plugins/task-checker/.claude-plugin/plugin.json` aligned with existing plugin manifests.

**Step 3: Move SKILL.md into standard skills path**

Create `plugins/task-checker/skills/task-checker/SKILL.md` with the current content (plus improvements from Task 3).

**Step 4: Remove legacy SKILL.md**

Delete `plugins/task-checker/SKILL.md`.

**Step 5: Sanity check**

Run: `python -c "import os; assert os.path.exists('plugins/task-checker/skills/task-checker/SKILL.md')"`
Expected: exit code 0

---

### Task 2: Make task-checker evals self-contained and reproducible

**Files:**
- Create: `plugins/task-checker/evals/example-plan.json`
- Create: `plugins/task-checker/evals/example-plan-missing-criteria.json`
- Modify: `plugins/task-checker/evals/evals.json`

**Step 1: Add a valid writing-plans-plus sample plan**

Create `plugins/task-checker/evals/example-plan.json` with:
- Plan metadata: `project`, `goal`, `description`, `architecture`, `tech_stack`, `created_at`
- At least 3 tasks with required fields (`id`, `title`, `description`, `steps`, `passes`)
- Include `validation_criteria` per task and at least one task with `depends_on`

**Step 2: Add a “missing criteria” sample plan**

Create `plugins/task-checker/evals/example-plan-missing-criteria.json` where at least one task lacks `validation_criteria` (or has vague criteria) to exercise the preconditions and “do not guess” behavior.

**Step 3: Update evals.json to reference repo-local files**

Replace any absolute paths in prompts/files with repo-relative paths under `plugins/task-checker/evals/`.

**Step 4: Validate JSON formatting**

Run: `python -m json.tool plugins/task-checker/evals/evals.json > /dev/null`
Expected: exit code 0

Run: `python -m json.tool plugins/task-checker/evals/example-plan.json > /dev/null`
Expected: exit code 0

Run: `python -m json.tool plugins/task-checker/evals/example-plan-missing-criteria.json > /dev/null`
Expected: exit code 0

---

### Task 3: Improve task-checker SKILL.md portability and clarity

**Files:**
- Modify: `plugins/task-checker/skills/task-checker/SKILL.md`

**Step 1: Make “dynamic verification” language-agnostic**

Replace the ctest/gtest-specific language with guidance to prefer project-native minimal test commands, while keeping ctest as one example.

**Step 2: Add optional compatibility section to frontmatter**

Add `compatibility` in frontmatter describing required capabilities (read plan file, search code, optional local test runs) without binding to a single ecosystem.

**Step 3: Verify the skill is still under 500 lines and the output template remains intact**

Run: `python -c "import pathlib; p=pathlib.Path('plugins/task-checker/skills/task-checker/SKILL.md'); assert p.exists(); assert sum(1 for _ in p.open()) < 500"`
Expected: exit code 0

---

### Task 4: Register task-checker plugin in marketplace.json

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Add plugin entry**

Add a new entry to `plugins[]`:
- `name`: `task-checker`
- `source`: `./plugins/task-checker`
- `description`: short trigger-focused description matching the skill’s frontmatter.

**Step 2: Validate JSON formatting**

Run: `python -m json.tool .claude-plugin/marketplace.json > /dev/null`
Expected: exit code 0

