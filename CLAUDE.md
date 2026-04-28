# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a personal skills repository for Claude Code, maintained as a Claude Code Marketplace plugin via `.claude-plugin` structure. All skills are created and updated using the `skill-creator` skill.

## Repository Structure

```
skills/
├── .claude-plugin/
│   └── marketplace.json     # Marketplace definition
├── plugins/
│   └── [plugin-name]/
│       ├── .claude-plugin/
│       │   └── plugin.json  # Plugin manifest
│       └── skills/
│           └── [skill-name]/
│               └── SKILL.md  # Skill definition
└── README.md
```

## Key Files

- `.claude-plugin/marketplace.json`: Top-level marketplace definition listing all available plugins
- `plugins/*/.claude-plugin/plugin.json`: Individual plugin manifests
- `plugins/*/skills/*/SKILL.md`: Skill definitions

## Skills in This Repository

- **aitc-workflow** — Multi-agent batch orchestration with Plan, Execute, Lifecycle modes
- **github-pr-reviewer** — Automated PR review with inline comments and approve/request-changes verdict
- **github-pr-fixer** — Automated PR fix loop that reads review feedback, implements fixes, and replies
- **md2pdf** — Markdown to PDF conversion with CJK support (simplified, GitHub Light theme)

## Development Workflow

### Creating/Updating Skills

**Always use the `skill-creator` skill** when creating new skills or updating existing ones. This ensures all constraints and conventions are followed.

### Marketplace Plugin Structure

Each plugin follows this structure:
1. Plugin directory in `plugins/[plugin-name]/`
2. `.claude-plugin/plugin.json` manifest with `name`, `description`, and `version`
3. Skills located in `skills/[skill-name]/SKILL.md`

### Adding a New Plugin to Marketplace

When adding a new plugin, update `.claude-plugin/marketplace.json` to include the new plugin in the `plugins` array with:
- `name`: Plugin identifier
- `source`: Relative path to plugin directory (`./plugins/[plugin-name]`)
- `description`: Brief description of the plugin
