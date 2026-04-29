# Verification

When all teammates for a task report completion, dispatch a standalone verification subagent. The verification covers all teammates assigned to this task — for role-split tasks, verify the integrated output of all roles together, not each role in isolation.

## Verification Subagent Prompt

```
Agent(
    description="Verify task <task-name> deliverables",
    subagent_type="general-purpose",
    model="opus",
    mode="default",
    prompt="""
    Verify ALL deliverables for task <task-name> in worktree <path>.

    TEAMMATES ON THIS TASK:
    - <name> (<role>): <scope>
    - <name> (<role>): <scope>

    PHASE-BY-PHASE CHECKLIST (across all teammates):
    [Checklist items from the plan's acceptance criteria, expanded
     with concrete file paths and expected outputs. For role-split
     tasks, verify integration points between roles — does the
     implementer's output match the researcher's spec?]

    DISCOVERY CHECK:
    - [ ] Each teammate reported Discoveries for their phases
    - [ ] Cross-check: any error-recovery pattern in execution logs
          that was not reported as a Discovery → FAIL
    - [ ] For role-split tasks: any handoff gap between roles
          (researcher described X but implementer built Y) → FAIL

    Report: PASS/FAIL with detailed issue list per teammate.
    If FAIL: specify which teammate(s) need to fix what.
    """
)
```

## Why Opus

Use `opus` for verification because it requires:
- Cross-referencing multiple output files for consistency
- Judging whether an empty output is a methodology error or a genuine result
- Identifying subtle quality issues like incomplete analysis or unsupported claims
- For role-split tasks: detecting integration gaps between independently-working teammates

Use a standalone subagent (no `team_name`) because verification is fire-and-forget — it checks, reports, and exits. It doesn't need the shared task list or inter-agent messaging.

## Rework Protocol

1. Extract the specific fix list from the verification output, routed per teammate
2. Send to each teammate that had failures: "Verification found N issues in your scope. Fix each one: 1. ... 2. ..."
3. Teammates fix and re-report completion
4. When all teammates for the task have re-reported, dispatch a fresh verification subagent (new instance, same checklist)
5. Repeat until PASS for all teammates
6. If a teammate fails verification 3 times, the Lead intervenes directly — the issue is likely beyond what the teammate can self-correct

## After PASS

1. Send shutdown_request to each teammate via SendMessage
2. Wait for all teammates to confirm exit (the teammate process exits and its tmux pane closes automatically)
3. For each teammate, verify the tmux pane is gone. The pane ID was recorded at spawn time. Confirm:
   ```bash
   tmux list-panes -F '#{pane_id}' | grep -c '<pane-id>'
   ```
   If the pane still exists (count > 0), the teammate didn't exit cleanly. Kill it:
   ```bash
   tmux kill-pane -t <pane-id>
   ```
4. Verify no orphan agent processes remain:
   ```bash
   ps aux | grep "claude" | grep -v grep | grep -i "<teammate-name>"
   ```
   If any found, kill them: `kill <pid>`
5. Completed teammates must be fully shut down before moving on. Lingering teammates consume tmux panes, clutter the Guardian's monitoring surface, and create ambiguity about who is still working.
6. Mark all teammates' tasks completed via TaskUpdate
7. **Update the plan** — dispatch the plan-editing subagent to mark the task `[x]`, advance the freeze point, and resolve any gaps
8. Merge all worktrees for this task to the main branch:
   ```bash
   git merge --no-ff <worktree-branch-1> <worktree-branch-2> ...
   ```
9. Proceed to the next task (audit → spawn → ...)
