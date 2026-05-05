#!/usr/bin/env bash
# Build an EPUB from a markdown file and email it to the user's Kindle.
#
# Usage: kindle_book.sh <markdown_path> "<Title>"
#
# Required env vars:
#   KINDLE_EMAIL          — your Send-to-Kindle address
#
# Email backend env vars (read by the default backend, scripts/send_email.py):
#   SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_USE_SSL
#
# Optional:
#   KINDLE_EMAIL_BACKEND  — path to an executable that accepts
#                           --to <addr> --subject <s> --body <b> --attach <file>.
#                           Default: <skill>/scripts/send_email.py

set -euo pipefail

MARKDOWN="${1:?Usage: kindle_book.sh <markdown_path> <title>}"
TITLE="${2:-Untitled}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "${KINDLE_EMAIL:-}" ]; then
    echo "ERROR: KINDLE_EMAIL env var must be set (your Send-to-Kindle address)" >&2
    exit 2
fi
if [ ! -f "$MARKDOWN" ]; then
    echo "ERROR: markdown file not found: $MARKDOWN" >&2
    exit 2
fi

BACKEND="${KINDLE_EMAIL_BACKEND:-$SCRIPT_DIR/send_email.py}"
if [ ! -x "$BACKEND" ]; then
    if [ -f "$BACKEND" ]; then
        echo "ERROR: email backend exists but is not executable: $BACKEND" >&2
        echo "Run: chmod +x $BACKEND" >&2
    else
        echo "ERROR: email backend not found: $BACKEND" >&2
    fi
    exit 2
fi

SAFE_NAME=$(echo "$TITLE" | tr -c '[:alnum:]' '_' | tr -s '_' | sed 's/^_//;s/_$//')
EPUB_DIR=$(dirname "$(readlink -f "$MARKDOWN")")
EPUB_PATH="$EPUB_DIR/${SAFE_NAME:-book}.epub"

bash "$SCRIPT_DIR/build_epub.sh" "$MARKDOWN" "$EPUB_PATH" "$TITLE"
SIZE=$(stat -c%s "$EPUB_PATH" 2>/dev/null || stat -f%z "$EPUB_PATH")
echo "Built: $EPUB_PATH ($SIZE bytes)" >&2

"$BACKEND" \
    --to "$KINDLE_EMAIL" \
    --subject "$TITLE" \
    --body "Sent via kindle-send." \
    --attach "$EPUB_PATH"

echo "Sent: $TITLE -> $KINDLE_EMAIL"
