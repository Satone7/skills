---
name: <descriptive-name>
description: <one-line description of what this skill covers>
type: task
task-type: new
batch: <batch-name>
created: <YYYY-MM-DD>
status: active
---

# <Skill Name>

## Purpose
<What operation does this skill help with? When should an agent invoke it?>

## Prerequisites
<What must be true or available before using this skill?>

## Procedure
<Step-by-step instructions. Include actual commands with real values where applicable — IPs, credentials, file paths, flag values. Zero abstraction is fine here.>
<Example: `ssh root@192.168.1.105 -p 2222`, not `ssh <user>@<board-ip>`>

## Discoveries
<Appended during execution. Each entry: date, what was learned, why it matters.>

### <YYYY-MM-DD>: <Discovery Title>
- **Context**: <What was happening when this was discovered>
- **Finding**: <What was learned>
- **Implication**: <How this changes future behavior>

## Self-Maintenance Rule

**If you loaded this SKILL and something is wrong** — a command flag changed, an IP is unreachable, a step order is incorrect, a prerequisite is missing — **fix it in this file immediately after completing your work.** Do not silently work around the issue. Do not only report it to the Lead. Edit this file:

1. Correct the outdated information in the relevant section (Purpose, Prerequisites, Procedure)
2. Append a dated entry to `## Discoveries` describing what was wrong and what you changed
3. No need to consult the Lead for corrections — this is the SKILL maintaining itself
