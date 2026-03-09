---
name: executing-single-task
description: Execute exactly one writing-plans-plus task from find-next-task output in a low-context subagent, then update the plan JSON (passes only) and create exactly one git commit for that task. Use this whenever you are asked to run “the next task” or “a single task” and write back passes.
---

# Executing Single Task

## Overview

This skill is the execution counterpart to `find-next-task`. It takes a single task (via the full `find-next-task` output JSON), executes it with minimal context, verifies results with evidence, updates the plan JSON by setting only `passes`, and commits once.

## Input

## Output

## Workflow

