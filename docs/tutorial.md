# Tutorial: from a course PDF to a narrated lecture

This is the complete walkthrough of how content gets produced in
escolib **today**: with a Claude Code session driving the pipeline. It is
the third pillar of the project — the curation workflow — shown end to end
on a realistic case.

## What you need

- **Python 3** and **ffmpeg** (only for narration).
- **Claude Code** running in the repo. The repo ships everything the session
  needs: `CLAUDE.md` (working context), the `/new-lecture` command, and
  `reader/lectures/README.md` (the pipeline reference the session follows).
- Only if you want narration: a **Google Cloud** project with the
  Text-to-Speech API enabled and `gcloud` authenticated. Cost: ~US$30 per
  million characters — about **US$2 for 80 minutes** of audio, paid once
  per text (a per-sentence cache makes later corrections cost cents).

No AI? You can still *read* any already-produced lecture — the reader is a
plain HTML file. The AI session is only needed to *produce* new content.

## The session

Open Claude Code in the repo and type:

```
/new-lecture apuntes/durkheim-cap1.pdf
```

What follows is a guided conversation. The session knows the pipeline; you
make the calls. A typical run:

### 1. It evaluates your PDF

```
Claude: El PDF tiene texto nativo (no es un escaneo): tildes correctas,
        guiones largos, sin errores de OCR. Sigo con la extracción.
```

Two possible paths here:

- **Native digital text** → straight to extraction.
- **A scan with bad OCR** → the session will STOP and ask you to find a
  native digital edition of the same translation. This is deliberate:
  fighting bad OCR produces bad lectures, and transcribing a copyrighted
  translation through the model runs into content-filter limits. The scan
  is still kept (as `fragment.pdf`) because it defines the exact scope of
  the excerpt.

### 2. It extracts the faithful text — with a script, not by hand

The session writes a `build_transcript.py` inside the lecture folder that
reconstructs paragraphs from the PDF layout (indentation, page breaks,
hyphenation) and regenerates `transcript.md` byte-for-byte. Reproducible
and auditable: the text was *extracted*, not *retyped*.

```
Claude: transcript.md: 42 párrafos · 6.930 palabras. El fragmento del
        escaneo termina a mitad de oración en la p. 52 — corté en la
        oración completa equivalente y lo documenté en el README.
```

### 3. It curates the text for study — asking you the borderline cases

Curation criterion: **prune the scholarly apparatus, keep the author's
voice**. Locators like `(IV, 1913, pp. 253 ss.)`, cross-references,
catalog data — out. Substantive asides and technical terms — kept. The
edits live as an exact-match list in `build_curated.py`, so every change
is documented and re-runnable.

```
Claude: Hay un caso dudoso: la aclaración «(véase el prólogo)» — ¿es
        aparato o contenido? El prólogo está incluido en esta lecture.
You:    Dejala.
```

### 4. It prepares the spoken forms

Anything that is not plain prose is a gamble with the TTS voice. The
session writes `tts-overrides.json`: the title gets a spoken form with
author and work, headings get read naturally ("I." → "Parte uno."),
symbols get expanded. Generic rules already live in `narrate.py`.

### 5. You narrate — after a dry run

```
python3 narrate.py durkheim-cap1 --dry-run   # review sentence splits, spoken forms
python3 narrate.py durkheim-cap1             # synthesize (this one costs money)
```

The dry run lists every sentence as it will be spoken — the session
reviews it with you and flags anything suspicious. The real run emits
`audio.mp3` (one continuous file) and `timeline.json` (exact start/end
per sentence — this is what powers the synchronized reading).

### 6. It registers the lecture and you verify

The session adds the entry to `lectures/index.json` (title, tags, word
count) and reminds you of the by-ear checklist: foreign names, number
expansions, anything flagged during curation. Open
`http://localhost:8123/?doc=durkheim-cap1`, turn on narration, tap a few
sentences. If something sounds wrong: fix `tts-overrides.json` and re-run
— the cache means you only pay for the corrected sentences.

## What you end up with

```
lectures/durkheim-cap1/
  fragment.pdf        the original source (defines the excerpt's scope)
  build_transcript.py reproducible extraction
  transcript.md       faithful text — canonical, for quoting
  build_curated.py    documented edit list
  curated.md          study text — what the reader shows and narrates
  tts-overrides.json  spoken forms
  audio.mp3           one CBR mp3
  timeline.json       the per-sentence sync map
  README.md           source, decisions, points verified by ear
```

That folder **is** the study piece — text, audio and (once you read it)
your annotations. Making it a formal, versioned, shareable package is the
project's first pillar and the most important issue on the roadmap.

## Using another AI

Nothing in the pipeline is Claude-specific except the polish of the
guidance: the working context lives in `CLAUDE.md` and `AGENTS.md` (a
format most coding agents read), the pipeline reference is
`reader/lectures/README.md`, and every step's contract is "produce these
files, reproducibly". Adapting the flow to other providers is a tracked
roadmap item.
