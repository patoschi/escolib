#!/usr/bin/env python3
"""Generates TTS narration (GCP Chirp3-HD) for a reader lecture.

Usage:  python3 narrate.py <lecture-folder> [--file curated.md] [--dry-run]

Reads <folder>/curated.md, splits it into blocks (title / headings / paragraphs)
and sentences, applies spoken-form transformations (generic rules +
<folder>/tts-overrides.json), synthesizes each sentence separately (cached in
<folder>/build/ by text+voice hash), concatenates the PCM inserting silences
and emits:
  <folder>/audio.mp3        (CBR 64k mono)
  <folder>/timeline.json    (turns → sentences with exact ms offsets)

The text of each sentence in the timeline is the DISPLAY TEXT (exactly as
index.html renders it); the spoken form is only used for synthesis.
"""
import argparse, base64, hashlib, io, json, os, re, struct, subprocess, sys, time, wave
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

VOICE = {"languageCode": "es-US", "name": "es-US-Chirp3-HD-Iapetus"}
SAMPLE_RATE = 24000
ENDPOINT = "https://texttospeech.googleapis.com/v1/text:synthesize"
# billing project: taken from the environment, never hardcoded
GCP_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT") or ""
MAX_BYTES = 4500          # margin below the API's 5000-byte limit

# silences (ms)
LEAD = 250                # before everything
GAP_SENT = 160            # between sentences of the same block
GAP_BLOCK = 700           # between blocks (paragraphs)
GAP_HEADING = 850         # after a title or heading
GAP_PART = 110            # between sub-parts of a long sentence
TAIL = 500                # at the end

# Chirp3-HD rejects very long individual sentences ("sentences that are
# too long"): long spoken forms are split into sub-parts at strong
# punctuation and synthesized separately (the timeline never sees this).
PART_LIMIT = 380

def split_spoken(s: str, limit: int = PART_LIMIT):
    if len(s) <= limit:
        return [s]
    head = s[:limit]
    cut = -1
    for sep in ("; ", " —", "— ", ", "):
        i = head.rfind(sep)
        if i > 40:
            cut = i + len(sep)
            break
    if cut <= 0:
        cut = max(head.rfind(" "), limit)
    first, rest = s[:cut].rstrip(), s[cut:].lstrip()
    return [first] + split_spoken(rest, limit) if rest else [first]

# ---------- markdown parsing ----------

def parse_blocks(md: str):
    """Blocks as renderDoc() sees them: title, first '>' (byline, not
    narrated), '##' headings and paragraphs."""
    out = []
    first_bq = True
    for b in re.split(r"\n\s*\n", md):
        t = b.strip()
        if not t:
            continue
        if t.startswith("# ") and not t.startswith("## "):
            out.append(("title", t[2:].strip()))
        elif t.startswith("> ") and first_bq:
            first_bq = False            # byline: not narrated
        elif t.startswith("> "):
            # blockquote: the reader preserves internal line breaks,
            # so each verse/line is its own timeline "sentence"
            out.append(("quote", [re.sub(r"^>\s?", "", x).strip()
                                  for x in t.split("\n") if x.strip()]))
        elif t.startswith("## "):
            out.append(("heading", t[3:].strip()))
        else:
            out.append(("p", t))
    return out

ABBREV_SKIP = re.compile(r"(?:^|[\s(“])[A-ZÁÉÍÓÚÑ]\.$")   # initial: "K." "F."

def split_sentences(text: str):
    """Split at sentence end: [.!?…] + closing quotes/parens + space +
    sentence opener. Protects initials like "K. Jaspers"."""
    sents, start = [], 0
    for m in re.finditer(r"[.!?…][”)»]*\s+", text):
        end = m.end()
        nxt = text[end:end + 1]
        if not nxt or nxt not in "ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ¿¡“(«—0123456789":
            continue
        core = text[start:m.start() + 1]           # up to and including the mark
        if ABBREV_SKIP.search(core.rstrip("”)»").rstrip()):
            continue
        if len(core.strip()) <= 8:                 # "1.", "§ 4.": joins the next one
            continue
        sents.append(text[start:end].rstrip())
        start = end
    tail = text[start:].strip()
    if tail:
        sents.append(tail)
    return sents

# ---------- spoken form ----------

def load_overrides(folder: Path):
    p = folder / "tts-overrides.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"sentence_overrides": [], "substrings": [], "regex": []}

def spoken_form(display: str, ov) -> str:
    for o in ov.get("sentence_overrides", []):
        if display.strip() == o["match"]:
            return o["spoken"]
    s = display
    for old, new in ov.get("substrings", []):
        s = s.replace(old, new)
    for pat, rep in ov.get("regex", []):
        s = re.sub(pat, rep, s)
    return s

# ---------- synthesis ----------

def get_token():
    global GCP_PROJECT
    if not GCP_PROJECT:
        r = subprocess.run(["gcloud", "config", "get-value", "project"],
                           capture_output=True, text=True)
        GCP_PROJECT = (r.stdout or "").strip()
    if not GCP_PROJECT or GCP_PROJECT == "(unset)":
        sys.exit("definí GOOGLE_CLOUD_PROJECT o corré `gcloud config set project <id>`")
    for cmd in (["gcloud", "auth", "application-default", "print-access-token"],
                ["gcloud", "auth", "print-access-token"]):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    sys.exit("no pude obtener token de gcloud")

def synth(text: str, token: str) -> bytes:
    """Returns WAV (LINEAR16). Retries on 429/5xx."""
    import urllib.request, urllib.error
    body = json.dumps({
        "input": {"text": text},
        "voice": VOICE,
        "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": SAMPLE_RATE},
    }).encode()
    req = urllib.request.Request(ENDPOINT, data=body, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "x-goog-user-project": GCP_PROJECT,
        "Content-Type": "application/json",
    })
    delay = 2.0
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return base64.b64decode(json.loads(r.read())["audioContent"])
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 5:
                time.sleep(delay); delay *= 1.8; continue
            raise RuntimeError(f"TTS {e.code}: {e.read()[:300]} :: {text[:80]}")
        except (urllib.error.URLError, TimeoutError, OSError):
            # transient network errors (SSL EOF, timeouts, connection)
            if attempt < 5:
                time.sleep(delay); delay *= 1.8; continue
            raise
    raise RuntimeError("agotados los reintentos")

def pcm_of_wav(data: bytes) -> bytes:
    with wave.open(io.BytesIO(data)) as w:
        assert w.getframerate() == SAMPLE_RATE and w.getnchannels() == 1 and w.getsampwidth() == 2, \
            f"formato inesperado: {w.getframerate()}Hz ch={w.getnchannels()}"
        return w.readframes(w.getnframes())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--file", default="curated.md")
    ap.add_argument("--dry-run", action="store_true", help="only list sentences and spoken forms")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    folder = Path(args.folder).resolve()
    md = (folder / args.file).read_text(encoding="utf-8")
    ov = load_overrides(folder)
    blocks = parse_blocks(md)

    # plan: [{kind, sentences: [{display, spoken}]}]
    plan = []
    for kind, text in blocks:
        if kind in ("title", "heading"):
            sents = [text]
        elif kind == "quote":
            sents = text
        else:
            sents = split_sentences(text)
        items = []
        for s in sents:
            sp = spoken_form(s, ov)
            items.append({"display": s, "parts": split_spoken(sp)})
        plan.append({"kind": kind, "sentences": items})

    n_sents = sum(len(b["sentences"]) for b in plan)
    n_parts = sum(len(s["parts"]) for b in plan for s in b["sentences"])
    n_chars = sum(len(p) for b in plan for s in b["sentences"] for p in s["parts"])
    print(f"bloques: {len(plan)} · oraciones: {n_sents} · requests: {n_parts} · caracteres: {n_chars}")

    if args.dry_run:
        for b in plan:
            print(f"\n[{b['kind']}]")
            for s in b["sentences"]:
                joined = " ".join(s["parts"])
                mark = "  ≠ " if joined != s["display"] else "    "
                extra = f"  [{len(s['parts'])} partes]" if len(s["parts"]) > 1 else ""
                print(f"{mark}{joined[:110]}{extra}")
        return

    build = folder / "build"; build.mkdir(exist_ok=True)
    token = get_token()

    def key(spoken):
        return hashlib.sha1(f"{VOICE['name']}|{SAMPLE_RATE}|{spoken}".encode()).hexdigest()

    todo = {}
    for b in plan:
        for s in b["sentences"]:
            s["keys"] = [key(p) for p in s["parts"]]
            for k, p in zip(s["keys"], s["parts"]):
                if not (build / f"{k}.wav").exists():
                    todo[k] = p
    print(f"a sintetizar: {len(todo)} (cache: {n_parts - len(todo)})")

    if todo:
        done = 0
        with ThreadPoolExecutor(args.workers) as ex:
            futs = {ex.submit(synth, txt, token): k for k, txt in todo.items()}
            for f in as_completed(futs):
                (build / f"{futs[f]}.wav").write_bytes(f.result())
                done += 1
                if done % 25 == 0 or done == len(todo):
                    print(f"  {done}/{len(todo)}")

    # sample-exact assembly
    bpms = SAMPLE_RATE * 2 // 1000                    # bytes per ms (16-bit mono)
    sil = lambda ms: b"\x00" * (ms * bpms)
    pcm = bytearray(sil(LEAD))
    cursor = LEAD
    turns = []
    for i, b in enumerate(plan):
        t0 = cursor
        sent_out = []
        for j, s in enumerate(b["sentences"]):
            if j > 0:
                pcm += sil(GAP_SENT); cursor += GAP_SENT
            s0 = cursor
            for pi, k in enumerate(s["keys"]):
                if pi > 0:
                    pcm += sil(GAP_PART); cursor += GAP_PART
                chunk = pcm_of_wav((build / f"{k}.wav").read_bytes())
                pcm += chunk; cursor += len(chunk) // bpms
            sent_out.append({"text": s["display"], "start_ms": s0, "end_ms": cursor})
        turns.append({"i": i, "kind": b["kind"], "start_ms": t0, "end_ms": cursor, "sentences": sent_out})
        gap = GAP_HEADING if b["kind"] in ("title", "heading") else GAP_BLOCK
        if i < len(plan) - 1:
            pcm += sil(gap); cursor += gap
    pcm += sil(TAIL); cursor += TAIL

    wav_path = build / "_full.wav"
    with wave.open(str(wav_path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SAMPLE_RATE)
        w.writeframes(bytes(pcm))
    mp3 = folder / "audio.mp3"
    # 64k CBR mono: transparent for speech, and half the size — mp3s are
    # heavy artifacts (they are not committed; the demo deploys them apart)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav_path),
                    "-codec:a", "libmp3lame", "-b:a", "64k", "-ac", "1", str(mp3)], check=True)

    timeline = {
        "schema": "audiolib/narration@1",
        "slug": folder.name,
        "source": args.file,
        "engine": "gcp",
        "voice": VOICE["name"],
        "audio": "audio.mp3",
        "sample_rate": SAMPLE_RATE,
        "total_ms": cursor,
        "gaps_ms": {"sentence": GAP_SENT, "block": GAP_BLOCK, "heading": GAP_HEADING, "lead": LEAD},
        "turns": turns,
    }
    (folder / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False), encoding="utf-8")
    mins = cursor / 60000
    print(f"listo: {mp3.name} ({mins:.1f} min) · timeline.json ({len(turns)} turns, {n_sents} oraciones)")

if __name__ == "__main__":
    main()
