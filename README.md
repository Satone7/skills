# Claude Skills Repository

Personal collection of Claude Code skills for enhanced AI-assisted development workflows.

## Skills Overview

### writing-plans-plus

A structured planning tool that generates machine-readable task lists for software engineering projects.

**Use case:** When you have a spec or requirements for a multi-step task and need to generate a detailed implementation plan with structured tasks.

**Key features:**
- Parses user requirements into actionable implementation steps
- Generates machine-readable task lists
- Integrates with task management systems

## Installation

### Claude Code

#### 方法1：通过 Marketplace 安装（推荐）

1. 添加本仓库到 Claude Code Marketplace：
   ```
   /plugin add https://github.com/Satone7/skills.git
   ```

2. 查看可用的 skills：
   ```
   /plugin list
   ```

3. 安装所需的 skill：
   ```
   /plugin install writing-plans-plus
   ```

#### 方法2：手动安装

将 skill 目录复制到 Claude Code skills 目录：

```bash
mkdir -p ~/.claude/skills/
cp -r /path/to/this/repo/writing-plans-plus ~/.claude/skills/
```

### OpenClaw

在 OpenClaw 中安装 skills：

1. 克隆本仓库：
   ```bash
   git clone https://github.com/Satone7/skills.git ~/my-skills
   ```

2. 在 OpenClaw 配置中添加 skills 路径：
   ```yaml
   # ~/.openclaw/config.yaml
   skills:
     paths:
       - ~/my-skills/writing-plans-plus
   ```

3. 重启 OpenClaw 或重新加载配置。

## License

Personal use only.
