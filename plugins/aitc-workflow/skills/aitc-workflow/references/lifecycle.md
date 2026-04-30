# Lifecycle Mode — Detailed Procedures

This reference contains the detailed procedures for each lifecycle action. The SKILL itself contains the decision logic, classification rules, and boundary conditions.

## Merge Procedure (supplement type)

### Pre-merge Checks

1. Read the task SKILL's `## What` and `## How` sections
2. Read the target project skill's full content
3. Identify where the supplement's content fits:
   - If it corrects a specific section → mark that section for replacement
   - If it adds new content → identify the insertion point
   - If it contradicts existing content → flag for user review

### Generating the Merged Version

1. Start from the target project skill's current content
2. Apply corrections from the supplement's `## How` section
3. If the supplement corrects a procedure, replace the old procedure — don't keep both versions
4. If the supplement adds knowledge, insert it in the most natural location
5. Do NOT merge the `## Discoveries` section — that's session-specific

### Validation

After generating the merged version:
1. Verify frontmatter is intact (name, description unchanged)
2. Verify no duplicate sections
3. Verify internal references still point to correct locations
4. Show the user `git diff` before applying

### On Conflict

If the supplement's corrections conflict with content that was independently updated during execution:
1. Keep the more recent version (execution-time update takes priority)
2. Note the conflict in the commit message
3. Ask the user if they want to review the conflict manually

## Promote Procedure (new type)

### Tier Selection

| Criteria | Target Tier | Location |
|----------|-------------|----------|
| General tooling, debugging, workflows applicable to any project | Global | `~/.claude/skills/<name>/` |
| Domain or project-specific knowledge | Project | `skills/<name>/` |

### Frontmatter Cleanup

When promoting, transform the frontmatter:

**From:**
```yaml
name: <descriptive-kebab-name>
description: <one-line>
type: task
task-type: new
batch: <batch-name>
created: <YYYY-MM-DD>
status: active
```

**To:**
```yaml
name: <descriptive-kebab-name>
description: <one-line — review and improve trigger words>
type: project  # or global
created: <original-date>
promoted: <today>
```

Remove: `task-type`, `batch`, `status`. Add: `promoted`.

### Content Review

Before copying, review the content:
1. Remove any session-specific references (worktree paths, batch names, teammate names)
2. Generalize concrete values into placeholders only if they're truly variable
3. Keep concrete values if they're universally true (e.g., specific compiler flags)
4. Add trigger words to `description` if the skill should auto-trigger in future sessions

### Target Exists

If a skill with the same name already exists at the target location:
1. Ask the user: "A skill named `<name>` already exists. Overwrite / rename / skip?"
2. If overwrite: show diff, confirm
3. If rename: suggest `<name>-v2` or a descriptive variant
4. If skip: keep the task SKILL as-is (don't delete it)

## Archive Procedure (instance type)

1. Create `archived/aitc-task-<batch>/` if it doesn't exist
2. Move the file: `git mv skills/aitc-task-<batch>/<file> archived/aitc-task-<batch>/`
3. The file stays as-is — no frontmatter changes needed
4. Archived files serve as reference for future sessions; they are not loaded by `find-task-skills`

## Cleanup Checklist

After all decisions are executed:
- [ ] `.discovery-hints.md` removed
- [ ] Empty `skills/aitc-task-<batch>/` directory removed
- [ ] All changes staged and committed
- [ ] Summary reported to user with failure count
