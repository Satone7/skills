# Prompt Assembly

Every teammate prompt is assembled from the following parts, in order. For the rare case where ROLE-SPLIT was approved, use the role-specific variants in Part A and Part C.

## Part A — Role Declaration

The `MODEL:` line in the prompt body is informational only — it tells the teammate what model it is running on, but does not control the actual model. The model is set by the `model=` parameter in the `Agent()` call. Both must agree: if `Agent(model="sonnet")` writes `MODEL: opus`, the teammate works with a false self-perception that can distort its judgment.

**Single-teammate:**
```
You are the <task-name> worker in the <team-name> team.
Your task: Execute the full pipeline for <task-description>.
TARGET DIRECTORY: <path>
MODEL: <model>
MODE: auto
```

**Role-split (one teammate per role):**
```
You are the <role-name> for task <task-name> in the <team-name> team.
Your role: <role-description — what this role is responsible for>.
Your scope is LIMITED TO: <specific phases this role handles>.
You depend on: <preceding role outputs, if any>.
Other roles on this task: <list other roles and what they handle>.
TARGET DIRECTORY: <path>
MODEL: <model>
MODE: auto
```

The role-split declaration gives each teammate clear boundaries — they know exactly what they own and what they don't, and who to wait for before starting.

## Part B — Context

Dynamically populated based on execution order:

```
You are the <Nth> active teammate. Previous teammates (<list>) have
completed and their code is merged to the main branch. Reference their
output in <report-paths>.
```

This gives each teammate awareness of what came before, enabling cross-referencing without the Lead having to manually relay findings.

## Part C — Phase Requirements

Each phase with specific instructions and skill references. Extract verbatim from the plan's task description section.

## Part D — Discovery Reporting Mandate

Include verbatim in every teammate prompt. Read `templates/teammate-prompt-fragment.md` and copy its full content as Part D. The template contains the mandatory discovery reporting format.

Discoveries are the raw material for task SKILLs. If teammates silently fix issues, that knowledge is lost forever when the teammate exits. The verification step cross-checks reported discoveries against execution logs to catch omissions.

## Part E — Task SKILL Discovery

Include verbatim in every teammate prompt:

```
TASK SKILL DISCOVERY:
Invoke the find-task-skills skill at the start of your work. It will guide
you to discover and load relevant task SKILLs from skills/aitc-task-<batch>/.

Do NOT rely on the Lead to list available task SKILLs — you are responsible
for finding the ones relevant to your task. The task SKILL directory is:
skills/aitc-task-<batch>/
```

The `find-task-skills` skill handles listing, relevance judgment, loading, and self-maintenance. The Lead no longer manually populates this section — the teammate discovers task SKILLs independently.
