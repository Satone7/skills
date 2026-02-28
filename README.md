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
   /plugin marketplace add Satone7/skills
   ```

   或使用完整 URL：
   ```
   /plugin marketplace add https://github.com/Satone7/skills.git
   ```

2. 查看可用的 skills：
   ```
   /plugin list
   ```

3. 安装所需的 skill：
   ```
   /plugin install writing-plans-plus@satone-skills
   ```

#### 方法2：手动安装

将 skill 目录复制到 Claude Code skills 目录：

```bash
mkdir -p ~/.claude/skills/
cp -r /path/to/this/repo/plugins/writing-plans-plus ~/.claude/skills/
```

### OpenClaw

#### 方法1：通过 Marketplace 安装（推荐）

1. 添加本仓库到 OpenClaw Marketplace：
   ```
   /plugin marketplace add Satone7/skills
   ```

   或使用完整 URL：
   ```
   /plugin marketplace add https://github.com/Satone7/skills.git
   ```

2. 查看可用的 skills：
   ```
   /plugin list
   ```

3. 安装所需的 skill：
   ```
   /plugin install writing-plans-plus@satone-skills
   ```

#### 方法2：手动安装

将 skill 目录复制到 OpenClaw skills 目录：

```bash
mkdir -p ~/.openclaw/skills/
cp -r /path/to/this/repo/plugins/writing-plans-plus ~/.openclaw/skills/
```

## Repository Structure

```
skills/
├── .claude-plugin/
│   └── marketplace.json     # Marketplace definition
├── plugins/
│   └── writing-plans-plus/
│       ├── .claude-plugin/
│       │   └── plugin.json  # Plugin manifest
│       └── skills/
│           └── writing-plans-plus/
│               └── SKILL.md  # Skill definition
└── README.md
```

## License

Personal use only.
