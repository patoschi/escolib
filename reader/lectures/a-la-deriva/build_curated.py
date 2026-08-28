#!/usr/bin/env python3
"""Builds curated.md for "A la deriva" (Horacio Quiroga) from source.wiki.

Source: https://es.wikisource.org/wiki/A_la_deriva (public domain — the
author died in 1937). The wikitext is clean running prose; this script
strips the wiki markup and emits the reader's markdown format.
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

TITLE = "A la deriva"
BYLINE = ("Horacio Quiroga · Cuentos de amor, de locura y de muerte · 1917. "
          "Cuento. Publicado por primera vez en la revista Fray Mocho (1912). "
          "Texto de dominio público, tomado de Wikisource.")

# Wikisource typos, arbitrated against printed editions (exact, unique matches)
TYPOS = [
    ("y prestó oído en vano-. \n¡Compadre Alves!", "y prestó oído en vano—.\n\n—¡Compadre Alves!"),
]

def main():
    raw = (HERE / "source.wiki").read_text(encoding="utf-8")

    # drop templates, div wrappers, category links and the return-link footer
    raw = re.sub(r"\{\{Encabezado.*?\}\}\n", "", raw, flags=re.S)
    raw = re.sub(r"\{\{c\|.*?\}\}\n?", "", raw, flags=re.S)
    raw = re.sub(r"</?div[^>]*>\n?", "", raw)
    raw = re.sub(r"\[\[Categoría:[^\]]*\]\]\n?", "", raw)

    for old, new in TYPOS:
        assert raw.count(old) == 1, f"typo pattern not unique: {old[:40]!r}"
        raw = raw.replace(old, new)

    # flatten wiki inline markup: ''italics'' and [[target|label]] links
    raw = raw.replace("''", "")
    raw = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", raw)

    # paragraphs = blank-line blocks; single newlines inside a block are soft
    paras = [re.sub(r"\s*\n\s*", " ", p.strip())
             for p in re.split(r"\n\s*\n", raw) if p.strip()]

    out = f"# {TITLE}\n\n> {BYLINE}\n\n" + "\n\n".join(paras) + "\n"
    (HERE / "curated.md").write_text(out, encoding="utf-8")
    words = len(re.findall(r"\S+", " ".join(paras)))
    print(f"curated.md: {len(paras)} párrafos · {words} palabras · {len(out)} chars")

if __name__ == "__main__":
    main()
