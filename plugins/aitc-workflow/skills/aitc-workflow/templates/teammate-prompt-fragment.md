# Teammate Prompt — Mandatory Fragment

Copy this verbatim into EVERY teammate prompt, as Part D after the phase requirements.

---

DISCOVERY REPORTING AND TASK SKILL CREATION:

After each phase, you MUST include a section in your completion message:

  ## Discoveries
  - New: <any operation where existing skill was wrong/missing/incomplete.
    Describe what you expected, what actually happened, and what you did.
    If this knowledge is reusable → CREATE a task SKILL file in
    skills/aitc-task-<batch>/ following the format of existing
    task SKILLs listed in your prompt. Report: "Created task SKILL <name>">
  - Supplement: <any correction to project skill instructions. Include the
    skill name, the specific issue, and the corrected approach.
    If this supplements an existing project skill → CREATE a supplement
    task SKILL.>
  - Self-Maintenance: <if you loaded a task SKILL and found an inconsistency,
    you MUST edit that SKILL file directly to correct it. Report what you
    changed.>
  - None: <only if you genuinely discovered nothing new in this phase>

If you encounter an error or unexpected behavior, do NOT silently work around
it and continue. Create a task SKILL or edit the existing one. Report it as
a Discovery even if you resolved it yourself.

TASK SKILLS YOU CREATE go in skills/aitc-task-<batch>/ in your
worktree. They will be merged to the main branch when your work is complete.
Follow the format of existing task SKILLs — they are your templates.

If "None" is reported but verification finds an unreported issue or a
missing task SKILL, that counts as a FAIL.
