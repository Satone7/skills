#!/usr/bin/env python3
"""Extract image context from styled HTML for Claude to review.

Outputs a JSON array of image entries with surrounding text context,
so Claude can decide how to group images into <figure> elements and
assign captions. This script does NOT modify the HTML.

Usage:
    python extract_figures.py <styled.html>

Output (JSON array):
[
  {
    "index": 0,
    "position": 12345,
    "context_before": "...100 chars before img...",
    "context_after": "...200 chars after img...",
    "in_figure": false
  },
  ...
]
"""

import argparse
import json
import re
import sys


def extract_img_contexts(html_path, max_context=250):
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    results = []
    for i, m in enumerate(re.finditer(r'<img[^>]*>', content)):
        pos = m.start()

        # Check if already inside <figure>
        before = content[max(0, pos - 3000):pos]
        in_figure = before.count('<figure') > before.count('</figure>')

        # Get text context (strip base64 from context_after)
        ctx_before = content[max(0, pos - max_context):pos]
        ctx_after_raw = content[m.end():m.end() + max_context * 2]

        # Strip base64 image data from context for readability
        ctx_before = re.sub(r'data:image/[^"]{0,50}', 'data:image/[...]', ctx_before)
        ctx_after = re.sub(r'data:image/[^"]+', '[BASE64]', ctx_after_raw)
        ctx_after = ctx_after[:max_context]

        # Clean whitespace for JSON readability
        ctx_before = ctx_before.replace('\n', '\\n')
        ctx_after = ctx_after.replace('\n', '\\n')

        results.append({
            "index": i,
            "position": pos,
            "in_figure": in_figure,
            "context_before": ctx_before,
            "context_after": ctx_after,
        })

    return results


def main():
    parser = argparse.ArgumentParser(description='Extract image contexts for Claude figure grouping')
    parser.add_argument('html', help='Styled HTML file to analyze')
    parser.add_argument('--only-bare', action='store_true', help='Only show images not inside <figure>')
    args = parser.parse_args()

    results = extract_img_contexts(args.html)

    if args.only_bare:
        results = [r for r in results if not r['in_figure']]

    print(json.dumps(results, ensure_ascii=False, indent=2))
    bare_count = sum(1 for r in results if not r['in_figure'])
    total = len(results) + (sum(1 for r in extract_img_contexts(args.html) if r['in_figure']) if args.only_bare else 0)
    if not args.only_bare:
        bare_count = sum(1 for r in results if not r['in_figure'])
        print(f"\n# Total: {len(results)} images, {bare_count} bare (not in <figure>)", file=sys.stderr)
    else:
        print(f"\n# {len(results)} bare images need figure wrapping", file=sys.stderr)


if __name__ == '__main__':
    main()
