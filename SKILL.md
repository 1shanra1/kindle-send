---
name: kindle-send
description: "Send arbitrary markdown to the user's Kindle as a clean EPUB. Trigger on 'send to kindle', 'kindle this', 'push to kindle', 'compile a book to kindle', or any request to read content on Kindle — whether the source is a local file, a web article, an Obsidian vault page, or several of the above stitched into a mini-book."
allowed-tools: Bash, Read, Write, Agent, WebFetch, WebSearch
---

# Kindle Send

Pipeline: get markdown → (optional preprocess) → (optional voice rewrite) → EPUB → email to Kindle.

The skill is intentionally generic. Your job as the orchestrator is to decide what counts as "the markdown" for the user's request and to assemble it. Then you hand a markdown file and a title to `kindle_book.sh` and you're done.

## Decision tree (what to do based on the user's request)

**Case A: User points at a specific local markdown file** ("send `notes/oxide.md` to kindle"):
1. Use the file as-is.
2. Skip to Step 4 (Send) below.

**Case B: User asks for an Obsidian vault page** ("send my wiki page on X to kindle", "kindle the X note"):
1. Locate the page in the vault. (You decide how — fuzzy match against `${VAULT_ROOT}/wiki`, or whatever convention the user has.)
2. Run the Obsidian preprocessor: `python3 ${CLAUDE_SKILL_DIR}/preprocessors/obsidian_clean.py <page.md> <vault_root> <out.md>`
3. (Optional) Voice rewrite pass — see Step 3 below.
4. Send.

**Case C: User asks for a single web article** ("send https://example.com/article to kindle"):
1. Fetch the page (WebFetch or a similar tool that returns markdown).
2. Save the markdown to a temp file.
3. (Optional) Voice rewrite pass.
4. Send.

**Case D: User asks for a compiled mini-book from multiple sources** ("compile a book on X from these articles", "bundle the recent posts on Y into one EPUB"):
1. Resolve sources — search, fetch URLs, glob a directory, whatever the user described.
2. Convert each source to markdown if it isn't already. Each chapter starts with a single `# Title` header — `kindle.css` page-breaks on H1 so every chapter starts on a fresh page.
3. Concatenate into one markdown file. Optionally prepend a `# Book Title` cover and a generated `## Contents` list.
4. (Optional) Voice rewrite — usually skip this for fetched articles; they're already in article voice.
5. Send.

**Case E: Anything else** — get markdown into a file by whatever means the user described, then send.

## Step 3: Voice rewrite (optional)

Useful when the input is dense, attribution-heavy, or research-note-style (Obsidian vault pages, internal documentation, dense reference material). Pointless for content that's already in article voice (web articles, blog posts, news stories).

If you decide to do it: read `references/rewrite_prompt.md`, substitute the cleaned markdown into the `<<<MARKDOWN>>>` block, spawn a subagent with that prompt, write the returned markdown to a new temp file, and pass that to Step 4.

When in doubt, skip the rewrite. A second pass costs tokens and time and risks introducing errors.

## Step 4: Send

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/kindle_book.sh <markdown_path> "<Title>"
```

Required env: `KINDLE_EMAIL` plus SMTP credentials (or a custom `KINDLE_EMAIL_BACKEND`). The script exits non-zero with a clear error if any required env var is missing — pass that error to the user and ask them to fix the config.

After sending, reply to the user with the title and a confirmation. Amazon usually delivers within a minute.

## Compilation guidance (Case D specifics)

When stitching multiple sources into one EPUB:

- Each source becomes one chapter under a single `# Heading`. Don't have the body re-introduce its own H1; convert any source-internal H1s to H2 to preserve the chapter hierarchy.
- Add a generated `# Sources` final chapter listing each chapter's URL/origin if the sources came from the web.
- Cap individual chapter length to something reasonable (~5-15k words). If a source is much longer, summarize or split.
- For book-length compilations, consider asking the user whether they want a voice rewrite or a prose summary — these are different products.

## Limitations

- Image attachments are dropped — Kindle won't see them. If a source has critical images, warn the user.
- Send-to-Kindle has a 50 MB attachment cap (Amazon's). Stay under that.
- The "From" address must be on the user's Amazon Approved Personal Document E-mail List. If sends silently disappear, that's the first thing to check.
