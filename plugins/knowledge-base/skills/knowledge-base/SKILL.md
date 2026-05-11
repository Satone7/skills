---
name: knowledge-base
version: 0.3.3
description: >
  Access and manage the personal knowledge base stored on NAS via SSH.
  Connection parameters are loaded from env vars (KB_HOST, KB_PORT, KB_USER)
  or a local config file (~/.config/knowledge-base/config.json).
  Remote path is accessed via ~/kb symlink on the NAS.
  Use this skill whenever the user wants to record a note, look up information,
  search notes, organize the knowledge base, or mentions anything about their
  knowledge base, personal wiki, or notes stored on NAS. Also trigger when
  the user says "记笔记", "查笔记", "知识库", "我的笔记", or asks about
  technical configurations, reading notes, project docs, or CGRA papers
  that might be stored in the knowledge base.
---

# Knowledge Base

A personal knowledge base living on the NAS, accessed exclusively via SSH. The knowledge base stores notes across categorized directories, with a central index file and a CLAUDE.md governing its conventions.

## Access

### Connection Config

Connection parameters (host, user, port) are **not hardcoded** in this skill. They are stored in a local config file and loaded automatically.

**Config file**: `~/.config/knowledge-base/config.json`

```json
{
  "host": "<NAS hostname or IP>",
  "port": "<SSH port>",
  "user": "<SSH username>"
}
```

The remote knowledge base path is accessed via the `~/kb` symlink on the NAS. No need to configure it — just use `~/kb` in all SSH commands.

### Config Resolution (run this at the start of every session)

1. Check environment variables: `KB_HOST`, `KB_PORT`, `KB_USER`
2. If all three are set, use them (skip config file)
3. Otherwise, read `~/.config/knowledge-base/config.json`
4. If the config file exists and has all fields, use those values
5. If any value is missing, ask the user for the missing fields, then write the complete config to `~/.config/knowledge-base/config.json` (create the directory if needed). Do this once — future sessions will auto-load.
6. After resolving config, verify SSH access:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=5 -p $KB_PORT $KB_USER@$KB_HOST echo "OK"
```

If this fails, the current machine does not have SSH key access. Inform the user and stop — do not attempt alternative access methods.

7. **Read CLAUDE.md first**: Before any knowledge base operation, read the conventions file:

```bash
ssh -p $KB_PORT $KB_USER@$KB_HOST 'cat ~/kb/CLAUDE.md'
```

This file defines the knowledge base's structure, naming conventions, and operational rules. Understanding it ensures consistency with existing notes and prevents accidental breakage.

All operations go through SSH. Do not use local CIFS mounts.

### SSH Command Pattern

All file operations use this base pattern (using resolved config values):

```bash
ssh -p $KB_PORT $KB_USER@$KB_HOST '<command>'
```

Note: Use single quotes around the command to prevent local shell expansion. The knowledge base path uses `$HOME/kb` on the remote side. For paths containing emoji or spaces, wrap the path in double quotes inside the single-quoted command:

```bash
ssh -p $KB_PORT $KB_USER@$KB_HOST 'ls "$HOME/kb/💡 技术笔记/"'
```

Alternatively, escape spaces with `\`:

```bash
ssh -p $KB_PORT $KB_USER@$KB_HOST 'ls ~/kb/💡\ 技术笔记/'
```

## Directory Structure

```
~/kb/
├── CLAUDE.md              # Knowledge base conventions (read this first)
├── 📑 索引.md              # Central index of all content
├── skills-lock.json       # Skill lock file (do not modify)
├── 📚 阅读笔记/             # Reading notes & learning insights
├── 💡 技术笔记/             # Tech notes, configs, scripts, tools
├── 📝 日常笔记/             # Daily thoughts, ideas, misc
├── 📋 项目文档/             # Project plans, designs, summaries
├── 🔗 资源收藏/             # Useful links, tools, resources
└── 🔬 CGRA论文/             # CGRA papers (HTML format), with sub-index
```

## Operations

### 1. Query / Search

Search across the knowledge base using grep:

```bash
ssh -p $KB_PORT $KB_USER@$KB_HOST 'grep -ril "关键词" "$HOME/kb/"'
```

List files in a specific category:

```bash
ssh -p $KB_PORT $KB_USER@$KB_HOST 'ls "$HOME/kb/💡 技术笔记/"'
```

Read a specific note:

```bash
ssh -p $KB_PORT $KB_USER@$KB_HOST 'cat "$HOME/kb/💡 技术笔记/<filename>"'
```

### 2. Write / Create Note

Determine the correct category directory, then write:

```bash
ssh -p $KB_PORT $KB_USER@$KB_HOST 'cat > "$HOME/kb/<category>/<filename>.md" << '\''NOTEEOF'\''
<content>
NOTEEOF'
```

For simpler paths without special characters:

```bash
ssh -p $KB_PORT $KB_USER@$KB_HOST 'cat > ~/kb/<category>/<filename>.md << '\''NOTEEOF'\''
<content>
NOTEEOF'
```

Alternatively, use double quotes around the whole command and escape spaces in the path:

```bash
ssh -p $KB_PORT $KB_USER@$KB_HOST "cat > ~/kb/💡\ 技术笔记/<filename>.md << 'NOTEEOF'
<content>
NOTEEOF"
```

For heredoc content that may contain single quotes or special characters, use a different delimiter or escape properly.

#### Choosing the Category

| User Intent | Category |
|---|---|
| Technical configs, scripts, tool usage | 💡 技术笔记 |
| Book/article insights, learning summaries | 📚 阅读笔记 |
| Daily thoughts, random ideas, misc | 📝 日常笔记 |
| Project plans, designs, tracking docs | 📋 项目文档 |
| Useful links, tools, references | 🔗 资源收藏 |
| CGRA/academic papers | 🔬 CGRA论文 |

When uncertain, ask the user which category fits.

#### File Format Rule

Documents use **Markdown** by default, but switch to **HTML** when content is substantial:

- **≤ 100 lines**: Use `.md` (Markdown)
- **> 100 lines**: Use `.html` with embedded CSS styling

This threshold exists because long Markdown files lose readability without syntax highlighting and layout control — HTML with proper styling gives tables, code blocks, and mixed CJK/Latin text a much better reading experience.

When **supplementing** an existing `.md` note causes it to exceed 100 lines, convert the entire file to `.html` as part of the same task. The conversion workflow:

1. Read the current `.md` content
2. Convert Markdown to well-structured HTML (headings → `<h1>`–`<h4>`, tables → `<table>`, code → `<pre><code>`, lists → `<ul>`/`<ol>`, etc.)
3. Add embedded `<style>` appropriate to the content type (see style guide below)
4. Write the `.html` file, then delete the old `.md` file
5. Update the index if the filename changed

#### HTML Style Guide

Choose a style based on content type:

| Content Type | Style Approach |
|---|---|
| Technical notes (configs, scripts) | Clean monospace-friendly layout, dark code blocks, table borders |
| Reading notes / learning summaries | Serif body font, comfortable line-height, warm tones |
| Project docs (plans, tracking) | Grid-friendly, prominent tables, status badges |
| Resource collections | Link-heavy layout, card-like sections |
| Academic papers | Academic formatting, two-column optional, LaTeX-style headings |

All HTML files should include:
- `<meta charset="UTF-8">` for CJK support
- Responsive viewport meta tag
- Embedded `<style>` block (no external CSS dependencies)
- A footer with creation/update timestamp

#### File Naming Convention

- Chinese filenames, descriptive
- Optional date prefix: `2026-03-24_`
- Underscores `_` instead of spaces
- No special characters beyond emoji in directory names
- Extension follows the format rule above: `.md` or `.html`
- Example: `Ubuntu安装Docker脚本.md`, `2026-05-11_Claude_Code配置.html`

#### Note Template (Markdown, ≤ 100 lines)

```markdown
# [Title]

创建时间：YYYY-MM-DD

---

## [Sections as appropriate]

---

*笔记创建时间：YYYY-MM-DD*
```

#### Note Template (HTML, > 100 lines)

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[Title]</title>
<style>
  /* Choose style based on content type */
  body { font-family: ...; max-width: 900px; margin: auto; padding: 2em; }
  /* Add more rules as needed */
</style>
</head>
<body>
<h1>[Title]</h1>
<p class="meta">创建时间：YYYY-MM-DD</p>
<!-- Content sections -->
<footer><p>笔记创建时间：YYYY-MM-DD</p></footer>
</body>
</html>
```

### 3. Update Existing Note

Read the current file first. After making changes:

- **Count the total lines** of the updated content
- If the file is `.md` and now exceeds 100 lines → convert to `.html` (see File Format Rule above)
- If the file stays within 100 lines → overwrite the existing file as-is

Overwrite via SSH:

```bash
ssh -p $KB_PORT $KB_USER@$KB_HOST 'cat > "$HOME/kb/<category>/<filename>" << '\''NOTEEOF'\''
<updated content>
NOTEEOF'
```

If converting from `.md` to `.html`, also remove the old file:

```bash
ssh -p $KB_PORT $KB_USER@$KB_HOST 'rm "$HOME/kb/<category>/<old_filename>.md"'
```

When updating, preserve the existing structure and only modify the relevant sections. Update the "最后更新" or creation timestamp at the bottom.

### 4. Update Index

After creating a significant new note or restructuring, update the central index:

```bash
ssh -p $KB_PORT $KB_USER@$KB_HOST 'cat > "$HOME/kb/📑 索引.md" << '\''NOTEEOF'\''
<updated index content>
NOTEEOF'
```

The index currently lists each category with a brief description and a link. When adding a new category or a significant new sub-section, reflect it here. Update the "最后更新" date.

### 5. Maintain / Organize

- **Reindex**: Read all directories, check the index is accurate, update if needed
- **Quality check**: Verify notes have proper headers, timestamps, and consistent formatting
- **Suggest improvements**: If you notice notes that are stubs (like "待补充" sections) or could be better organized, mention it to the user

## Important Notes

- **Emoji in paths**: The directory names contain emoji prefixes. Always quote paths with single quotes in SSH commands.
- **No local mount**: Never use `/mnt/nas/` paths. All operations go through SSH.
- **Sensitive content**: The knowledge base contains API keys and tokens (e.g., in 💡 技术笔记). Handle these responsibly — never display full credentials unless the user explicitly asks, and warn if notes with credentials are being shared or exposed.
- **Sub-indices**: The 🔬 CGRA论文 directory has its own `📑 CGRA论文索引.md`. Respect this sub-index pattern for large specialized collections.
- **Content encoding**: Files are UTF-8. Ensure proper locale settings in SSH commands if encountering encoding issues (`LC_ALL=en_US.UTF-8`).
