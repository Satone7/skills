---
name: <project-skill>-v2
description: Supplements <project-skill> with <what this adds/corrects>
type: task
task-type: supplement
supplements: <project-skill-name>
batch: <batch-name>
created: <YYYY-MM-DD>
status: active
---

# <Skill Name> — Supplement to `<project-skill>`

## Supplemented Skill
- **Skill**: `<project-skill>`
- **Location**: `skills/<project-skill>/`

## Issues Found
<What was wrong, missing, or outdated in the original skill? Be specific —
include the exact section, the incorrect information, and what should have been there.>

## Corrections / Additions
<The corrected or additional content. When promoted, this content should be
merged into the original skill. Structure by affected section.>

### Section: <affected section in original skill>
<Corrected content>

## Discoveries
<Appended during execution. Additional findings beyond the initial correction.>

### <YYYY-MM-DD>: <Discovery Title>
- **Context**: <What was happening>
- **Finding**: <What was learned>
- **Implication**: <How this changes the supplement>

## Self-Maintenance Rule

**If you loaded this SKILL and something is wrong** — the supplement's correction is itself outdated, the target skill has changed, or new issues are discovered beyond the original correction — **fix it in this file immediately after completing your work.** Do not silently work around the issue. Do not only report it to the Lead. Edit this file:

1. Correct or expand the `## Corrections / Additions` section
2. Append a dated entry to `## Discoveries` describing what was wrong and what you changed
3. No need to consult the Lead for corrections — this is the SKILL maintaining itself
