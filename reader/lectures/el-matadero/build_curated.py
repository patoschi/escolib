#!/usr/bin/env python3
"""Builds curated.md for "El matadero" (Esteban Echeverría) from source.wiki.

Source: https://es.wikisource.org/wiki/El_Matadero (public domain — the
author died in 1851; written c. 1839, published posthumously in 1871).
Strips the wiki markup and emits the reader's markdown format.
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

TITLE = "El matadero"
BYLINE = ("Esteban Echeverría · Relato · 1871. Escrito hacia 1839 y publicado "
          "póstumamente en la Revista del Río de la Plata. "
          "Texto de dominio público, tomado de Wikisource.")

def main():
    raw = (HERE / "source.wiki").read_text(encoding="utf-8")

    # drop templates, div wrappers and category links
    raw = re.sub(r"\{\{Encabezado.*?\n\}\}\n", "", raw, flags=re.S)
    raw = re.sub(r"\{\{c\|.*?\}\}\n?", "", raw, flags=re.S)
    raw = re.sub(r"</?div[^>]*>\n?", "", raw)
    raw = re.sub(r"\[\[Categoría:[^\]]*\]\]\n?", "", raw)

    # flatten wiki inline markup: ''italics'' and [[target|label]] links
    raw = raw.replace("''", "")
    raw = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", raw)

    leftovers = re.findall(r"[{}\[\]<>]|''", raw)
    assert not leftovers, f"unhandled markup remains: {leftovers[:10]}"

    # paragraphs = blank-line blocks; single newlines inside a block are soft
    paras = [re.sub(r"\s*\n\s*", " ", p.strip())
             for p in re.split(r"\n\s*\n", raw) if p.strip()]

    out = f"# {TITLE}\n\n> {BYLINE}\n\n" + "\n\n".join(paras) + "\n"
    (HERE / "curated.md").write_text(out, encoding="utf-8")
    words = len(re.findall(r"\S+", " ".join(paras)))
    print(f"curated.md: {len(paras)} párrafos · {words} palabras · {len(out)} chars")

if __name__ == "__main__":
    main()
