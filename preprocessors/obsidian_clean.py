#!/usr/bin/env python3
"""Optional Obsidian-vault preprocessor for kindle-send.

Run this on a single Obsidian vault page before passing it to the EPUB build.
It turns Obsidian-specific syntax into Kindle-friendly markdown:

  1. Strip YAML frontmatter
  2. Drop wiki-meta sections by header name (Log, Schema, Changelog,
     "What this X doesn't say")
  3. Convert source citations [[sources/<id>]] -> numbered footnotes
  4. Drop image embeds ![[X.png]]
  5. Convert remaining wikilinks [[Y]] -> italic
  6. Flatten Obsidian callouts (> [!note] Title -> > **Title**)
  7. Append pandoc footnote definitions populated from each source page's frontmatter

Don't run this on non-Obsidian markdown — the section drops and citation
conversions assume Obsidian conventions and will mangle other formats.

Usage: obsidian_clean.py <input.md> <vault_root> <output.md>

Vault layout this script expects:
  <vault_root>/sources/<id>.md   — referenced via [[sources/<id>]] in pages

Source pages should have frontmatter with `url` and `created` fields, and an
H1 line — those populate the footnote bibliography. Missing fields fall back
to sensible defaults.
"""
import os
import re
import sys
from pathlib import Path


DROP_SECTION_PATTERNS = [
    re.compile(r'^what this .+? doesn[’\']?t say\s*$', re.I),
    re.compile(r'^log\s*$', re.I),
    re.compile(r'^schema\s*$', re.I),
    re.compile(r'^changelog\s*$', re.I),
]

SOURCE_REF_RE = re.compile(r'\[\[sources/([^\]|]+?)(?:\|[^\]]+)?\]\]')


def strip_frontmatter(md: str) -> str:
    return re.sub(r'^---\n.*?\n---\n*', '', md, count=1, flags=re.S)


def drop_meta_sections(md: str) -> str:
    """Drop sections whose header (any level) matches DROP_SECTION_PATTERNS.

    A "section" runs from its header to the next header at the same or shallower level.
    """
    lines = md.split('\n')
    out = []
    skip_level = None
    for line in lines:
        m = re.match(r'^(#{1,6})\s+(.+?)\s*$', line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            if skip_level is not None and level <= skip_level:
                skip_level = None
            if any(p.match(title) for p in DROP_SECTION_PATTERNS):
                skip_level = level
                continue
        if skip_level is not None:
            continue
        out.append(line)
    return '\n'.join(out)


def collect_source_refs(md: str) -> list[str]:
    seen: list[str] = []
    for m in SOURCE_REF_RE.finditer(md):
        sid = m.group(1).strip()
        if sid not in seen:
            seen.append(sid)
    return seen


def replace_source_refs(md: str, source_to_n: dict[str, int]) -> str:
    def repl(m):
        sid = m.group(1).strip()
        return f'[^{source_to_n[sid]}]'
    md = SOURCE_REF_RE.sub(repl, md)
    md = re.sub(r'\s*\(\s*(\[\^\d+\])\s*\)', r' \1', md)
    md = re.sub(r'\s*\(\s*(\[\^\d+\])\s*,\s*(\[\^\d+\])\s*\)', r' \1 \2', md)
    return md


def replace_wikilinks(md: str) -> str:
    md = re.sub(r'!\[\[[^\]]+\]\]', '', md)
    md = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'*\2*', md)
    md = re.sub(r'\[\[([^\]]+)\]\]', r'*\1*', md)
    return md


def flatten_callouts(md: str) -> str:
    return re.sub(r'^>\s*\[!\w+\]\s*(.*)', r'> **\1**', md, flags=re.M)


def parse_source_meta(source_path: Path) -> dict:
    out = {'title': source_path.stem, 'url': None, 'date': None}
    if not source_path.exists():
        return out
    content = source_path.read_text(encoding='utf-8')
    fm = re.match(r'^---\n(.*?)\n---', content, re.S)
    if fm:
        for line in fm.group(1).splitlines():
            if ':' not in line:
                continue
            k, _, v = line.partition(':')
            k = k.strip().lower()
            v = v.strip().strip('\'"')
            if k == 'url' and v:
                out['url'] = v
            elif k in ('created', 'updated', 'ingested') and v and not out['date']:
                out['date'] = v
    h1 = re.search(r'^#\s+(.+?)\s*$', content, re.M)
    if h1:
        out['title'] = h1.group(1).strip()
    return out


def main() -> int:
    if len(sys.argv) < 4:
        print("Usage: obsidian_clean.py <input.md> <vault_root> <output.md>", file=sys.stderr)
        return 64
    input_path = Path(sys.argv[1])
    vault_root = Path(sys.argv[2])
    output_path = Path(sys.argv[3])

    md = input_path.read_text(encoding='utf-8')
    md = strip_frontmatter(md)
    md = drop_meta_sections(md)

    source_ids = collect_source_refs(md)
    source_to_n = {sid: i + 1 for i, sid in enumerate(source_ids)}
    md = replace_source_refs(md, source_to_n)
    md = replace_wikilinks(md)
    md = flatten_callouts(md)

    if source_ids:
        fn_lines = []
        for sid in source_ids:
            meta = parse_source_meta(vault_root / 'sources' / f'{sid}.md')
            parts = [meta['title']]
            if meta['url']:
                parts.append(meta['url'])
            if meta['date']:
                parts.append(f'retrieved {meta["date"]}')
            fn_lines.append(f"[^{source_to_n[sid]}]: {'. '.join(parts)}.")
        md = md.rstrip() + '\n\n' + '\n\n'.join(fn_lines) + '\n'

    output_path.write_text(md, encoding='utf-8')
    print(f"sources={len(source_ids)}", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
