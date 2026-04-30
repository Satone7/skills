# Plan Template

Copy this skeleton when generating a plan file. Replace `<placeholders>` with concrete values.

```markdown
# <Work Name> — Execution Plan

**Date**: <YYYY-MM-DD> | **Team**: <team-name> | **Freeze point**: (none yet)

## Team Structure

**Teammate** (has `team_name`, joins team, reachable via SendMessage):
```
Agent(
    team_name="<team-name>",
    name="<name>",
    subagent_type="general-purpose",
    model="<sonnet-or-opus>",
    mode="auto",
    run_in_background=True,
    prompt="""..."""
)
```

**Subagent** (no `team_name`, standalone, fire-and-forget):
```
Agent(
    description="<purpose>",
    subagent_type="general-purpose",
    model="<sonnet-or-opus>",
    mode="default",
    prompt="""..."""
)
```

Do NOT use `isolation="worktree"` — the Lead creates worktrees manually.
Model must be `sonnet` or `opus` for workers, `haiku` for Guardian.

## Tasks

| # | Status | Teammate | Scope | Model | Priority |
|---|--------|----------|-------|-------|----------|
| 1 | [ ] | <name> | <scope> | sonnet | high |
| 2 | [ ] | <name> | <scope> | sonnet | medium |

Status markers: `[ ]` pending | `[>]` in-progress | `[x]` completed | `[~]` re-planned | `[-]` abandoned

### [ ] Task 1: <name>

**Scope**: <what this teammate is responsible for>

**Phases**:
1. <phase>: <description>
2. <phase>: <description>

**References**: <files, reports, skills to consult>

### [ ] Task 2: <name>

**Scope**: <what this teammate is responsible for>

**Phases**:
1. <phase>: <description>

**References**: <files, reports, skills to consult>

## Execution Strategy

- **Order**: serial (tasks run sequentially, each depends on preceding output)
- **Pre-requisites**: <models to pre-download, artifacts to pre-export>
- **Isolation**: each teammate in independent worktree under /tmp/worktrees/<team>-<task>/

## Acceptance Criteria

### Per-Task
- [ ] Task 1: <concrete deliverable, e.g., "profiling report at reports/perf.md">
- [ ] Task 2: <concrete deliverable>

### Cross-Task
- [ ] <criterion spanning multiple tasks, e.g., "all outputs integrated into final report">

## Amendments

(Empty initially — populated during execution by plan-editing subagent)

## Risk & Timeline

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| <risk description> | low/medium/high | <mitigation> |

| Task | Estimate | Model |
|------|----------|-------|
| 1. <name> | <duration> | sonnet |
| 2. <name> | <duration> | sonnet |
```
