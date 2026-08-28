# escolib

An open source kit for **complete study pieces**: the faithful text of an
excerpt, its audio synced sentence by sentence, and your annotations —
together, and meant to travel.

**Landing + live demo**: https://escolib.com/

No standard exists today for that combination. E-readers annotate but won't
narrate your own texts; audiobook apps narrate but aren't built for study;
TTS tools read aloud but leave nothing persistent — and none of them makes
the result shareable, so every student redoes the same curation work on the
same texts. The goal is to **standardize that result so it can be shared**:
curate a text once, well, and let the package travel.

## The three pillars

Today all three live in this repo; the design keeps them separable.

1. **A standard, transportable format** — the study piece as a package:
   curated text, audio with per-sentence timestamps (`timeline.json`),
   spoken forms, exportable annotations. Today a folder with clear
   conventions; the goal is a versioned package with import/export,
   watching EPUB 3 Media Overlays closely. *Being defined — the most
   important issue on the roadmap.*
2. **A reader that plays it** — a self-hosted, account-free, single-file
   web app. *Works today; it's the demo.*
3. **AI curation workflows** — the laid-out path for producing content:
   Claude Code sessions with commands (`/new-lecture`) and repo context
   that guide PDF → faithful text → curated text → narration, with
   script-reproducible edits. *Works today with Claude Code; other
   providers are a roadmap item.*

**How it actually works**: producing a new lecture currently requires an AI
session (Claude Code) plus, only for narration, a Google Cloud TTS account
(~US$2 per 80 minutes of audio). That dependency is a design decision, not
a temporary gap — quality curation is exactly what a guided AI session does
well. *Reading* already-produced lectures requires nothing: the reader is
plain HTML.

## The reader

- **Two reading modes** — continuous scroll and epub-style pagination —
  with bookmarks, a table of contents, and automatic reading/listening
  progress that survives font-size changes.
- **Notes designed for deep reading**: highlight with a double tap, tag
  with colors, comment by keyboard or **voice dictation**. Notes export to
  JSON and to an AI-friendly markdown format (excerpt + surrounding
  context + your comment), so they can feed a study session.
- **Synchronized narration**: one continuous MP3 per text with a
  per-sentence timeline. Tap a sentence to move the playhead; the active
  sentence is highlighted and the view follows the audio — including page
  turns mid-sentence.
- **Installable as a PWA**; lectures you've read stay available offline
  (network-first service worker — nothing is bulk-downloaded, and
  reloading always gets fresh content).

## Quick start

```bash
git clone https://github.com/patoschi/escolib.git
cd escolib/reader
python3 serve.py          # http://localhost:8123/  (demo library included)
```

Open a specific text with `?doc=<slug>`. To read from a phone or tablet:
`python3 serve.py --lan`, then same Wi-Fi network + your machine's LAN IP
(without `--lan` the server binds to localhost only). Voice dictation requires a
secure context (HTTPS or localhost).

To **produce** your first lecture, open a Claude Code session in the repo
and run `/new-lecture <your.pdf>` — the session drives the whole pipeline
and asks you to decide the borderline cases. The full annotated walkthrough
is in [`docs/tutorial.md`](docs/tutorial.md); the pipeline reference is
[`reader/lectures/README.md`](reader/lectures/README.md).

## Structure

```
docs/           tutorial: from a course PDF to a narrated lecture
reader/
  index.html    the complete reader (self-contained HTML+CSS+JS) — see reader/README.md
  serve.py      dev server with Range request support (without it, audio can't seek)
  lectures/     one folder per text: source, transcript, curated text, audio, timeline
                narrate.py = TTS pipeline · README.md = the PDF → lecture process
                index.json = library catalog (shelves, status, tags)
```

## What gets versioned

Code, documentation, and the public-domain demo texts. Everything else
stays out of the repo — see `.gitignore`:

- **Your lecture content** (copyrighted texts, audio, PDFs) is never committed.
- **Narration audio is a build artifact**, reproducible with `narrate.py` —
  only the short *A la deriva* sample ships in the repo so a fresh clone
  plays out of the box. The longer demo narrations are
  [release assets](https://github.com/patoschi/escolib/releases/tag/demo-audio),
  streamed by the reader through the `audioUrl` field of the catalog;
  without a local mp3 or an `audioUrl`, a lecture simply doesn't offer
  narration.

Reader notes and progress live in the browser's `localStorage`, exportable
to JSON from the notes panel.

There is no business model: this is collaborative open source, with the
technical vision tracked as [public issues](https://github.com/patoschi/escolib/issues).

## License

MIT — see `LICENSE`.

---

### En español

Escolib es un kit open source para piezas de estudio completas: el texto
fiel de un fragmento, su audio sincronizado por oración y tus anotaciones,
juntos y transportables. Tres pilares: un formato estándar compartible (en
definición), un reader self-hosted que funciona hoy (es la demo), y
workflows de curaduría con IA (sesiones de Claude Code con el camino ya
trazado). Producir contenido nuevo requiere una sesión de IA y ~US$2 de
TTS por hora de audio; leer lo ya producido no requiere nada. El objetivo
de fondo: estandarizar para compartir — que curar un texto se haga una
sola vez y le sirva al siguiente. La demo y los textos están en español; la
documentación del repo, en inglés.
