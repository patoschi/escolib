# Lectures: the PDF → text → audio process

Guide for adding a new text to the reader. The Claude Code command `/new-lecture` walks through these steps interactively.

> Lecture folders are **not versioned** (they contain copyrighted texts, heavy audio and PDFs — see the repo `.gitignore`); this document describes the patterns their scripts follow.

## Anatomy of a lecture

```
lectures/<slug>/
  fragment.pdf        original source (the scan/course PDF that defines the scope)
  transcript.md       text FAITHFUL to the edition — canonical, for quoting; only edition typos are fixed
  curated.md          text CURATED for study — what the reader shows and what gets narrated
  tts-overrides.json  per-lecture spoken forms for synthesis
  audio.mp3           TTS narration (a single CBR mp3)
  timeline.json       audio↔text map (turns → sentences with start_ms/end_ms)
  build/              synthesis cache (one wav per sentence; regenerable, not published)
  build_curated.py    script with the exact list of transcript → curated edits
  README.md           source, decisions, points to verify by ear
```

The reader (`../index.html`) loads `?doc=<slug>` trying `text.md` → `curated.md` → `transcript.md`, and offers narration only if `timeline.json` exists and its `source` field matches the displayed variant.

## Step 1 — Evaluate the PDF

```bash
pdftotext -f 1 -l 3 fragment.pdf - | head -40
```

- **Native text** (digital edition): correct words, accents intact, proper em dashes `—`. Ideal — go to step 2.
- **Scanned OCR**: errors like `preliminm`, `Grert%en`, `rn`→`m`, fused words. **Don't fight a bad OCR.** Transcribing by hand or via a language model doesn't work either: extensively reproducing a copyrighted translation runs into the model's content filter.
- **➜ If the PDF is bad, ASK THE USER to look for alternative editions** (the text usually exists as a native digital edition; it's an excerpt for study purposes). Keep the original scan as `fragment.pdf` anyway, because it defines the exact scope (pages, where it starts and ends).

If an alternative shows up, verify it is **the same translation** by checking its beginning and end against the scan.

## Step 2 — Extract `transcript.md`

With `pdftotext -layout`, paragraph reconstruction is reliable:

- indentation at the start of a line = new paragraph; a line at the margin after a page break = continuation (page breaks do NOT split paragraphs);
- short centered lines = section headings;
- remove: page numbers, repeated running heads, footnote markers `[n]` (when the editor's notes live outside the excerpt);
- rejoin hyphenated words; watch for residue like `Pro- bleme`;
- if the scanned excerpt ends mid-sentence, cut at the equivalent **complete sentence** of the good edition, and document it.

Do this **with a script, not by hand** (a `build_transcript.py` inside the lecture folder): it's reproducible, auditable, and avoids the content-filter problem. The script should regenerate `transcript.md` byte-for-byte; adapt its heading regexes, page range and cut sentence per text.

Output format (what the reader's `renderDoc` expects):

```markdown
# Title

> Author · Work, ch. N · YEAR. Lede/description of the excerpt, translator, publisher.

## I. Subheading (if any)

Paragraphs separated by a blank line, no internal line breaks.
```

## Step 3 — Curate: `transcript.md` → `curated.md`

Criterion: **prune the scholarly apparatus, keep the author's voice.**

- **Omit**: locators `(IV, 1913, pp. 253 ff.)`, catalog data (`Spanish trans. …`), internal cross-references `(§ 2)`, `(cf. no. 6)`, `(see above)`.
- **Foreign title + vernacular gloss** → keep only the vernacular one. Keep journal names when they are the only identification.
- **Keep**: rhetorical and substantive asides in parentheses or dashes, standalone foreign technical terms (*Verstehen*).
- Surviving `cf.` → "see".

Implementation: a `build_curated.py` in the lecture folder with a list of exact, unique replacements (the script fails if a pattern doesn't appear exactly once). Borderline cases (content or apparatus?) are decided by reading, not by regex.

## Step 4 — Spoken forms: `tts-overrides.json`

Generic rules live in `narrate.py` (e.g. `§ N.` → its spoken form). Text-specific ones go in the lecture's JSON:

- title → a spoken form with author and work;
- headings (`I. …` → "Part one. …");
- symbols the TTS can't read: `2 × 2 = 4`, `α)`, a quoted `§ X`, editorial brackets.

Rule of thumb: **anything that isn't plain prose is a gamble with the TTS** — either prune it in step 3, give it a spoken form here, or note it for verification by ear.

## Step 5 — Synthesize

```bash
python3 narrate.py <slug> --dry-run   # review sentence splits and spoken forms
python3 narrate.py <slug>             # synthesizes, assembles, emits audio.mp3 + timeline.json
```

What it does and why:

- **Unit = sentence** (exact per-sentence timestamps for narration mode). Chirp3-HD rejects sentences longer than ~400 characters: long ones are split internally on `;`/`—`/`,` (the timeline never sees those seams).
- **Per-hash cache** in `build/`: fixing one sentence and regenerating costs only that sentence.
- Sample-exact PCM assembly with silences (160 ms sentence / 700 ms paragraph / 850 ms title) → a single **CBR mp3** (required for range-based seeking to land correctly).
- Requires `ffmpeg` and `gcloud` authenticated against a GCP project with the Cloud Text-to-Speech API enabled. Cost: ~US$30 per million characters (~$2 for a 70k-character chapter).

## Step 6 — Test and verify

```bash
python3 ../serve.py          # from reader/ — do NOT use `python -m http.server`:
                             # without Range support, audio seeks reset to 0:00
open "http://localhost:8123/?doc=<slug>"
```

- Turn on narration mode, click sentences, try space/arrow keys.
- **Verify by ear** the risk points (note them in the lecture's README with timestamps: foreign names, symbol expansions, numbers). If something sounds wrong: fix `tts-overrides.json` and go back to step 5 (the cache makes it cheap).

## Quick checklist

1. [ ] PDF evaluated; if the OCR is bad → **ask the user for alternatives**
2. [ ] `transcript.md` faithful, excerpt cut at a complete sentence, documented
3. [ ] `curated.md` derived by script with a list of edits
4. [ ] `tts-overrides.json` with titles and symbols
5. [ ] `--dry-run` reviewed (odd short sentences, splits, spoken forms)
6. [ ] Audio generated; risk points verified by ear
7. [ ] Lecture README: source, decisions, verification timestamps
8. [ ] **Add the lecture to `index.json`** (library home + TOC menu read the catalog from there)
