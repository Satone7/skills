# Pre-Execution Task Audit

The initial plan's complexity estimate is a guess made with incomplete information. Before executing each task, re-assess it against current reality: accumulated task SKILLs, discovery hints from preceding tasks, and outputs that may reveal hidden complexity.

**Default strategy: top-level plan splitting.** When a task turns out to be more complex than estimated, decompose it into independent emergent tasks in the plan, each assigned to a single teammate. This keeps context boundaries clean and task ownership unambiguous. ROLE-SPLIT (multiple teammates collaborating on one task) is a special-case fallback that requires independent justification — see `role-split-review.md`.

## When to Audit

Audit every task before spawning its teammate(s). The cost of the audit is small; the cost of assigning a complex task to a single overloaded teammate — or discovering mid-execution that the task is twice the expected scope — is large.

## Audit Subagent Prompt

Dispatch a **standalone subagent** (no `team_name` — the audit is read-only analysis, not team work):

```
Agent(
    description="Audit task <task-name> before execution",
    subagent_type="general-purpose",
    model="opus",
    mode="default",
    prompt="""
    Audit task "<task-name>" before execution. Your job is to reassess
    complexity against current reality, not the initial plan.

    READ:
    1. The task description and phases in docs/plans/<batch>.md
    2. All task SKILLs in skills/aitc-task-<batch>/
    3. skills/aitc-task-<batch>/.discovery-hints.md
    4. Outputs from preceding completed tasks (merged to main branch)

    REPORT:

    A. COMPLEXITY REASSESSMENT
    - Original estimate: <from plan>
    - Current assessment: simple | moderate | complex | critical
    - Rationale: <what changed, what was underestimated>

    B. EMERGENT TASKS (primary mechanism for handling complexity)
    New tasks discovered from accumulated knowledge that are NOT in
    the current plan. For each:
    - Task name and description
    - Why it emerged (which discovery or output revealed it)
    - Estimated complexity and model recommendation
    - Whether it BLOCKS the current task or can run in parallel
    - Whether it should absorb the current task (if the discovery
      fundamentally changes what needs to be done)

    If the task is more complex than estimated, PREFER decomposing it
    into emergent tasks rather than recommending ROLE-SPLIT. Emergent
    tasks keep context boundaries clean — each teammate owns a complete,
    verifiable deliverable.

    C. ROLE-SPLIT FLAG (only if you see strong evidence)
    Set this flag ONLY if ALL of the following are true:
    1. The task CANNOT be meaningfully decomposed into sequential
       independent sub-tasks (the phases are tightly coupled)
    2. There is evidence of bidirectional dependency between roles
       (not just speculation — the discovery hints or task SKILLs
       must show that handoff gaps are likely without live iteration)
    3. The task's context volume plausibly exceeds a single context
       window (e.g., multiple large codebases, extensive logs)

    If the flag is set, briefly state which conditions were met and
    what evidence supports them. Do NOT recommend a specific role
    breakdown — that belongs to a separate review (§2.0.1).

    DEFAULT: single teammate for the task as currently scoped in the plan.
    """
)
```

Use `opus` for audits — misjudging complexity causes cascading failures downstream.

## Processing Audit Results

**Task is simple/moderate → single teammate:**
Proceed to prompt assembly with the original task scope.

**Emergent tasks discovered:**
1. Classify each:
   - **Blocker** — must be done before the current task can proceed
   - **Parallel** — can run alongside the current task
   - **Absorbing** — fundamentally changes the current task's scope; the original task should be redefined
2. Dispatch the plan-editing subagent to insert emergent tasks into the plan. Provide: task name, scope, blocker/parallel/absorbing classification, and the current freeze point.
3. Re-rank priorities: an emergent blocker jumps ahead of non-blocked tasks
4. For absorbing tasks: the subagent updates the original task description to reflect the new scope
5. If the emergent task fundamentally changes the work's direction, pause and inform the user before proceeding
6. Create corresponding task SKILL(s) to capture what triggered the emergent task
7. The original task and emergent tasks each get a single teammate

**Audit raised the ROLE-SPLIT flag:**
Do not act on it immediately. Instead, dispatch an independent review subagent (`role-split-review.md`) to validate whether ROLE-SPLIT is truly necessary. The audit's flag is a signal for further investigation, not a decision.

Emergent tasks are normal — they are not plan failures. The initial plan is a best-guess with incomplete information. Discovering new work is evidence that the audit is functioning correctly.
