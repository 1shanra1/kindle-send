# kindle-send

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that turns arbitrary markdown into a clean, article-voice EPUB and emails it to your Kindle's Send-to-Kindle address.

The pipeline is simple: **markdown in → EPUB out → email to your Kindle**. What makes it interesting is what the orchestrator (the Claude Code agent driving the skill) can stitch onto either end:

- "Send this markdown file to my Kindle." → straight pipeline.
- "Send my Obsidian wiki page on X to my Kindle." → resolve the page, optionally apply the Obsidian preprocessor, optionally do a voice rewrite, ship.
- "Compile a short book from these five articles and send it to my Kindle." → fetch each article (web tools, RSS, etc.), concatenate as chapters, ship.
- "Bundle the recent posts on X into one EPUB." → orchestrator searches, dedups, compiles, ships.

The core scripts only care about: a markdown file, a title, and a destination. Everything upstream — what the markdown is, where it came from, how it was assembled — is the orchestrator's call.

## What the scripts do

- **`scripts/kindle_book.sh`** — entry point. Takes a markdown file + title, builds an EPUB with the Kindle stylesheet, hands it to the email backend.
- **`scripts/build_epub.sh`** — pandoc wrapper. Markdown → EPUB3 with `kindle.css`. Runs a tiny Obsidian-syntax safety pass (wikilinks, image embeds, callouts) so passing a raw Obsidian page through doesn't break — but the safety pass is conservative and won't damage non-Obsidian markdown.
- **`scripts/send_email.py`** — default email backend. SMTP with credentials from environment variables. Swappable via `KINDLE_EMAIL_BACKEND`.
- **`scripts/kindle.css`** — Kindle-optimized stylesheet. Forces pure-white background (pandoc's `#fdfdfd` default reads as visibly off-white on Paperwhite eInk), strips inherited container backgrounds, lets the device pick the font.
- **`preprocessors/obsidian_clean.py`** — *optional*. If your input is an Obsidian-style vault page, this strips frontmatter, drops wiki-meta sections (Log, Schema, "What this X doesn't say"), converts `[[sources/<id>]]` citations to numbered footnotes (with a generated bibliography pulled from each source page's frontmatter), and flattens wikilinks. Don't run this on non-Obsidian markdown — it expects Obsidian conventions.
- **`references/rewrite_prompt.md`** — *optional*. The prompt template for a "voice rewrite" pass: smooth dense, attribution-heavy reference prose into journalistic prose without changing facts. Useful for vault-style or research-note inputs; pointless for prose that's already article-shaped.

## Prerequisites

- **Pandoc** ≥ 3.0. `apt install pandoc`, `brew install pandoc`, etc.
- **Python** 3.10+.
- **An email account that can send to your Kindle.** The bundled `send_email.py` uses standard SMTP. Gmail with an [App Password](https://support.google.com/accounts/answer/185833) is the easiest path; any SMTP server works.
- **Send-to-Kindle setup on Amazon's side** (one-time):
  1. Sign in to [Amazon Manage Your Content and Devices](https://www.amazon.com/hz/mycd/myx) → Preferences → Personal Document Settings.
  2. Note your **Send-to-Kindle email address** (e.g. `yourname_AbCdEf@kindle.com`) — this becomes `KINDLE_EMAIL`.
  3. Add the **From-address** (the SMTP user) to the **Approved Personal Document E-mail List**. Without this, Amazon silently drops everything.

## Configuration

| Variable               | Purpose                                                                              |
| ---------------------- | ------------------------------------------------------------------------------------ |
| `KINDLE_EMAIL`         | Your Send-to-Kindle address.                                                         |
| `SMTP_HOST`            | e.g. `smtp.gmail.com`.                                                               |
| `SMTP_PORT`            | `465` for SSL, `587` for STARTTLS.                                                   |
| `SMTP_USER`            | The address you're sending from. Must be on Amazon's Approved Senders list.          |
| `SMTP_PASS`            | App password for `SMTP_USER`.                                                        |
| `SMTP_USE_SSL`         | Optional. `1` for SSL, `0` for STARTTLS. Defaults to SSL when port is 465.           |
| `KINDLE_EMAIL_BACKEND` | Optional. Path to a custom send script (see "Swapping the email backend"). |

## Installation

### As a Claude Code skill

```bash
cd <your-project>/.claude/skills
git clone https://github.com/<owner>/kindle-send.git
chmod +x kindle-send/scripts/*.sh kindle-send/scripts/*.py kindle-send/preprocessors/*.py
```

Claude Code will pick up the skill automatically. `SKILL.md` describes the trigger phrases ("send X to kindle", "compile X to kindle", "kindle this", etc.) and the orchestration steps.

### Standalone

The scripts are independently runnable — Claude Code is not required. See "Manual usage" below.

## Manual usage

The simplest case: you have a markdown file, you want it on your Kindle.

```bash
KINDLE_EMAIL="..." SMTP_HOST="..." SMTP_PORT="..." SMTP_USER="..." SMTP_PASS="..." \
    bash scripts/kindle_book.sh path/to/article.md "Article Title"
```

For Obsidian-style vault pages, optionally run the preprocessor first:

```bash
python3 preprocessors/obsidian_clean.py page.md "$VAULT_ROOT" cleaned.md
bash scripts/kindle_book.sh cleaned.md "Page Title"
```

For a multi-source mini-book, just concatenate markdown chapters into one file and ship it:

```bash
cat chapter1.md chapter2.md chapter3.md > book.md
bash scripts/kindle_book.sh book.md "My Compiled Book"
```

EPUB chapter breaks happen on every H1 (per `kindle.css`), so put each chapter under its own `# Heading`.

## Voice rewrite (optional)

If your input is dense, attribution-heavy, or research-note style, you may want a voice pass before the EPUB build. `references/rewrite_prompt.md` is a tightly-constrained prompt template — preserves headers, footnotes, tables, lists, numbers, names, and direct quotes verbatim while smoothing repetitive scaffolding into journalistic prose.

You drive this yourself with whatever LLM you prefer (Claude, GPT, local model). When using Claude Code, the `SKILL.md` describes how the orchestrator should invoke a subagent for this step.

## Swapping the email backend

`kindle_book.sh` invokes `KINDLE_EMAIL_BACKEND`, defaulting to `scripts/send_email.py`. Any executable that accepts these flags works as a drop-in replacement:

```
<your-script> --to <addr> --subject <s> --body <b> --attach <file>
```

Use cases: corporate SMTP relays, AWS SES, Mailgun, msmtp, mailx, OAuth-based Gmail clients, etc.

## Layout

```
kindle-send/
├── README.md
├── LICENSE
├── SKILL.md                          # orchestration instructions for Claude Code
├── scripts/
│   ├── kindle_book.sh                # markdown + title -> EPUB -> email
│   ├── build_epub.sh                 # pandoc wrapper
│   ├── send_email.py                 # default SMTP backend
│   └── kindle.css                    # Kindle-optimized stylesheet
├── preprocessors/
│   └── obsidian_clean.py             # optional, opt-in
└── references/
    └── rewrite_prompt.md             # optional voice-rewrite prompt
```

## License

MIT — see [LICENSE](LICENSE).
