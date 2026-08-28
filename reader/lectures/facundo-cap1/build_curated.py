#!/usr/bin/env python3
"""Builds curated.md for Facundo, chapter I (Sarmiento) from source.wiki.

Source: https://es.wikisource.org/wiki/Facundo_(1874)/Capítulo_I — the 1874
Hachette edition with modernized spelling (author died in 1888; public
domain). The chapter subtitle becomes a ## section and the French epigraph
a blockquote.
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

TITLE = "Facundo — Capítulo I"
BYLINE = ("Domingo Faustino Sarmiento · Facundo. Civilización y barbarie · 1845. "
          "Capítulo I. Edición Hachette de 1874, de ortografía modernizada. "
          "Texto de dominio público, tomado de Wikisource.")

def main():
    raw = (HERE / "source.wiki").read_text(encoding="utf-8")

    raw = re.sub(r"\{\{encabezado.*?\}\}\n", "", raw, flags=re.S | re.I)
    raw = raw.replace("__NOEDITSECTION__\n", "")
    raw = re.sub(r"\[\[Categoría:[^\]]*\]\]\n?", "", raw)
    raw = re.sub(r"^== .*? ==$\n", "", raw, flags=re.M)          # "Capítulo I" (ya está en el título)

    # chapter subtitle === … === → ## section
    raw = re.sub(r"^=== (.*?)\.? ===$", r"## \1", raw, flags=re.M)

    # right-aligned French epigraph → blockquote (quote + attribution)
    def epigraph(m):
        inner = re.sub(r"<br\s*/?>", "\n", m.group(1))
        lines = [re.sub(r"<[^>]+>|''", "", l).strip() for l in inner.split("\n")]
        return "\n".join("> " + l for l in lines if l)
    raw = re.sub(r"<div style='text-align:right'>(.*?)</div>", epigraph, raw, flags=re.S)

    # flatten inline wiki markup
    raw = raw.replace("''", "")
    raw = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", raw)

    leftovers = re.findall(r"[{}<]|''|\[\[", raw)
    assert not leftovers, f"unhandled markup remains: {leftovers[:10]}"

    blocks = []
    for b in re.split(r"\n\s*\n", raw):
        t = b.strip()
        if not t:
            continue
        if t.startswith("## ") or t.startswith("> "):
            blocks.append(t)
        else:
            blocks.append(re.sub(r"\s*\n\s*", " ", t))

    out = f"# {TITLE}\n\n> {BYLINE}\n\n" + "\n\n".join(blocks) + "\n"
    (HERE / "curated.md").write_text(out, encoding="utf-8")
    words = len(re.findall(r"\S+", " ".join(b for b in blocks if not b.startswith(">"))))
    print(f"curated.md: {len(blocks)} bloques · {words} palabras · {len(out)} chars")

if __name__ == "__main__":
    main()
