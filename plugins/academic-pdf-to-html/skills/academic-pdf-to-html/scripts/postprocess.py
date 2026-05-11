#!/usr/bin/env python3
"""Post-process MinerU-extracted HTML: deterministic fixes only.

Only handles mechanical transformations that don't require semantic understanding.
Semantic tasks (figure grouping, caption matching, Chinese summary writing) are
left to Claude as a separate step.

Usage:
    python postprocess.py <input.html> <output.html> [--title "Paper Title"]
"""

import argparse
import re


def remove_broken_mermaid(content):
    """Remove broken Mermaid code blocks. MinerU emits both JPEG images and
    malformed Mermaid code; we keep the JPEGs and remove the Mermaid."""
    content = re.sub(r'flowchart\s*\n```mermaid\s+.*?```', '', content, flags=re.DOTALL)
    content = re.sub(r'<pre class="mermaid">\s*.*?\s*</pre>', '', content, flags=re.DOTALL)
    return content


def fix_heading_levels(content):
    """Normalize heading levels: REFERENCES/ACKNOWLEDGMENTS/CONCLUSIONS often
    come out as <h1> instead of <h2>."""
    content = re.sub(r'<h1[^>]*>REFERENCES</h1>', '<h2 id="references">REFERENCES</h2>', content)
    for pattern_id, heading_re in [
        ('acknowledgments', r'<h1[^>]*>(ACKNOWLEDGMENTS?|Acknowledgments?|Acknowledgement)</h1>'),
        ('conclusions', r'<h1[^>]*>(CONCLUSIONS?|Conclusions?)</h1>'),
    ]:
        def _replacer(m, _id=pattern_id):
            return f'<h2 id="{_id}">{m.group(1)}</h2>'
        content = re.sub(heading_re, _replacer, content, flags=re.IGNORECASE)
    return content


def add_heading_ids(content):
    """Add id attributes to <h2> headings for TOC anchor links."""
    def slugify(text):
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s]+', '-', text)
        return text

    def add_id(match):
        attrs = match.group(1) or ''
        text = match.group(2)
        if 'id=' in attrs:
            return match.group(0)
        return f'<h2{attrs} id="{slugify(text)}">{text}</h2>'

    content = re.sub(r'<h2([^>]*)>(.*?)</h2>', add_id, content)
    return content


def wrap_abstract(content):
    """Wrap the Abstract paragraph in a styled div."""
    def _replacer(m):
        return '<div class="abstract"><strong>Abstract</strong>&nbsp;' + m.group(1) + '</div>'
    content = re.sub(r'<p>\s*Abstract[—\-](.*?)</p>', _replacer, content, flags=re.DOTALL)
    return content


def wrap_author_info(content):
    """Wrap author/affiliation lines in a centered div."""
    h1_end = content.find('</h1>')
    if h1_end < 0:
        return content
    h1_end += 5

    next_section = re.search(r'(?:<h2|<div class="zh-summary"|<div class="abstract")', content[h1_end:])
    if not next_section:
        return content

    section_start = h1_end + next_section.start()
    author_block = content[h1_end:section_start].strip()

    if '<p>' in author_block:
        wrapped = f'\n<div class="author-info">\n{author_block}\n</div>\n'
        content = content[:h1_end] + wrapped + content[section_start:]
    return content


def fix_markdown_tables(content):
    """Convert markdown table blocks (| ... |) to proper HTML tables.
    MinerU sometimes outputs tables as raw markdown instead of HTML."""
    lines = content.split('\n')
    result = []
    i = 0
    changed = False

    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith('|') and stripped.endswith('|'):
            table_lines = []
            while i < len(lines):
                s = lines[i].strip()
                if s.startswith('|') and s.endswith('|'):
                    table_lines.append(s)
                    i += 1
                else:
                    break
            rows = []
            for tl in table_lines:
                cells = [c.strip() for c in tl.strip('|').split('|')]
                if all(re.match(r'^[-:]+$', c) for c in cells):
                    continue
                rows.append(cells)
            if rows:
                max_cols = max(len(r) for r in rows)
                for r in rows:
                    while len(r) < max_cols:
                        r.append('')
                html = '<table>\n<thead>\n<tr>\n'
                for cell in rows[0]:
                    html += f'<th>{cell}</th>\n'
                html += '</tr>\n</thead>\n<tbody>\n'
                for row in rows[1:]:
                    html += '<tr>\n'
                    for cell in row:
                        html += f'<td>{cell}</td>\n'
                    html += '</tr>\n'
                html += '</tbody>\n</table>'
                result.append(html)
                changed = True
            continue
        result.append(lines[i])
        i += 1

    return '\n'.join(result) if changed else content


def fix_table_headers(content):
    """Convert first row of <table> to <thead>/<th> if it uses <td> for all cells."""
    def _replacer(m):
        table_content = m.group(0)
        # Find first <tr>...</tr> that contains only <td> (no <th>)
        first_row = re.search(r'<tr>(.*?)</tr>', table_content, re.DOTALL)
        if not first_row:
            return table_content
        row_content = first_row.group(1)
        if '<th' in row_content or '<thead' in table_content:
            return table_content
        # Convert <td> to <th> in first row
        new_row = row_content.replace('<td>', '<th>').replace('</td>', '</th>')
        thead = f'<thead>\n<tr>{new_row}</tr>\n</thead>\n<tbody>'
        # Remove the original first row and wrap remaining in tbody
        rest = table_content[first_row.end():]
        # Remove existing <tbody> if present
        rest = rest.replace('<tbody>', '', 1)
        return f'<table>\n{thead}{rest}'

    return re.sub(r'<table>\s*<tbody>\s*<tr>.*?</tr>', _replacer, content, flags=re.DOTALL)


def fix_latex_in_tables(content):
    """Convert raw LaTeX inline math in table cells to HTML.
    Handles $N \\times$ → N× and similar simple patterns.
    Only targets simple patterns; complex formulas are left for MathJax."""
    # Replace $N.NN \times /N.NN \times$ patterns
    def _replace_times(m):
        nums = re.findall(r'(\d+\.?\d*)', m.group(0))
        if len(nums) >= 2:
            return f'{nums[0]}×/{nums[1]}×'
        return m.group(0)

    content = re.sub(
        r'\$\s*\d+\.?\d*\s*\\times\s*/\s*\d+\.?\d*\s*\\times\s*\$',
        _replace_times, content
    )
    # Replace standalone $N \times M$ patterns
    def _replace_standalone(m):
        nums = re.findall(r'(\d+\.?\d*)', m.group(0))
        if len(nums) >= 2:
            return f'{nums[0]}×{nums[1]}'
        return m.group(0)

    content = re.sub(
        r'\$\s*\d+\.?\d*\s*\\times\s*\d+\.?\d*\s*\$',
        _replace_standalone, content
    )
    # Replace bare $\times$ → ×
    content = re.sub(r'\$\s*\\times\s*\$', '×', content)
    # Replace $\times N$ → ×N
    content = re.sub(r'\$\s*\\times\s*(\d+)\s*\$', r'×\1', content)
    return content


def wrap_references(content):
    """Wrap the references section in a styled div."""
    refs_h2 = content.find('<h2 id="references">')
    if refs_h2 < 0:
        refs_h2 = content.find('>REFERENCES</h2>')
        if refs_h2 < 0:
            return content
        refs_h2 = content.rfind('<h2', 0, refs_h2)

    h2_close = content.find('</h2>', refs_h2) + 5
    body_end = content.rfind('</body>')
    if body_end < h2_close:
        return content

    before = content[:h2_close]
    refs_body = content[h2_close:body_end].strip()
    after = content[body_end:]
    return before + '\n<div class="references">\n' + refs_body + '\n</div>\n' + after


def fix_title(content, title=None):
    """Replace generic <title>full</title> with the actual paper title."""
    if title:
        content = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', content)
    else:
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content)
        if h1_match:
            extracted = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
            content = re.sub(r'<title>.*?</title>', f'<title>{extracted}</title>', content)
    return content


ACADEMIC_STYLE = '''
  @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&family=Noto+Sans+SC:wght@400;500;700&family=Lora:ital,wght@0,400;0,700;1,400&display=swap');

  :root {
    --primary: #2c3e50;
    --accent: #3498db;
    --accent-light: #ebf5fb;
    --text: #333;
    --text-light: #666;
    --bg: #ffffff;
    --border: #e0e0e0;
    --shadow: rgba(0,0,0,0.08);
  }

  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }

  body {
    max-width: 820px; margin: 0 auto; padding: 2rem 3rem;
    font-family: 'Lora', 'Noto Serif SC', 'Georgia', serif;
    font-size: 16px; line-height: 1.8; color: var(--text); background: var(--bg);
  }
  h1 {
    font-size: 1.8em; text-align: center; color: var(--primary);
    margin-top: 0; margin-bottom: 0.3em;
    font-family: 'Noto Sans SC', 'Helvetica Neue', sans-serif; font-weight: 700;
  }
  .author-info {
    text-align: center; color: var(--text-light); font-size: 0.9em;
    line-height: 1.6; margin-bottom: 2em; font-family: 'Noto Sans SC', sans-serif;
  }
  .zh-title {
    text-align: center; color: var(--accent); font-size: 1.1em;
    font-family: 'Noto Sans SC', sans-serif; margin: 0.3em 0 0.2em 0; font-weight: 500;
  }
  .institution {
    text-align: center; color: var(--text-light); font-size: 0.85em;
    font-family: 'Noto Sans SC', sans-serif; margin: 0 0 0.5em 0;
  }
  h2 {
    color: var(--primary); border-bottom: 2px solid var(--accent); padding-bottom: 0.3em;
    margin-top: 2.5em; font-family: 'Noto Sans SC', 'Helvetica Neue', sans-serif;
    font-weight: 700; font-size: 1.4em;
  }
  h3, h4 {
    color: var(--primary); font-family: 'Noto Sans SC', 'Helvetica Neue', sans-serif; margin-top: 1.8em;
  }
  p { margin: 0.8em 0; }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  figure {
    margin: 2em 0; padding: 1.5em; background: var(--accent-light);
    border-radius: 8px; text-align: center; border: 1px solid var(--border);
  }
  figure img { max-width: 100%; height: auto; border-radius: 4px; margin: 0.5em; }
  figcaption { font-size: 0.9em; color: var(--text-light); margin-top: 0.8em; font-style: italic; }
  table {
    width: 100%; border-collapse: collapse; margin: 1.5em 0;
    font-size: 0.85em; font-family: 'Noto Sans SC', sans-serif;
  }
  th, td { border: 1px solid var(--border); padding: 0.5em 0.8em; text-align: center; }
  th, tr:first-child td { background: var(--primary); color: white; font-weight: 500; }
  tr:nth-child(even) { background: #f9f9f9; }
  .abstract {
    background: linear-gradient(135deg, #f8f9fa 0%, #eef2f7 100%);
    border-left: 4px solid var(--accent); padding: 1em 1.5em; margin: 1.5em 0;
    border-radius: 0 6px 6px 0; font-size: 0.95em;
  }
  .abstract strong { color: var(--primary); }
  .zh-summary {
    background: linear-gradient(135deg, #fef9e7 0%, #fdf2e9 100%);
    border: 1px solid #f0c27f; border-radius: 10px; padding: 1.5em 2em; margin: 2em 0;
    font-family: 'Noto Sans SC', sans-serif; font-size: 0.95em; line-height: 1.9;
    color: #444; box-shadow: 0 2px 8px var(--shadow);
  }
  .zh-summary h3 { margin-top: 0; color: #c0392b; font-size: 1.2em; border-bottom: none; padding-bottom: 0; }
  .zh-summary ul { padding-left: 1.2em; }
  .zh-summary li { margin: 0.3em 0; }
  .toc {
    background: #f4f6f9; border-radius: 10px; padding: 1.2em 2em;
    margin: 1.5em 0 2em 0; border: 1px solid var(--border);
    font-family: 'Noto Sans SC', sans-serif;
  }
  .toc h3 { margin: 0 0 0.8em 0; font-size: 1.1em; color: var(--primary); border-bottom: none; padding-bottom: 0; }
  .toc ol { padding-left: 1.5em; margin: 0; }
  .toc li { margin: 0.3em 0; }
  .toc a { color: var(--primary); font-weight: 500; }
  .references {
    font-size: 0.88em; color: var(--text-light); line-height: 1.6;
    margin-top: 2em; border-top: 1px solid var(--border); padding-top: 1em;
  }
  @media (max-width: 700px) {
    body { padding: 1rem 1.2rem; }
    h1 { font-size: 1.4em; }
  }
'''


def replace_style(content):
    return re.sub(r'<style>.*?</style>', f'<style>\n{ACADEMIC_STYLE}\n</style>', content, flags=re.DOTALL)


def build_toc_html(content):
    headings = re.findall(r'<h2[^>]*id="([^"]+)"[^>]*>(.*?)</h2>', content)
    if not headings:
        return ''
    items = [f'    <li><a href="#{slug}">{text}</a></li>' for slug, text in headings]
    return '<div class="toc">\n<h3>章节索引</h3>\n<ol>\n' + '\n'.join(items) + '\n</ol>\n</div>\n'


def build_zh_summary_placeholder():
    return '<div class="zh-summary">\n<h3>中文摘要</h3>\nZH_SUMMARY_PLACEHOLDER\n</div>\n'


def insert_summary_and_toc(content, zh_html, toc_html):
    insert_pos = None
    abstract_pos = content.find('<div class="abstract">')
    h2_pos = re.search(r'<h2', content)
    if abstract_pos > 0:
        insert_pos = abstract_pos
    elif h2_pos:
        insert_pos = h2_pos.start()
    if insert_pos:
        content = content[:insert_pos] + zh_html + '\n' + toc_html + content[insert_pos:]
    return content


def postprocess(input_html, output_html, title=None, zh_summary=None):
    with open(input_html, 'r', encoding='utf-8') as f:
        content = f.read()

    content = remove_broken_mermaid(content)
    content = fix_heading_levels(content)
    content = add_heading_ids(content)
    content = replace_style(content)
    content = fix_title(content, title)
    content = wrap_abstract(content)
    content = wrap_author_info(content)
    content = fix_markdown_tables(content)
    content = fix_table_headers(content)
    content = fix_latex_in_tables(content)
    content = wrap_references(content)

    zh_html = (
        f'<div class="zh-summary">\n<h3>中文摘要</h3>\n{zh_summary}\n</div>\n'
        if zh_summary else build_zh_summary_placeholder()
    )
    toc_html = build_toc_html(content)
    content = insert_summary_and_toc(content, zh_html, toc_html)

    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(content)
    return content


def main():
    parser = argparse.ArgumentParser(description='Deterministic post-processing of MinerU HTML')
    parser.add_argument('input', help='Input HTML from MinerU')
    parser.add_argument('output', help='Output HTML')
    parser.add_argument('--title', help='Paper title (auto-detected if omitted)')
    parser.add_argument('--zh-summary', help='Chinese summary HTML to inject')
    args = parser.parse_args()
    postprocess(args.input, args.output, args.title, args.zh_summary)
    print(f'Written: {args.output}')


if __name__ == '__main__':
    main()
