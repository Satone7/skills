---
name: academic-pdf-to-html
description: Convert academic PDF papers to beautifully styled HTML documents with Chinese summaries and chapter indexes. Use this skill whenever the user wants to convert a PDF paper to HTML, read a research paper as HTML, transform papers for web viewing, or mentions anything about making PDFs look good as web pages. Also trigger when the user says "paper to html", "pdf to html", "convert my papers", "美化论文", "论文转网页", or asks to make academic papers readable in a browser with proper formatting and figures.
---

# Academic PDF to HTML

Convert academic PDF papers into polished, web-ready HTML. The work is split between a deterministic script (mechanical fixes) and Claude (semantic understanding).

**Design principle**: The script handles what regex can do reliably. Claude handles what requires understanding context — grouping images with captions, writing summaries, translating section headings.

## Prerequisites

- **MinerU CLI** (`mineru-open-api`) installed and authenticated.
  - Install: `npm i -g mineru-open-api`
  - Authenticate: `mineru-open-api auth` (token from https://mineru.net/apiManage/token)
  - Verify: `mineru-open-api --version`

If MinerU is not installed, install it first: `npm i -g mineru-open-api`

## Workflow

### Step 1: Extract PDF to HTML

**Before extracting**, check the PDF file size. If it exceeds 200 MB or 600 pages, warn the user about MinerU's limits and suggest `--pages` for a range.

```bash
mineru-open-api extract "paper.pdf" -o ./output/ -f html
```

If auth error → ask user to run `mineru-open-api auth`. If timeout → retry with `--timeout 600`. If output dir missing → `mkdir -p ./output/`.

Key flags: `-f html` (required for images), `--pages 1-10`, `--language en|ch`, `--timeout 600`

### Step 2: Run postprocess script (deterministic)

**Checkpoint**: Confirm the MinerU HTML output exists and is non-empty before proceeding.

Script path: `plugins/academic-pdf-to-html/skills/academic-pdf-to-html/scripts/postprocess.py`

```bash
python3 plugins/academic-pdf-to-html/skills/academic-pdf-to-html/scripts/postprocess.py ./output/paper.html ./output/paper_styled.html
```

The script handles these reliably:
- Remove broken Mermaid blocks
- Fix heading levels (REFERENCES/ACKNOWLEDGMENTS/CONCLUSIONS → `<h2>`)
- Add heading IDs for TOC anchors
- Replace CSS with academic paper theme
- Fix `<title>` from h1 text
- Wrap Abstract in styled div
- Wrap author/affiliation in centered div
- Wrap references section
- Insert TOC skeleton and `ZH_SUMMARY_PLACEHOLDER`

The script does NOT attempt figure grouping — that requires semantic understanding.

### Step 3: Claude groups images into figures (semantic)

Run the diagnostic script to see which images need attention:

Script path: `plugins/academic-pdf-to-html/skills/academic-pdf-to-html/scripts/extract_figures.py`

```bash
python3 plugins/academic-pdf-to-html/skills/academic-pdf-to-html/scripts/extract_figures.py ./output/paper_styled.html --only-bare
```

This outputs JSON with each bare `<img>` and its surrounding text context. Use this to decide:

1. **Which images should be grouped together** (e.g., sub-figures (a), (b), (c) of one figure)
2. **Where the caption is** — captions can appear before the image, after it, or in the same `<p>` separated by `<br/>`. Caption formats vary: `Fig. N:`, `Fig. N.`, `Figure N.`, `FIG. N`, or even `(a) Code Snippet`
3. **Whether to add a `<figcaption>`** — some images have no caption

Then edit the HTML to wrap each group:

```html
<figure style="text-align: center; margin: 1.5em 0;">
  <img ... />
  <img ... />
  <figcaption style="font-size: 0.9em; color: #555; margin-top: 0.5em;">Figure 1. Caption text</figcaption>
</figure>
```

**For uncaptioned images**, wrap without `<figcaption>`:

```html
<figure style="text-align: center; margin: 1.5em 0;">
  <img ... />
</figure>
```

**Tips for efficiency**: If `--only-bare` shows 0 results, all images are already in figures — skip this step. For papers with many images, batch-edit by reading the JSON output and making all Edit calls at once.

### Step 4: Write the Chinese summary (semantic)

Replace `ZH_SUMMARY_PLACEHOLDER` with a Chinese summary of the paper:

1. Read the processed HTML (first 200 lines for title/abstract/structure, skip base64)
2. Write 1-2 paragraphs summarizing the problem and approach, then `<strong>主要发现：</strong>` with 3-6 bullet points
3. Replace `ZH_SUMMARY_PLACEHOLDER` in the file

**Checkpoint**: Verify `ZH_SUMMARY_PLACEHOLDER` no longer appears in the file.

### Step 5: Add bilingual TOC labels (semantic)

The script generates TOC entries with English-only headings. Add Chinese translations:

```html
<li><a href="#i.-introduction">Introduction &mdash; 引言</a></li>
```

### Step 6: Verify

Open in browser and check: figures visible with captions, summary displays, TOC links work, no raw Mermaid code, no `ZH_SUMMARY_PLACEHOLDER`.

**If verification fails**: see "Common Issues and Fixes" below.

## Common Issues and Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Images show as `<!-- image-->` | Used `flash-extract` instead of `extract` | Re-run with `extract -f html` |
| Mermaid syntax errors | MinerU broken Mermaid | Script removes them |
| `mineru-open-api: command not found` | CLI not installed | `npm i -g mineru-open-api` |
| Auth error on `extract` | No API token | Run `mineru-open-api auth` |
| Output file empty | Extraction failed | Check stderr, retry with `-v` |
| `ZH_SUMMARY_PLACEHOLDER` visible | Claude didn't replace | Manually find-and-replace |
| Images not in `<figure>` | Step 3 skipped | Run `extract_figures.py --only-bare` and group manually |
| Paper has no `<h2>` sections | Non-standard format | TOC will be empty; still add Chinese summary |
| Caption not standard format | Uses `(a)`, `Table N`, etc. | Claude identifies these via context in Step 3 |

## Batch Processing

```bash
for pdf in ./papers/*.pdf; do
  name=$(basename "$pdf" .pdf)
  mineru-open-api extract "$pdf" -o ./output/ -f html --timeout 600
  python3 plugins/academic-pdf-to-html/skills/academic-pdf-to-html/scripts/postprocess.py "./output/${name}.html" "./output/${name}_styled.html"
done
```

Then for each styled HTML, Claude runs Steps 3-5 (figure grouping, summary, bilingual TOC).