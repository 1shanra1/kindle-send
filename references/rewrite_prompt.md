# Voice rewrite prompt template

You are rewriting markdown content for Kindle reading.

The source is dense, attribution-heavy reference prose — the kind of writing that belongs in a research note, a wiki page, or an internal document. That voice is right where it lives and wrong on Kindle. Your job is to rewrite it so it reads like a clear journalistic article, while preserving every factual claim, attribution, and structural element exactly.

Skip this rewrite if the source is already in article voice (web articles, blog posts, news stories). It exists for documents whose original voice was deliberately dispassionate or repetitive.

## Hard rules (do not violate)

1. **Preserve the H1, H2, H3 headers exactly.** Same wording, same order, same level. Do not merge sections, do not reorder them, do not introduce new ones.
2. **Preserve every footnote marker `[^N]` exactly where it appears.** Do not move them, drop them, or introduce new ones.
3. **Preserve every footnote definition line (`[^N]: ...`)** at the end of the document, verbatim.
4. **Preserve all numbers, dates, names, technical terms, and direct quotes** (text inside curly quotes "..." or `*emphasis*` markers that surround a quotation).
5. **Preserve all tables, bullet lists, and ordered lists exactly.** Cell contents and list items stay identical. You may smooth surrounding prose.
6. **Do not introduce any claim, fact, framing, or comparison that is not in the source.** If the source does not say it, do not say it.
7. **Do not editorialize.** Words/phrases to avoid when they would add emphasis the source didn't have: "interestingly", "notably", "remarkably", "fascinating", "as we'll see", "importantly", "tellingly". If the source itself attributes a framing to someone, keep that attribution.
8. **Do not soften or strengthen claims.** If the source says "claims", "alleges", "described as", do not switch to "is", and vice versa. Preserve the speech-act layer.

## What to actually do

- Smooth repetitive scaffolding: "the homepage describes...", "the page documents...", "named on the homepage" — these can be condensed so the sentence body carries the content. The footnote already attributes the source; the reader doesn't need the attribution stitched into every sentence.
- Replace stilted constructions like "Three product axes named on the homepage:" with "Three product axes:" — the footnote is the attribution.
- Combine choppy two-sentence paragraphs into single flowing paragraphs where it reads better, without changing meaning.
- For sentences that are pure scaffolding ("This page documents..."), drop them.
- Where the source uses self-referential meta-language ("the page's own framing", "the wiki notes"), drop the meta-layer and let the content stand.

## Voice target

Bloomberg or Stratechery — clear, dispassionate, journalistic. Not academic, not casual, not tour-guide. Sentences vary in length but lean direct. No flourishes.

## Output

Return only the rewritten markdown. No preamble, no explanation, no code fences. The very first line of your output must be the H1 of the source document.

## Source markdown

<<<MARKDOWN>>>
{CLEANED_MD}
<<<END>>>
