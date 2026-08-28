---
description: Add a new text to the library — guided PDF → transcript → curated → narration pipeline
---

Add a new lecture to the library, following `reader/lectures/README.md` step by step. The user's input (may be empty): $ARGUMENTS

If the input doesn't include them, ask the user for: the source (PDF path or where to get it), the desired slug (kebab-case, it becomes the folder name and the notes/progress key), and whether this lecture should get narration (TTS audio costs real money — ~US$2 per 70k characters).

Then work through the pipeline, checking in with the user at each decision point:

1. **Evaluate the PDF** (`pdftotext -f 1 -l 3 <pdf> - | head -40`). If it's bad OCR, STOP and ask the user to find a native digital edition — do not transcribe by hand or via the model (the content filter blocks extensive reproduction of copyrighted texts, and hand transcription isn't reproducible). Keep the original scan as `fragment.pdf`; it defines the excerpt's scope.
2. **Extract `transcript.md` with a script** (`build_transcript.py` inside the lecture folder), reconstructing paragraphs from the layout. The script must be reproducible byte-for-byte. Follow the output format in the README (title, `>` source line, `##` sections, blank-line-separated paragraphs).
3. **Curate** into `curated.md` via `build_curated.py` with an exact-match edit list (prune locators, cross-references and catalog apparatus; keep the author's voice). Ask the user about borderline cases.
4. **Spoken forms**: write `tts-overrides.json` for the title, headings, and any symbols/abbreviations the TTS would mangle.
5. **Synthesize** (only if the lecture gets audio): `python3 narrate.py <slug> --dry-run` first, show the user anything suspicious (odd sentence splits, spoken forms), then run it for real after their OK.
6. **Register** the lecture in `reader/lectures/index.json` (slug, title, status, tags, `audio`, word count) — the library home, TOC and offline precache all read from there.
7. **Verify**: serve with `python3 serve.py`, open `?doc=<slug>`, and if there's audio, test sentence taps and seeking. List the risk points to verify by ear in the lecture's `README.md`.

Remember: the lecture folder is gitignored (copyrighted content) — never commit its contents, only changes to shared code/docs like `index.json`.
