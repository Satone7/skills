---
name: aitc-workflow-lifecycle
version: 1.1.0
description: >
  Manually invoked — NOT auto-triggered. Archive completed task SKILLs and promote
  reusable knowledge into project or global skills. User must explicitly request it
  (e.g., "use aitc-workflow-lifecycle", "wrap up", "archive", "promote", "lifecycle").
  This is the terminal step of the AITC workflow: Plan → Execute → Lifecycle.
---

# AITC Workflow — Lifecycle Mode

Archive completed task SKILLs and promote reusable knowledge. This is the third and final workflow SKILL: Plan → Execute → **Lifecycle** (this one).

## Entry Condition

- All teammates have completed and been shut down
- Cross-task synthesis (if specified in plan) is done
- User indicates "wrap up", "archive", "promote", "lifecycle", or all tasks are marked complete

## Pre-flight

1. Identify the batch name from the plan file or user's message
2. Verify `skills/aitc-task-<batch>/` exists
   - **Not found**: ask the user for the correct batch name; if none exists, the workflow may have skipped Plan/Execute — exit with explanation
3. List all `.md` files (excluding `.discovery-hints.md`)
   - **Empty directory**: report "No task SKILLs to process." and jump to Cleanup (§3.4)

## Workflow

### 3.1 Inventory Task SKILLs

For each file, read the frontmatter. Classify by `task-type`:

| task-type | Meaning | Default Recommendation |
|-----------|---------|----------------------|
| `new` | Entirely new operational knowledge | Promote |
| `supplement` (with `supplements: <skill>`) | Corrections to existing skill | Merge into target |
| `instance` (with `instance-of: <skill>`) | Parameterized instance | Archive |

**Corrupt frontmatter**: if a file is missing `task-type` or has invalid YAML, flag it in the table with type `⚠ corrupt` and recommend delete. Show the user what's wrong before deleting.

### 3.2 Present Summary to User

Present a table of all task SKILLs with preliminary recommendations:

| Task SKILL | Type | Supplements / Instance-Of | Content Summary | Recommendation |
|------------|------|---------------------------|-----------------|----------------|
| ... | new | — | ... | Promote to project/global skill |
| ... | supplement | some-skill | ... | Merge into some-skill |
| ... | instance | some-skill | ... | Archive as reference |
| ... | ⚠ corrupt | — | ... | Delete (reason: ...) |

Recommendation logic:
- **new + cross-project applicable** → promote to global skill (`~/.claude/skills/`)
- **new + project-specific** → promote to project skill (`skills/`)
- **supplement with still-valid corrections** → merge into the target project skill
- **supplement already absorbed** (target skill was already updated during execution) → delete
- **supplement target not found** (the skill it supplements doesn't exist) → promote as standalone or delete
- **instance** → archive as reference

Ask the user to confirm or override each recommendation, one at a time.

### 3.3 Execute User's Decisions

Process each decision independently. If one fails, continue with the rest and report all failures at the end.

#### Merge (supplement type)
1. Read both the task SKILL and the target project skill
   - **Target not found**: report failure, suggest promote-as-new or delete
2. Generate the merged version — fold the task SKILL's `## How` content into the appropriate section of the original
3. Show the user the diff before applying
4. On confirmation, write the merged version
5. Delete the task SKILL

#### Promote (new type)
1. Determine target tier (project vs global) based on domain specificity
2. Copy to the target location with frontmatter cleanup:
   - Remove `task-type`, `batch`, `supplements`, `instance-of` fields
   - Set `type: project` or `type: global`
   - Keep `created` date, add `promoted: <YYYY-MM-DD>`
3. Use the final skill name (respecting renames from execution)
4. **Target already exists**: ask user — overwrite, rename, or skip?

#### Archive (instance type, or user preference)
1. Create `archived/aitc-task-<batch>/` if it doesn't exist
2. Move the file there
3. Keep as read-only reference

#### Delete
1. Remove the file
2. Appropriate when: false lead, fully absorbed into another skill, or corrupt

### 3.4 Cleanup

1. Remove `.discovery-hints.md` if it exists
2. If `skills/aitc-task-<batch>/` is now empty, remove the directory
3. Commit all changes:
   ```bash
   git add docs/plans/<batch>.md
   git add skills/aitc-task-<batch>/   # or archived/
   git add skills/<any-updated-project-skills>/
   git commit -m "chore: archive <name> task SKILLs, promote discoveries"
   ```
4. Report summary: "Work <name> complete. N task SKILLs processed: X merged, Y promoted, Z archived, W deleted. F failures: <list>."

After cleanup, the AITC workflow session is complete.
