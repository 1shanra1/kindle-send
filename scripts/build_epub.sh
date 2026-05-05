#!/usr/bin/env bash
# Build an EPUB from a markdown file with the Kindle-optimized stylesheet.
#
# Usage: build_epub.sh <source.md> <output.epub> <title>
#
# Runs a small safety pass that strips a few Obsidian-specific syntaxes
# (wikilinks, image embeds, callouts). The pass is conservative — markdown
# without these constructs flows through untouched.

set -euo pipefail

SOURCE="${1:?source markdown path required}"
OUTPUT="${2:?output epub path required}"
TITLE="${3:-Untitled}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TMPMD=$(mktemp --suffix=.md)
trap 'rm -f "$TMPMD"' EXIT

python3 - "$SOURCE" "$TMPMD" <<'PY'
import re, sys
src, dst = sys.argv[1], sys.argv[2]
content = open(src, encoding="utf-8").read()

# Drop YAML frontmatter (only at the top of the file)
content = re.sub(r'^---\n.*?\n---\n', '', content, count=1, flags=re.S)

# Obsidian wikilinks: [[Page|Display]] -> *Display*; [[Page]] -> *Page*
# (No-op on plain markdown.)
content = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'*\2*', content)
content = re.sub(r'\[\[([^\]]+)\]\]', r'*\1*', content)

# Obsidian image embeds: drop
content = re.sub(r'!\[\[[^\]]+\]\]', '', content)

# Obsidian callouts: > [!note] Title -> > **Title**
content = re.sub(r'^>\s*\[!\w+\]\s*(.*)', r'> **\1**', content, flags=re.M)

open(dst, 'w', encoding="utf-8").write(content)
PY

pandoc "$TMPMD" \
    --from markdown \
    --to epub3 \
    --metadata title="$TITLE" \
    --metadata lang="en-US" \
    --toc --toc-depth=2 \
    --css "$SCRIPT_DIR/kindle.css" \
    --output "$OUTPUT"
