# Claude Skills Repository

Personal collection of Claude Code skills for enhanced AI-assisted development workflows.

## Skills Overview

### aitc-workflow

Multi-agent batch orchestration for long-running tasks. Provides Plan, Execute, and Lifecycle modes with team coordination and knowledge capture via task SKILLs.

### github-pr-reviewer

Automated GitHub PR reviewer that deep-analyzes pull requests and posts structured review feedback with inline comments, suggestions, and an approve/request-changes verdict.

### github-pr-fixer

Automated GitHub PR fixer that reads review feedback, implements code fixes, runs tests, and replies to reviewers until all review threads are resolved.

### md2pdf

Convert Markdown documents to PDF with CJK/Latin mixed text, fenced code blocks, tables, and clickable TOC using a simplified GitHub Light theme.

## Repository Structure

```
skills/
├── .claude-plugin/
│   └── marketplace.json     # Marketplace definition
├── plugins/
│   ├── aitc-workflow/
│   ├── github-pr-reviewer/
│   ├── github-pr-fixer/
│   └── md2pdf/
└── README.md
```

## License

Personal use only.
