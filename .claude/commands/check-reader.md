---
description: Verify reader/index.html after changes — syntax check plus headless flow checks
---

Verify the current state of `reader/index.html`. Focus (optional, from the user): $ARGUMENTS

1. **Syntax**: extract each `<script>` block of `reader/index.html` to a temp file and run `node --check` on it.
2. **Serve**: make sure `reader/serve.py` is running (`cd reader && python3 serve.py`); never use a plain static server (audio seeking needs Range requests).
3. **Headless flows**: drive headless Chrome (`--headless=new --remote-debugging-port=...`) via CDP — `Runtime.evaluate` with `awaitPromise:true` to simulate gestures and inspect state, `Page.captureScreenshot` for visual checks. Exercise at minimum:
   - page mode ON, and every note/narration check **on page ≥ 2** (page 1 hides coordinate bugs because `scrollLeft = 0`);
   - creating a highlight (double tap on a word) and reopening it;
   - if the test lecture has audio: sentence tap moves the playhead, follow mode brings the view along.
4. Report what was exercised and what wasn't (e.g. real touch gestures and iOS quirks can only be tested on-device).
