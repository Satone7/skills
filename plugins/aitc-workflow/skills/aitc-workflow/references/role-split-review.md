# ROLE-SPLIT — Gated Review

ROLE-SPLIT is a **restricted pattern**. It creates teammates that must coordinate via SendMessage, introduces handoff gaps between roles, and adds verification complexity. It should only be used when top-level plan splitting is genuinely insufficient.

## Gate: Independent Review Subagent

When the audit subagent sets the ROLE-SPLIT flag, dispatch a **second, independent subagent** to validate the necessity. This subagent must have no prior exposure to the task — it provides a cold-eyed assessment:

```
Agent(
    description="Review ROLE-SPLIT necessity for task <task-name>",
    subagent_type="general-purpose",
    model="opus",
    mode="default",
    prompt="""
    An audit of task "<task-name>" flagged it as a potential candidate
    for ROLE-SPLIT (multiple teammates collaborating on one task).

    Your job: independently validate whether ROLE-SPLIT is truly
    necessary, or whether top-level plan splitting is sufficient.

    READ:
    1. The audit subagent's report (especially the ROLE-SPLIT flag
       evidence)
    2. The task description and phases in docs/plans/<batch>.md
    3. All task SKILLs and discovery hints in skills/aitc-task-<batch>/
    4. Outputs from preceding completed tasks

    VALIDATE EACH CONDITION independently:

    1. NON-DECOMPOSABLE?
       Can the task be broken into sequential independent sub-tasks?
       - If YES → REJECT ROLE-SPLIT. Recommend emergent tasks instead.
       - If NO → explain why decomposition fails (what makes the phases
         inseparable?)

    2. BIDIRECTIONAL DEPENDENCY?
       Is there concrete evidence that roles would need live iteration?
       - Look for: discovery hints showing handoff failures, task SKILLs
         documenting integration issues, preceding task outputs with
         cross-cutting concerns
       - If evidence is only speculative ("might need iteration") →
         REJECT. Require demonstrated need, not hypothetical.

    3. CONTEXT VOLUME?
       Would a single context window plausibly overflow?
       - Estimate: number of codebases, log volume, reference docs
       - If under ~80% of a typical context budget → REJECT.
         Single-agent context is large; "this feels big" is not evidence.

    REPORT:
    - Verdict: APPROVE or REJECT ROLE-SPLIT
    - For each condition: MET / NOT MET with reasoning
    - If APPROVE: recommended role breakdown with specific scope per role,
      convergence criteria (when does iteration stop?), and model per role
    - If REJECT: concrete alternative — either "single teammate suffices"
      or "decompose into these N emergent plan tasks"

    DEFAULT VERDICT: REJECT. Override only when all three conditions
    are independently confirmed with concrete evidence.
    """
)
```

## Lead Decision

- **Review APPROVES** → use the recommended role breakdown. Spawn role-teammates in dependency order. Document the decision and evidence in the plan's Amendments section.
- **Review REJECTS** → follow the review's alternative recommendation (single teammate or emergent tasks). Do not override a rejection — if two independent subagents disagree, neither has a strong enough case.
- **Review is ambiguous** (approves with weak evidence) → default to REJECT. Weak evidence is weak ROLE-SPLIT.

## Why This Gate Exists

ROLE-SPLIT is irreversible — once you spawn multiple teammates for one task, you've committed to coordinating them. Emergent tasks are reversible — you can always split further later. The gate prevents premature commitment to a coordination-heavy pattern when a simpler decomposition would work.
