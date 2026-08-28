# escolib — working context

Study library: annotatable web reader with synchronized TTS narration. Main docs:
`README.md` (overview) · `reader/README.md` (features + architecture + gotchas) · `reader/lectures/README.md` (PDF → lecture process).

## How to work here

- **Serve**: `cd reader && python3 serve.py` → `http://localhost:8123/?doc=<slug>`. Never `python3 -m http.server` (without Range requests, audio can't seek). For phones/tablets on the LAN: run `python3 serve.py --lan` (localhost-only by default) and use the machine's local IP. The service worker is network-first, so a plain reload gets fresh content; if a client seems stuck on old code, unregister its SW once (DevTools → Application).
- **Verify reader changes**: extract the last `<script>` from `index.html` and run `node --check`; for flows, headless Chrome + CDP (`--remote-debugging-port`, `Runtime.evaluate` with `awaitPromise:true`, screenshots via `Page.captureScreenshot`). **Test note/narration flows on page ≥ 2 of page mode** — page 1 hides coordinate bugs (scrollLeft = 0).
- Touch/iOS bugs are the norm, not the exception — treat iPhone/iPad as the primary target.

## Reader code rules

See "Architecture decisions" in `reader/README.md`. The ones most often broken by accident:
- Absolute overlays inside `#doc` in page mode: add `doc.scrollLeft`.
- All anchoring is by `doc.textContent` offset, never by pixels.
- Don't add actions to single tap (reserved for audio navigation) or gestures that collide with page swipe/selection handles.
- iOS: hide with `visibility` in addition to `transform`; sheets via `visualViewport`; `touch-action:manipulation`.

## Narration pipeline (`reader/lectures/narrate.py`)

- GCP TTS **Chirp3-HD** (requires gcloud ADC against a project with the Cloud TTS API enabled). ~US$2 per 80 min.
- Synthesizes **per sentence** (exact timestamps); sentences >~400 chars are split on `;`/`—`/`,` (the API rejects them). Per-hash cache in `build/` — regenerating only re-synthesizes what changed.
- `--dry-run` before spending. Spoken forms: generic rules in the script, text-specific ones in the lecture's `tts-overrides.json`.
- Sample-exact PCM assembly → one CBR mp3 + `timeline.json` (`source` ties the narration to the text variant).

## Learned constraints (don't retry)

- **Don't transcribe copyrighted texts through the model**: the content filter cuts off extensive reproduction. The path is to find a native digital edition and extract/clean by script; targeted corrections can come from the model.
- Voice dictation (Web Speech API) doesn't exist in insecure contexts: over an IP it requires HTTPS.
- Chirp3-HD: no SSML, no per-word timestamps (hence the per-character interpolation for sentences that cross pages).

## Working style

- Specs arrive as `request*.md` files or messages with bug lists — attack the root cause, don't patch symptoms; verify the exact reported scenario before answering.
- UX references: e-readers (Kindle/Apple Books) and rounded floating inputs in the style of the Claude app.
- git: version only code/docs — `resources/` and lecture content (copyrighted texts, mp3s, PDFs) are gitignored. Keep it that way.
