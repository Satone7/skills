---
name: executing-single-task
description: 执行 writing-plans-plus 计划中的“恰好一个任务”：输入为 find-next-task 的完整输出 JSON。严格按四阶段流程（实现→规范审查→质量审查→最终验证），基于证据更新 plan JSON 的 passes（成功时删除 issue 字段；失败时写入/更新非空 issue[]），并创建且仅创建一个 git commit。凡用户要求“执行下一个任务/只跑一个任务/把 passes 写回/自动执行单任务”都应优先使用本技能。
---

# Executing Single Task

## Overview

这是 `find-next-task` 的执行配套技能。它把“脚本化单任务执行协议”固化为可重复、可审计的流程：一次只处理一个 task，拆分为 4 个阶段（实现、规范审查、质量审查、最终验证），并将验证结果写回计划文件。

**开始时必须宣布：**“我正在使用 executing-single-task 来执行恰好一个任务，并按证据写回 passes/issue 与一次提交。”

## Compatibility & Fallback

默认假设当前环境具备：
- 可创建 subagent（用于 Implementer / Spec Reviewer / Code Quality Reviewer）
- 可运行验证命令（测试/构建/静态检查等，取决于 task）
- 可写入 `plan_file` 且可创建 git commit

如果无法创建 subagent（能力缺失或被明确禁止），则必须在同一会话中“角色化分段”完成四阶段：
- 先以 Implementer 视角完成实现并停下
- 再以 Spec Reviewer 视角仅做合规审查并停下
- 再以 Code Quality Reviewer 视角仅做质量审查并停下
- 最后以主 Agent 执行验证与写回/提交

## Required First Step

在任何响应或动作之前，先调用 `using-superpowers`。如果它指出任何可能相关的技能（哪怕只有 1% 可能），先加载再继续。

## Input

输入为 `find-next-task` 的完整输出 JSON（逐字粘贴，不要改写）。`plan_file` 是唯一真相来源。

**Fail-fast conditions (no file changes):**
- `error != null`
- `selection_required == true`
- `next_task == null`
- `plan_file` missing or not an absolute path
- `next_task.id` missing

额外 fail-fast（无文件改动）：
- `plan_file` 不存在或无法读取/解析
- 计划中找不到 `id == next_task.id` 的任务

## 执行模式约定（重要）

如果上游脚本或用户明确表示“全托管 / 自动循环 / 禁止提问”，则：
- 禁止向用户提问澄清（不得使用 AskUserQuestion）
- 必须自行通过阅读现有代码、任务描述与验收标准做出决策并推进
- 不确定时优先选择最小改动、可验证、可回滚的实现

## Output

输出必须为可读报告（允许 markdown 标题/列表），并严格使用以下结构（顺序固定，字段齐全）。

## Report Structure

始终按此模板输出：

### 1) Task Identity

- plan_file: ...
- task_id: ...
- title: ...

### 2) Execution Summary

- result: SUCCESS | FAIL | BLOCKED
- what_changed: ...
- files_touched: ...

### 3) Verification Evidence

逐条列出你亲自运行的验证证据（命令、退出码、关键输出摘要）。

### 4) Plan Update

- passes_written: true | false
- issue_field: deleted | updated | unchanged | not_present
- rationale: 用证据解释为何如此更新

### 5) Git Commit

- commit_created: true | false
- commit_sha: ...
- commit_message: ...
- included_changes: 代码变更 + plan JSON 变更（如有）

### 6) Errors / Blockers

如果失败或阻塞：列出可行动的错误项（可复现、可定位、可修复）。

`result` 语义：
- `SUCCESS`：实现完成 + 验证通过 + 写回 `passes: true` + 成功时删除 `issue` 字段（若存在）+ 创建且仅创建一次提交
- `FAIL`：已尝试实现但验证失败/不完整；`passes` 必须保持/写回 `false`，并写入/更新非空 `issue[]`；仍然需要“恰好一次提交”记录现状（除非被明确要求不要提交）
- `BLOCKED`：输入/计划解析/依赖缺失等导致无法开工；不得改动任何文件；不得提交

## Workflow

### 阶段 0：校验输入与定位任务

1. 校验 fail-fast 条件
2. 读取并解析 `plan_file`
3. 用 `next_task.id` 在计划中定位对应 task（以计划文件为准）
4. 若任一步失败：输出 `BLOCKED` 报告并停止

### 阶段 1：派遣 Implementer Subagent（实现）

你是主 Controller Agent。不得直接动手实现代码；必须使用 Agent 工具创建 Implementer Subagent 执行实现工作。

Implementer 的职责：
- 按 task 的 `description` 与 `steps` 实现需求
- 尽量只读写 `task.files.create/modify/test` 指定的文件
- 避免超出任务范围（YAGNI）
- 在实现结束后给出变更摘要与建议的验证步骤（但不要把“通过”当成结论）

### 阶段 2：派遣 Spec Reviewer Subagent（规范合规审查）

Spec Reviewer 的职责：
- 仅依据 task 描述与验收标准审查：是否“做对了需要做的”，以及是否“做多了不该做的”
- 用 git diff / 文件检查给出结论：SPEC COMPLIANT 或 SPEC NON-COMPLIANT
- 若不合规：列出可行动的问题清单，要求 Implementer 返工

### 阶段 3：派遣 Code Quality Reviewer Subagent（代码质量审查）

Code Quality Reviewer 的职责：
- 关注风格、一致性、可维护性、测试、稳健性
- 若有问题：列出可行动的问题清单，要求 Implementer 返工

### 阶段 4：主 Agent 最终验证（证据在前）

你必须亲自做最终验证并记录证据，禁止依赖 subagent 的“看起来没问题”。

验证优先级：
1. task `steps` 中明确给出的验证命令/步骤
2. `validation_criteria` 可证伪/可复现的检查（写出你怎么验证）
3. 仍不明确：再次调用 `using-superpowers`，并使用它建议的验证类技能（例如 `verification-before-completion`）

### 写回规则：passes 与 issue

你只能在满足“新鲜、可复现、证据完备”的前提下写 `passes: true`。

成功（写 `passes: true`）时：
- 若 task 含有 `issue` 字段：必须删除该字段（而非置空）

失败（保持/写 `passes: false`）时：
- 必须写入或更新 `issue` 字段为非空数组 `issue[]`
- `issue[]` 每条必须可行动（包含失败点、位置、期望/实际、复现/证据指引）

### Git 提交规则：恰好一次

除 `BLOCKED` 外，都需要创建且仅创建一个提交，并且提交必须同时包含：
- 本任务的代码变更（如有）
- `plan_file` 对应 task 的 `passes/issue` 更新

提交信息建议（二选一，保持一致）：
- 功能实现：`feat(task): <id> <title>`
- 缺陷修复：`fix(task): <id> <title>`
- 仅记录问题：`chore(task): record issue for <id> <title>`

`BLOCKED`：禁止提交。

### 收尾：清理临时文件

执行结束前，必须清理本次任务运行中产生的临时文件（除非 task 明确要求保留作为产物或证据）：
- 临时目录（例如 `/tmp/...` 下本次创建的目录/文件）
- 构建产物与中间目录（例如 `build/`、`dist/`、`.cache/` 等，依据项目实际）
- 临时日志（例如 `*.log`），除非 task 要求将其作为验收证据保留

清理动作必须在最终报告里体现（写入 `files_touched` 或在 “Verification Evidence / Errors” 中说明保留/删除的理由）。

## Minimal Test Prompts（用于自测/回归）

1. “这是 find-next-task 的输出 JSON。请只执行 next_task 这一个任务，按证据写回 passes/issue 并提交一次。”
2. “同上，但该 task 含 issue[]（返工任务）。修复后必须删除 issue 字段并写 passes=true。”
3. “find-next-task 返回 selection_required=true。请按技能要求 fail-fast，不改动文件不提交，并输出 BLOCKED 报告。”
