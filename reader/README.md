# reader

Self-contained web reader (`index.html`, no dependencies, no build step) for studying long texts with notes and synchronized narration. Loads lectures via `?doc=<slug>` (tries `text.md` → `curated.md` → `transcript.md`; `&file=<name>` forces a specific variant).

## Features

**Reading**
- **Epub-style page mode** (default) and **continuous scroll** (book button): CSS columns the width of the viewport, `‹ 12/141 ›` indicator, swipe / arrow keys / mouse wheel to turn pages. The DOM does not change between modes: notes and narration work identically in both.
- **Table of contents** (list button): title, `##` sections, `§ N.` openings, and bookmarks.
- **Automatic progress**: reading and audio positions save themselves (settled scroll, page turn, every ~5 s of audio, tab hidden), anchored to text offsets — they survive font-size changes. On open, the reader resumes with a "Go to start" toast as an escape hatch.
- **Bookmarks** (ribbon in the header, Kindle-style): toggles on the current view, fills in when the visible area contains one; listed with % and excerpt inside the TOC.

**Notes** (no mode toggle: direct gestures)
- **Double click/tap on a word** creates a highlight and opens the editor; **handles** stretch the selection. Tapping a highlight reopens it.
- Color tags, auto-saving comment, **voice dictation** (Web Speech API, requires HTTPS or localhost).
- The editor is the same everywhere: a minibar + box anchored next to the note. When the on-screen keyboard opens (`visualViewport`), the box becomes a full-width strip glued to the keyboard, the playback bar hides, and the document shifts so the highlight stays visible.
- Notes panel (header): filters by tag, **Copy for AI** (markdown with excerpt + context paragraph + comment), **Export/Import JSON** (notes + bookmarks + progress, for another device).

**Narration** (headphones button; available when the lecture has a `timeline.json` whose `source` matches the displayed variant)
- One continuous MP3 + a per-sentence timeline. **Tapping a sentence moves the playhead** (it only plays if audio was already playing); play/pause (space), **fragment jumps** ⏮ ⏭ (← →), speed control.
- Active-sentence highlight uses the **CSS Custom Highlight API** (doesn't touch the DOM → coexists with note `<mark>`s).
- **Follow mode**: the view follows the audio; navigating far away turns it off, and it re-arms on return / sentence tap / play. For sentences that span a page break, the page turn is **interpolated by character position** within the sentence's duration.
- Annotating (double tap) **pauses** the audio; while a note is open, tap-to-seek is inert. Play resumes by bringing the view back to the sentence.

## Architecture decisions worth not breaking

- **Everything anchors to offsets of `doc.textContent`** (notes, progress, bookmarks, timeline sentences). Overlays are re-derived via `rangeFromOffsets` → rects. Golden rule in page mode: positioning absolute overlays inside `#doc` requires adding `doc.scrollLeft` (content coordinates, not screen coordinates).
- `caretOffsetFromPoint` has a **column-aware** geometric fallback (iPad returns null frequently); any point-based lookup must respect column reading order.
- **Gestures**: tap = audio navigation · double tap = note · drag on text = page swipe · drag on a handle = stretch selection. Tap/drag discrimination is by distance (>12px) from `pointerdown`; swipes don't arm on `.hand/.gdot/mark`.
- **Stable pagination**: if the lecture has narration, the page height ALWAYS reserves room for the audio bar — toggling narration must not repaginate. Only font-size changes and resizes repaginate (keeping the position by offset).
- The first click of a double click **must not seek**: tap-to-seek is deferred 360 ms and cancelled when a double tap is detected.
- Elements hidden with `transform` + `backdrop-filter` can paint in the wrong place on iOS: hide with `visibility` as well.

## Development

- `python3 serve.py [port] [--lan]` — required: it supports **Range requests** (Python's `http.server` doesn't, and without ranges the `<audio>` element can't seek) and sends `Cache-Control: no-store`. The service worker is network-first, so a plain reload fetches fresh content; visited lectures remain as the offline fallback.
- Headless verification: Chrome `--headless=new` + DevTools Protocol (`Runtime.evaluate` with `awaitPromise`) to simulate gestures and check state. Test note/narration flows **on page ≥ 2 of page mode** — coordinate bugs don't show on page 1 (`scrollLeft = 0`).
- `localStorage` keys: `audiolib.reader.v1.notes.<slug>` (legacy prefix kept on purpose: renaming would orphan existing notes), `.pos.<slug>`, `.bm.<slug>`, `.prefs` (the slug includes the variant: `my-first-text:curated`).
