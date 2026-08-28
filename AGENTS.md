# AI agent context

Working context for AI coding agents (Cursor, Codex, etc.) lives in [`CLAUDE.md`](CLAUDE.md) — read it first. In short:

- **Docs map**: `README.md` (overview) · `reader/README.md` (reader features, architecture decisions, gotchas) · `reader/lectures/README.md` (PDF → lecture pipeline).
- **Serve** with `cd reader && python3 serve.py` (never a plain static server: audio seeking needs Range requests).
- **Verify** JS changes with `node --check` on the extracted `<script>` of `reader/index.html`; test note/narration flows on page ≥ 2 of page mode.
- **Never commit lecture content** (copyrighted texts, audio, PDFs) — only code and docs are versioned.

Claude Code users also get the `/new-lecture` command (`.claude/commands/new-lecture.md`), which walks through adding a new text end to end.
