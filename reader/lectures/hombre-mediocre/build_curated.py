#!/usr/bin/env python3
"""Builds curated.md for "La moral de los idealistas" (El hombre mediocre,
introduction) from source.api.json — the parse-API HTML of
https://es.wikisource.org/wiki/El_hombre_mediocre_(1913)/La_moral_de_los_idealistas
(the page transcludes a scan, so the raw wikitext has no text).

Author died in 1925; public domain. The 1913 spelling ("á", "ó") is kept —
the edition's orthography is part of the text; pronunciation fixes for the
TTS live in tts-overrides.json.
"""
import html as H
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

TITLE = "La moral de los idealistas"
BYLINE = ("José Ingenieros · El hombre mediocre · 1913. Introducción del ensayo, "
          "edición Renacimiento (Madrid); se conserva la ortografía de la época. "
          "Texto de dominio público, tomado de Wikisource.")

SECTIONS = re.compile(r"^([IVX]+)\.—\s*(.*?)\.?$")

def clean(x: str) -> str:
    x = re.sub(r"<sup\b.*?</sup>", "", x, flags=re.S)          # footnote markers
    x = re.sub(r"<span class=\"pagenum[^>]*>.*?</span>", "", x, flags=re.S)
    x = re.sub(r"<[^>]+>", "", x)
    x = H.unescape(x)
    return re.sub(r"\s+", " ", x).strip()

def main():
    doc = json.loads((HERE / "source.api.json").read_text(encoding="utf-8"))["parse"]["text"]
    blocks, seen_heading = [], False
    for m in re.finditer(r"<(h2|h3|h4|p)\b[^>]*>(.*?)</\1>", doc, flags=re.S):
        tag, inner = m.group(1), clean(m.group(2))
        if not inner:
            continue
        if tag in ("h2", "h3"):
            seen_heading = True                     # título y sumario: no van al cuerpo
            continue
        if tag == "h4":
            seen_heading = True
            s = SECTIONS.match(inner)
            blocks.append(f"## {s.group(1)}. {s.group(2)}" if s else f"## {inner}")
        elif seen_heading:                          # <p> del encabezado de edición: fuera
            blocks.append(inner)
    out = f"# {TITLE}\n\n> {BYLINE}\n\n" + "\n\n".join(blocks) + "\n"
    (HERE / "curated.md").write_text(out, encoding="utf-8")
    words = len(re.findall(r"\S+", " ".join(blocks)))
    print(f"curated.md: {len(blocks)} bloques · {words} palabras · {len(out)} chars")

if __name__ == "__main__":
    main()
