# Teammate Prompt — Mandatory Fragment

Copy this verbatim into EVERY teammate prompt, as Part D after the phase requirements.

---

DISCOVERY REPORTING AND TASK SKILL CREATION:

This is a HARD GATE. You will not pass verification unless you follow these rules.

## Rule 1 — Capture in Real-Time

When you discover something — a wrong assumption, a missing step, a workaround that worked, a concrete value (IP, flag, path) that future teammates will need — invoke IMMEDIATELY:

  Skill("task-skills-creator")

Do NOT wait until your work is done. Do NOT plan to "report it later." Context compression erases details within a few turns. Capture the moment you discover.

The skill spawns a forked subagent that handles file creation/editing. You just describe what you found. Your context stays clean.

## Rule 2 — Report in Discoveries

After each phase, include in your completion message:

  ## Discoveries
  - Created task SKILL: <name> — <one-line summary> (invoked task-skills-creator)
  - Self-Maintenance: <if you loaded a task SKILL and found an inconsistency,
    you must edit that SKILL file directly. Report what you changed.>
  - None: <only if you genuinely discovered nothing new in this phase>

## Rule 3 — Verification Cross-Check

The verification subagent will cross-check your reported Discoveries against the task SKILL directory. If you report a discovery but no corresponding file exists → FAIL. If the execution log shows error-recovery patterns you didn't report → FAIL.

If you encounter an error or unexpected behavior, do NOT silently work around it. Invoke task-skills-creator immediately. Report it even if you resolved it yourself.

TASK SKILLS YOU CREATE go in skills/aitc-task-<batch>/ in your worktree.
They will be merged to the main branch when your work is complete.
