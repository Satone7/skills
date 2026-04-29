---
name: <skill>-<batch>
description: Instance of <skill> configured for batch <batch>
type: task
task-type: instance
instance-of: <skill-name>
batch: <batch-name>
created: <YYYY-MM-DD>
status: active
---

# <Skill Name> — Instance of `<skill>` for `<batch>`

## Parameterization
<The specific parameters, values, and configuration for this batch.
Include ALL non-default values needed to reproduce this instance.

Every value here must be CONCRETE AND REAL. No placeholders. No "<fill-me>".
A teammate reading this skill needs the actual IP address, the actual token,
the actual flag values — not a template to fill in themselves.

Example (guardian instance — every placeholder from the guardian skill filled):
- team_name: "onnx-opt-batch3"
- batch_name: "onnx-opt-batch3"
- instance_skill_path: "skills/aitc-task-onnx-opt-batch3/guardian-onnx-opt-batch3.md"
- log_file_path: "docs/plans/guardian-log-onnx-opt-batch3.md"
- notes_file_path: "/tmp/guardian-onnx-opt-batch3-notes.txt"
- plan_file_path: "docs/plans/onnx-opt-batch3.md"
- task_count: 4
- cron_interval: "*/5 * * * *"

### 2026-04-30: Scoped pane checks to current tmux window
- **Context**: Guardian was checking ALL tmux panes across all windows.
  Non-current-window panes from unrelated sessions appeared in the member list,
  causing false "idle" or "blocked" classifications.
- **Finding**: Teammates only ever appear in the current tmux window.
  Checking other windows produces irrelevant results.
- **Implication**: Updated State Assessment step 3 from "List all tmux panes"
  to "List panes in the CURRENT tmux window only (tmux list-panes -t $(tmux display-message -p '#I'))."
  This is recorded directly in the instance SKILL so future cron ticks use the corrected scope.

Abstraction happens later, during Lifecycle promotion — not here.>

## Differences from Base Skill
<Any deviations from the base skill's default behavior needed for this batch.
If none, state "None — follows base skill exactly.">

## Discoveries
<Appended during execution. Findings that may inform future instances or
the base skill itself.>

### <YYYY-MM-DD>: <Discovery Title>
- **Context**: <What was happening>
- **Finding**: <What was learned>
- **Implication**: <How this affects the base skill or future instances>

## Self-Maintenance Rule

**If you loaded this SKILL and something is wrong** — a parameter value is incorrect, the instance configuration doesn't match reality, the base skill's expected behavior differs from actual — **fix it in this file immediately after completing your work.** Do not silently work around the issue. Do not only report it to the Lead. Edit this file:

1. Correct the outdated value(s) in `## Parameterization` or `## Differences from Base Skill`
2. Append a dated entry to `## Discoveries` describing what was wrong and what you changed
3. No need to consult the Lead for corrections — this is the SKILL maintaining itself
