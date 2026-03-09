---
name: "task-checker"
description: "Strictly audits a writing-plans-plus JSON plan for per-task completion, description accuracy, and test adequacy (ignore CI). Use whenever user asks to audit a plan, validate acceptance criteria, or request gap analysis and minimal test additions."
compatibility: "Requires: read a writing-plans-plus plan JSON; search code/tests to produce evidence links. Optional: run minimal local verification commands (ignore CI)."
---

# Task Checker

## Goal

Turn “is this plan task actually done?” into a reviewable evidence chain:

- Per-task verification: confirm goals/acceptance criteria/deliverables exist in code and observable behavior
- Per-task drift detection: confirm the task description still matches the implementation (stale / diverged / re-scoped)
- Per-task test review: assess whether tests cover key success paths and failure/edge cases; propose minimal additions

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

### 2) Build an evidence model per task

For each task, attempt to collect at least these evidence types:

- code evidence: where implemented, where invoked, whether it is reachable
- test evidence: which tests cover it, whether assertions are meaningful
- runtime evidence: reproducible commands/scripts/test cases that validate key paths
- doc/plan consistency evidence: whether README/guide/plan notes match implementation

Map each acceptance point to one or more evidence items, producing an “acceptance → evidence” table.

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
- High-risk gaps (3–6 bullets): only issues that cause false “done” conclusions

### B. Per-task Audit Table

For each task, output:

- Task <id> <title>
  - Completion: Completed / Partial / Not Done
  - Description accuracy: Accurate / Drifted / Mis-specified
  - Acceptance → evidence mapping:
    - <criterion> → code evidence (link) → test evidence (link) → runtime evidence (if any)
  - Gaps:
    - missing implementation / missing invocation path / missing connectivity semantics / missing tests / tests without assertions / disabled tests, etc.
  - Minimal test additions (max 3, priority-ordered)

### C. Plan Revision Suggestions (optional)

Only output if clear plan drift/mismatch is found:

- which tasks/milestones should be updated or split
- which acceptance criteria should be converted from “soft signals” to “hard evidence”

## Notes (common sources of false positives)

- “Builds / returns true / prints logs” is not completion: verify core semantics (e.g., real connectivity graph built)
- DISABLED tests or SUCCEED()-only tests are coverage gaps, not coverage
- Scripts that run without assertions or stable output checks are not sufficient validation
- If intermediate phases (e.g., hardcoding) are skipped during evolution, mark as Drifted and recommend plan updates
