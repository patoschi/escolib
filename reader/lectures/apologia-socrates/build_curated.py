#!/usr/bin/env python3
"""Builds curated.md for the Apología de Sócrates (Azcárate translation)
from source.api.json — the parse-API HTML of
https://es.wikisource.org/wiki/Apología_de_Sócrates_(de_Azcárate_tr.)
(the page transcludes a scan of Obras completas de Platón, tomo I, 1871).

The translator died in 1886; translation in the public domain. Curation:
footnote markers pruned (the notes are the editor's apparatus); the 1871
spelling ("á", "deliberacion") is kept — pronunciation fixes for the TTS
live in tts-overrides.json.
"""
import html as H
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

TITLE = "Apología de Sócrates"
BYLINE = ("Platón · Apología de Sócrates · 1871. Traducción de Patricio de Azcárate "
          "(Obras completas de Platón, tomo I, Madrid), con el argumento del traductor; "
          "se conserva la ortografía de la época. Texto de dominio público, tomado de Wikisource.")

HEADINGS = {
    "ARGUMENTO.": "## Argumento",
    "APOLOGÍA DE SÓCRATES.": "## Apología de Sócrates",
}

def clean(x: str) -> str:
    x = re.sub(r"<sup\b.*?</sup>", "", x, flags=re.S)          # footnote markers
    x = re.sub(r"<span class=\"pagenum[^>]*>.*?</span>", "", x, flags=re.S)
    x = re.sub(r"<[^>]+>", "", x)
    x = H.unescape(x)
    return re.sub(r"\s+", " ", x).strip()

def main():
    doc = json.loads((HERE / "source.api.json").read_text(encoding="utf-8"))["parse"]["text"]
    blocks, seen_heading = [], False
    for m in re.finditer(r"<(h2|p)\b[^>]*>(.*?)</\1>", doc, flags=re.S):
        tag, inner = m.group(1), clean(m.group(2))
        if not inner:
            continue
        if tag == "h2":
            seen_heading = True
            blocks.append(HEADINGS.get(inner, f"## {inner}"))
        elif seen_heading:                          # <p> del encabezado de edición: fuera
            blocks.append(inner)
    assert blocks and blocks[0] == "## Argumento", f"estructura inesperada: {blocks[:1]}"
    out = f"# {TITLE}\n\n> {BYLINE}\n\n" + "\n\n".join(blocks) + "\n"
    (HERE / "curated.md").write_text(out, encoding="utf-8")
    words = len(re.findall(r"\S+", " ".join(blocks)))
    print(f"curated.md: {len(blocks)} bloques · {words} palabras · {len(out)} chars")

if __name__ == "__main__":
    main()
