# Lifecycle Mode — Archive & Promote Task SKILLs

## Entry Condition

- All teammates have completed and been shut down
- Cross-task synthesis (if specified in plan) is done
- User indicates "wrap up", "archive", "promote", or all tasks have been marked complete

## 3.1 Inventory Task SKILLs

List all files in `skills/aitc-task-<batch>/` (excluding `.discovery-hints.md`).

For each, read the frontmatter to determine type:
- `task-type: new` — entirely new operational knowledge
- `task-type: supplement` with `supplements: <skill>` — corrections or additions to existing skill
- `task-type: instance` with `instance-of: <skill>` — parameterized instance

## 3.2 Present Summary to User

Present a table of all task SKILLs with preliminary recommendations:

| Task SKILL | Type | Supplements / Instance-Of | Content Summary | Recommendation |
|------------|------|---------------------------|-----------------|----------------|
| ... | new | — | ... | Promote to project/global skill |
| ... | supplement | some-skill | ... | Merge into some-skill |
| ... | instance | some-skill | ... | Archive as reference |

Recommendation logic:
- **new + cross-project applicable** → promote to global skill (`~/.claude/skills/`)
- **new + project-specific** → promote to project skill (`skills/`)
- **supplement with still-valid corrections** → merge into the target project skill
- **supplement already absorbed** (target skill was already updated during execution) → delete
- **instance** → archive as reference for future work sessions

Ask the user to confirm or override each recommendation, one at a time.

## 3.3 Execute User's Decisions

### Merge (supplement type)
1. Read both the task SKILL and the original project skill
2. Generate the merged version — fold the task SKILL's corrections into the original
3. Show the user the diff before applying
4. On confirmation, update the project skill
5. Delete the task SKILL (its content now lives in the project skill)

### Promote (new type)
1. Determine target tier (project vs global) based on domain specificity
2. Copy to the target location with frontmatter cleanup:
   - Remove `task-type`, `batch`, `supplements`, `instance-of` fields
   - Set `type: project` or `type: global`
   - Keep `created` date, add `promoted: <YYYY-MM-DD>`
3. Use the final skill name (respecting any renames that happened during execution)

### Archive (instance type, or user preference)
1. Move to `archived/aitc-task-<batch>/`
2. Keep as read-only reference — no further action needed

### Delete
1. Remove the file
2. Appropriate when: the knowledge was a false lead, or has been fully absorbed into another skill

## 3.4 Cleanup

1. Remove `.discovery-hints.md` (transient Lead scratchpad)
2. If `skills/aitc-task-<batch>/` is empty, remove the directory
3. Commit all changes:
   ```bash
   git add docs/plans/<batch>.md
   git add skills/aitc-task-<batch>/   # or archived/
   git add skills/<any-updated-project-skills>/
   git commit -m "chore: archive <name> task SKILLs, promote discoveries"
   ```
4. Report summary: "Work <name> complete. N task SKILLs processed: X merged, Y promoted, Z archived, W deleted."
