# Error Recovery

Long-running tasks encounter failures. These procedures handle common cases without losing progress.

## Teammate Becomes Unresponsive

If a teammate's tmux pane shows no activity for an extended period (significantly beyond the task's estimated duration):

1. Check if the spinner is still animating (active work) vs frozen (stuck)
2. If frozen: send Ctrl-C via tmux, then diagnose via SendMessage
3. If the teammate doesn't respond to SendMessage within a reasonable time:
   - The agent process may have died; check `ps aux | grep agent`
   - Re-spawn the teammate with the same prompt; it will pick up from where it left off (worktree state is preserved)
   - Log the incident in the plan's execution log

## Lead Session Restart

If the Lead's session terminates and later restarts (power loss, crash, network drop):

1. The worktrees persist on disk — no work is lost
2. The Guardian cron is session-only (durable=false) and dies with the session
3. Recovery steps:
   - Check `git worktree list` to identify active worktrees
   - Read the Guardian log at `docs/plans/guardian-log-<batch>.md` for last-known state
   - Re-create the team: `TeamCreate(team_name="<name>")`
   - Re-spawn Guardian with the same parameters
   - Resume from the last completed teammate (check which worktrees have been merged)
   - The `skills/aitc-task-<batch>/.discovery-hints.md` and task SKILLs on disk are intact

## TeamCreate Failure

If TeamCreate returns an error (team name conflict from a prior run):

1. Check if the team still has active members: read `~/.claude/teams/<name>/config.json`
2. If all members are dead/defunct, delete the team: `TeamDelete`
3. Re-create with the same name
4. If members are still active, use a suffixed name: `<name>-v2`

## Merge Conflict During Worktree Merge

1. Conflicts should be rare (each teammate writes to isolated paths)
2. If a conflict occurs: resolve manually — teammate outputs (reports, patches) take priority
3. If in doubt, keep both versions and note in the plan log

## Guardian Cron Expiry

Recurring cron jobs auto-expire after 7 days (session lifetime bound). For tasks longer than 7 days:
- Set `durable: true` when creating the Guardian cron (if supported)
- Or re-create the Guardian cron at day 6

## Lead Edited Plan Directly

If the Lead edited the plan directly (violating the Plan Editing Boundary rule):

1. **Stop.** Do not continue orchestration. The plan file may now violate the frozen prefix constraint or have uncommitted changes.
2. Run `git diff docs/plans/<batch>.md` to see what was changed.
3. If the change was correct (e.g., marking a task `[x]`) but done through the wrong channel:
   - Commit the change: `git add docs/plans/<batch>.md && git commit -m "chore(plan): <what was changed>"`
   - The edit is accepted — the problem is the channel, not the content
4. If the change introduced errors (wrong marker, wrong task, frozen prefix violation):
   - Revert: `git checkout docs/plans/<batch>.md`
   - Re-dispatch the correct edit through the plan-editing subagent using the template in §Plan Editing Boundary
5. **Root cause**: The Lead edited directly because spawning a subagent felt heavier than the edit. But the subagent template in §Plan Editing Boundary is copy-pasteable — use it. The subagent also runs the dirty check and enforces the frozen prefix constraint, which direct edits skip.

## Verification Loop Exhaustion

If a teammate fails verification 3 times (the rework limit):

1. Do not shut down the teammate — instead, read their worktree to understand what state it's in
2. Classify each failure as critical (missing or incorrect deliverable) or cosmetic (formatting, naming)
3. Fix critical issues directly in the worktree (the Lead has filesystem access)
4. Document any cosmetic issues that will be accepted as-is in the plan's execution log
5. Run a final verification subagent on the repaired worktree
6. If it still fails, choose one of these paths:
   - **Accept with known issues**: if failures are minor and don't affect conclusions, document them and proceed
   - **Re-assign**: abandon the task, refine the teammate prompt based on what was learned, and spawn a new teammate to redo it
   - **Escalate**: present the situation to the user for a decision
7. Record the outcome and reasoning in the plan's execution log — this is valuable data for improving future plans
