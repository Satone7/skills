---
name: "task-checker"
description: "Strictly audits a writing-plans-plus JSON plan for per-task completion, description accuracy, and test adequacy (ignore CI). Use whenever user asks to audit a plan, validate acceptance criteria, or request gap analysis and minimal test additions."
---

# Task Checker

## Goal

Turn “is this plan task actually done?” into a reviewable evidence chain:

- Per-task verification: confirm goals/acceptance criteria/deliverables exist in code and observable behavior
- Per-task drift detection: confirm the task description still matches the implementation (stale / diverged / re-scoped)
- Per-task test review: assess whether tests cover key success paths and failure/edge cases; propose minimal additions

## Hard Rules (No False Positives)

These rules exist to prevent “looks done” audits that miss real gaps.

### 1) No fabricated or “hand-wavy” evidence

Disallowed evidence patterns (treat as a GAP):

- “Implicitly tested via integration” without a concrete test file + assertion that exercises the exact acceptance point
- “Build succeeds” / “tests pass” without actually running a command and recording its output (or finding a committed log with the exact output)
- “Git evidence shows…” unless you actually ran git commands and cited concrete commits/changes (do not assume history)
- Linking to a directory or repo root as evidence; evidence must point to a file and (usually) a line range
- “Task marked complete / passes:true in plan” as evidence; plan metadata is not implementation proof

### 2) Completion requires closure of acceptance points

- If any acceptance point lacks strong evidence, the task cannot be “Completed”.
- If an acceptance point is not verifiable as written, mark “Mis-specified” and list what must change in the plan to make it auditable.

### 3) Intermediate tasks are not “Completed” when superseded

If the plan has an explicit intermediate step (e.g., “hardcode X as a bridge”), and the codebase no longer contains that intermediate behavior:

- Mark completion as “Not Done (superseded)” and description accuracy as “Drifted”.
- Explain what replaced it and propose a plan revision (split/merge/retire the intermediate task).

### 4) Disabled tests never count as passing evidence

- DISABLED tests are always a gap, not coverage.
- If the only test coverage for a criterion is DISABLED (or “no crash”), the task cannot be “Completed”.

### 5) TODO/stub detectors gate completion

If the relevant code contains TODOs/stubs that directly relate to the task’s promised semantics (e.g., “Parse CONNECTIONS”):

- You must call it out as a gap.
- If the task’s acceptance points imply those semantics exist, the task is at most “Partial”.

## Preconditions (must hold)

- The project provides a JSON plan that follows the `writing-plans-plus` schema (“plan file”)
  - At minimum: plan metadata + a tasks list
  - Each task includes: id, title, description (or equivalent), and at least one acceptance/done criteria field (e.g., acceptance_criteria / validation_criteria / done_definition)

If the plan does not meet the minimum structure: do not guess. Output a “plan-structure gap list” and require the missing fields before auditing.

## Inputs

User should provide:

- Plan file path (required)
- Audit scope (optional):
  - all tasks (default)
  - specific task ids (e.g., [1,2,5])
- Audit depth (optional):
  - static evidence only (default): code/tests/docs/scripts
  - include local dynamic verification: run minimal necessary tests locally (ignore CI)

## Core Method (follow this order)

### 1) Read and “structure” the plan

1. Read the plan file and extract:
   - plan goal/scope/assumptions (goal/description/architecture/depends_on, etc.)
   - task list: id/title/description/steps/criteria/deliverables/dependencies
2. Convert each task into an audit checklist:
   - intent: what behavior/artifact must change
   - deliverables: which files/modules/interfaces should exist or change
   - acceptance points: which observable facts must hold (build success is not completion)
3. Record plan risk signals:
   - acceptance criteria based on log strings/output text
   - mandatory “temporary hardcode/intermediate stage” steps likely to be skipped later
   - missing or non-verifiable criteria (e.g., “looks better”)
4. Treat any “passes: true” fields as plan bookkeeping only; they are not evidence.

### 2) Build an evidence model per task

For each task, attempt to collect at least these evidence types:

- code evidence: where implemented, where invoked, whether it is reachable
- test evidence: which tests cover it, whether assertions are meaningful
- runtime evidence: reproducible commands/scripts/test cases that validate key paths
- doc/plan consistency evidence: whether README/guide/plan notes match implementation

Map each acceptance point to one or more evidence items, producing an “acceptance → evidence” table.

### 2.1 Evidence strength grading (use consistently)

Grade each acceptance point’s evidence:

- Strong: direct code evidence + a test with meaningful assertions OR runtime check with machine-checkable outputs
- Medium: direct code evidence + indirect validation (runtime log excerpt only, or a test that only partially asserts)
- Weak: code exists but no proof it is correct/reachable/covered
- None: no evidence

Task completion gates:

- Completed: all acceptance points are Strong (or a clearly justified mix of Strong + at most one Medium) AND no hard-rule violations
- Partial: at least one acceptance point is Medium/Weak/None, or there is a TODO/stub gap, or coverage is Borderline/Inadequate
- Not Done: core deliverables missing, acceptance contradicted, unreachable code, or intermediate task has been removed without plan update

### 3) Gather and validate evidence (do not stop at “found a file”)

#### 3.1 Code evidence

1. Prefer semantic search to locate implementation entry points:
   - class/function definitions
   - key fields/config/CLI flags
   - files mentioned by the plan (if any)
2. For each acceptance point, confirm at least:
   - implementation truly exists (not a stub, not TODO-only, not “return true”)
   - there is an invocation path (main flow can actually reach it)
   - behavior matches the task description (e.g., “parse CONNECTIONS” really builds connectivity)
   - if the criterion is a log/output string, require BOTH:
     - code evidence that prints/emits the exact string, AND
     - runtime evidence (or a test assertion) that the string actually appears
3. Produce evidence links:
   - always provide navigable file links with line ranges (file:///...#Lx-Ly)

#### 3.2 Test evidence

1. Search tests related to the task:
   - unit tests (same module/function)
   - integration tests (end-to-end / main flow)
2. Decide whether the tests are “countable” evidence:
   - tests that only do SUCCEED() / “no crash” are not semantic completion evidence
   - DISABLED tests (external env dependent) are coverage gaps, not coverage
   - scripts without assertions or machine-checkable outputs are not sufficient validation
3. Coverage assessment (answer at least):
   - success path: typical valid inputs produce expected artifacts/state
   - failure path: invalid/missing fields/boundaries are rejected or degraded properly
   - regression risk: plan-stated compatibility points are pinned by tests (format/interface/output)

#### 3.3 Dynamic verification (optional but strongly recommended)

If the project supports local test execution:

1. Prefer the minimal set:
   - project-native test commands (pick the smallest relevant subset)
   - examples: `pytest -q`, `npm test`, `go test ./...`, `cargo test`, `ctest --output-on-failure`
2. If the plan uses “manual command verification”, collapse it into repeatable checks:
   - e.g., run command + check key output + verify artifact files exist
3. Record an “executed checks list”:
   - commands run
   - key outputs / exit codes
   - which task acceptance point each check supports

#### 3.4 Data-shape validation (required for data-driven parsers)

If tasks involve parsing/loading structured inputs (JSON/XML/IR/etc.):

1. Locate the canonical sample inputs in-repo referenced by docs/benchmarks/tests.
2. Compare the sample’s shape with the parser’s branching logic (arrays vs objects, field names, nesting).
3. If there is a shape mismatch that would drop data silently (e.g., ignoring non-PATTERN entries in an array), it is a high-risk gap and blocks “Completed”.

### 4) Decide completion per task (strict, explainable, reviewable)

Assign one of these statuses per task:

- Completed: every acceptance point has strong evidence; tests cover key success + main failure/edge cases; no obvious TODO/stub/bypass implementation
- Partial: some points met, but key gaps exist (e.g., connectivity not built, skeleton-only, tests disabled)
- Not Done: core deliverables or acceptance points missing, or implementation clearly contradicts the description

Also evaluate “task description accuracy”:

- Accurate: description matches implementation
- Drifted: implementation changed but plan/docs still reflect an older state (common around “stub/hardcode” phases)
- Mis-specified: the plan is not reasonable or not verifiable (e.g., acceptance based on log strings)

### 5) Rate test adequacy and propose minimal additions

For each task, rate tests (Adequate / Borderline / Inadequate) and output a “minimal test additions list”:

- specify test intent (which acceptance point / failure path)
- specify suggested location (reuse existing test framework and directories)
- specify assertion type (state/artifact/structure/behavior), avoid “no crash only”

## Output Format (must follow)

### A. Overview

- Plan file: <path>
- Audit scope: all tasks / task ids [...]
- Overall verdict: Completed / Partial / Not Done (1–2 evidence-based sentences)
- Executed checks: list commands actually run (or “None”)
- High-risk gaps (3–6 bullets): only issues that cause false “done” conclusions

### B. Per-task Audit Table

For each task, output:

- Task <id> <title>
  - Completion: Completed / Partial / Not Done
  - Description accuracy: Accurate / Drifted / Mis-specified
  - Acceptance → evidence mapping:
    - <criterion> → evidence grade (Strong/Medium/Weak/None) → code evidence (link) → test evidence (link) → runtime evidence (if any)
  - Gaps:
    - missing implementation / missing invocation path / missing connectivity semantics / missing tests / tests without assertions / disabled tests, etc.
  - Minimal test additions (max 3, priority-ordered)

### C. Plan Revision Suggestions (optional)

Only output if clear plan drift/mismatch is found:

- which tasks/milestones should be updated or split
- which acceptance criteria should be converted from “soft signals” to “hard evidence”

### D. Apply Revisions to Plan JSON (only when user explicitly requests it)

If the user instructs you to update the plan JSON file based on your audit, you must:

0. **Separate audit vs patch:** keep your audit verdicts (Completed/Partial/Not Done, superseded, drifted) in the audit report. Do NOT serialize audit-only concepts into the plan JSON via new fields.
1. **Update only the existing plan JSON file** at the provided path (no new fields, no new formats).
2. **Strictly follow the `writing-plans-plus` schema** for all edits:
   - Do NOT introduce any field names outside the schema (no audit-only metadata like `status`, `gaps`, `risk`, `review`, etc.).
   - Allowed task fields are limited to: `id`, `title`, `description`, `steps`, `passes`, `files`, `depends_on`, `validation_criteria`, `skills`, `issue`, `completed_at`, `completed_by`, `notes`.
3. **When downgrading completion:** if a task currently has `passes: true` but your audit concludes it is not actually complete (Partial / Not Done), then:
   - Set `passes: false`
   - Add `issue`: a **non-empty** array of strings describing the concrete problems you found
   - Do NOT use `notes` to describe issues (issues belong in `issue`)
   - Preserve any existing completion metadata (`completed_at`, `completed_by`, and prior completion `notes`) for audit trail
4. **When fixing plan drift/mis-specification:** update only schema fields to make the task auditable:
   - tighten `description` and `steps` so they reflect current intended behavior
   - convert vague acceptance points into verifiable `validation_criteria`
   - update `files` lists only if they are materially wrong or missing key deliverables
5. **Issue/passes invariants (must hold after edits):**
   - If `issue` is present, `passes` MUST be `false`
   - If `passes` is `true`, `issue` MUST NOT be present
6. **Superseded/partial handling:** represent “superseded” or “partial” only using schema fields:
   - Set `passes: false`
   - Put the concrete reasons in `issue`
   - If helpful, annotate `title`/`description` text, but do NOT add new fields
7. **Pre-save self-check (required):** before saving the updated plan JSON:
   - remove any non-schema fields you accidentally added
   - verify there is no task with `issue` + `passes: true`
   - verify there is no task with `passes: true` + `issue`
8. **If the plan update requires restructuring (split/merge tasks):** only do this when the user explicitly requests it, and ensure any new tasks use only schema fields and default `passes: false`.

## Notes (common sources of false positives)

- “Builds / returns true / prints logs” is not completion: verify core semantics (e.g., real connectivity graph built)
- DISABLED tests or SUCCEED()-only tests are coverage gaps, not coverage
- Scripts that run without assertions or stable output checks are not sufficient validation
- If intermediate phases (e.g., hardcoding) are skipped during evolution, mark as Drifted and recommend plan updates

## Audit Self-Check (before finalizing)

If you wrote any of the following, you must replace it with concrete evidence or mark a gap:

- “implicit / likely / probably / should be” (without evidence)
- “Build succeeds” (without executed command output)
- “Test passes” (without citing an actual test + assertion, or test output)
- “Verified via integration” (without pointing to the integration test code or runtime log)
- “Git shows” (without commands and concrete results)
