---
name: aitc-workflow
version: 2.0.0
description: >
  Manually invoked — NOT auto-triggered. Multi-agent workflow orchestrator for long-running tasks.
  This is a redirector: it guides the user to one of three specialized SKILLs depending on where
  they are in the workflow. Plan → Execute → Lifecycle.
---

# AITC Workflow — Redirector

This is the entry point for the AITC workflow. Determine where the user is and route to the appropriate SKILL:

| User says | Route to |
|-----------|----------|
| "create a plan", "plan this task", new task with no plan file | Invoke `aitc-workflow-plan` |
| "execute the plan", "run batch", "start", existing plan file | Invoke `aitc-workflow-execute` |
| "wrap up", "archive", "promote", all tasks done | Invoke `aitc-workflow-lifecycle` |

Each SKILL is manually invoked and explicitly chains to the next at completion.

## Workflow Chain

```
aitc-workflow-plan  ──▶  aitc-workflow-execute  ──▶  aitc-workflow-lifecycle
    (Plan mode)             (Execute mode)              (Lifecycle mode)
```

Start with `aitc-workflow-plan` if no plan file exists. Each SKILL will tell the user what to invoke next.
