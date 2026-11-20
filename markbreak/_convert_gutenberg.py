#!/usr/bin/env python3
"""One-shot: Gutenberg 31799-0.txt -> MarkBreak spine under markbreak/."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "31799-0.txt"
OUT = Path(__file__).resolve().parent
COVER_SRC = ROOT / "cover.png"

ASTERISK_BREAK = re.compile(r"^\s*\*\s+\*\s+\*\s*$")


def yaml_quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def strip_pg_shell(text: str) -> str:
    start_m = re.search(r"\*\*\* START OF THIS PROJECT GUTENBERG EBOOK[^\n]*\*\*\*", text)
    if not start_m:
        raise SystemExit("missing Gutenberg START marker")
    end_m = re.search(r"\*\*\* END OF THIS PROJECT GUTENBERG EBOOK", text)
    if not end_m:
        raise SystemExit("missing Gutenberg END marker")
    return text[start_m.end() : end_m.start()]


def body_to_markdown(raw: str) -> str:
    raw = raw.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n")
    lines = [ln.rstrip() for ln in raw.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    paras: list[str] = []
    buf: list[str] = []
    verse: list[str] = []

    def flush_prose() -> None:
        nonlocal buf
        if not buf:
            return
        joined = " ".join(x.strip() for x in buf if x.strip())
        buf = []
        if not joined:
            return
        joined = re.sub(r"_([^_]+)_", r"*\1*", joined)
        paras.append(joined)

    def flush_verse() -> None:
        nonlocal verse
        if not verse:
            return
        block = "\n".join("".join(("    ", v.lstrip())) if v.strip() else "" for v in verse)
        # Prefer markdown blockquote for short verse, indented code-ish looks worse;
        # use lines starting with > for spoken/quoted verse blocks.
        q = []
        for v in verse:
            t = v.strip()
            if not t:
                q.append(">")
            else:
                t = re.sub(r"_([^_]+)_", r"*\1*", t)
                q.append(f"> {t}")
        paras.append("\n".join(q))
        verse = []

    for ln in lines:
        if ASTERISK_BREAK.match(ln):
            flush_verse()
            flush_prose()
            paras.append("---")
            continue
        # Indented verse / quotation (4+ spaces or leading spaces with quote content)
        if ln.startswith("    ") or (ln.startswith("  ") and not ln.startswith("   [")):
            flush_prose()
            verse.append(ln)
            continue
        if verse:
            flush_verse()
        if not ln.strip():
            flush_prose()
            continue
        buf.append(ln)
    flush_verse()
    flush_prose()
    return "\n\n".join(paras).strip() + "\n"


def main() -> None:
    text = strip_pg_shell(SRC.read_text(encoding="utf-8"))
    # Drop leading transcriber note block
    text = re.sub(
        r"^\s*\[\s*Transcriber's Note:.*?\]\s*",
        "",
        text,
        count=1,
        flags=re.S,
    )

    # Literary title marker (ALL CAPS line)
    m = re.search(r"^SKETCH OF A NEW ESTHETIC OF MUSIC\s*$", text, re.M)
    if not m:
        raise SystemExit("title line not found")
    literary = text[m.end() :]

    # Cut trailing transcriber corrections note
    cut = re.search(r"\[\s*Transcriber's Note:", literary)
    if cut:
        literary = literary[: cut.start()]

    lines = literary.split("\n")
    # Epigraph: quoted dialogue until blank line then prose starting LOOSELY / or first para
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    epi_lines: list[str] = []
    while i < len(lines):
        s = lines[i].strip()
        # End epigraph when main prose begins (not indented, not empty, not cite)
        if (
            s
            and not lines[i].startswith(" ")
            and not s.startswith('"')
            and not s.startswith("[")
            and not s.startswith("'")
            and s.upper() != s  # not all-caps title remnant
        ):
            # Main essay typically starts with LOOSELY or similar
            break
        epi_lines.append(lines[i])
        i += 1
    while epi_lines and not epi_lines[0].strip():
        epi_lines.pop(0)
    while epi_lines and not epi_lines[-1].strip():
        epi_lines.pop()

    body_lines = lines[i:]
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)

    epigraph_md = body_to_markdown("\n".join(epi_lines))
    body_md = body_to_markdown("\n".join(body_lines))

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.md"):
        if old.name == "CONVERSION.md":
            continue
        old.unlink()

    (OUT / "meta.md").write_text(
        """\
---
title: "Sketch of a New Esthetic of Music"
author: "Ferruccio Busoni"
language: en
publisher: "Project Gutenberg"
---

Translated from the German by Theodore Baker.
Public domain in the USA (Project Gutenberg EBook #31799).
Original English edition: G. Schirmer, New York, 1911.
""",
        encoding="utf-8",
    )

    (OUT / "00-epigraph.md").write_text(
        f"""\
---
title: "Epigraph"
role: epigraph
---

# Epigraph

{epigraph_md}
""",
        encoding="utf-8",
    )

    (OUT / "01-sketch.md").write_text(
        f"""\
---
title: {yaml_quote("Sketch of a New Esthetic of Music")}
role: chapter
---

# Sketch of a New Esthetic of Music

{body_md}
""",
        encoding="utf-8",
    )

    (OUT / "99-colophon.md").write_text(
        """\
---
title: "Colophon"
role: colophon
---

# Colophon

This MarkBreak edition is converted from Project Gutenberg EBook #31799,
*Sketch of a New Esthetic of Music* by Ferruccio Busoni, translated by Theodore Baker.
Public domain in the USA.

Source repository: https://github.com/13-Books/Sketch-of-a-New-Esthetic-of-Music_31799  
Gutenberg: https://www.gutenberg.org/ebooks/31799
""",
        encoding="utf-8",
    )

    (OUT / "book.md").write_text(
        """\
---
role: toc
meta: meta.md
spine:
  - { file: "00-epigraph.md", role: epigraph }
  - { file: "01-sketch.md", role: chapter }
  - { file: "99-colophon.md", role: colophon }
---

# Sketch of a New Esthetic of Music

Ferruccio Busoni (English translation by Theodore Baker, 1911). MarkBreak spine.
""",
        encoding="utf-8",
    )

    if COVER_SRC.exists():
        shutil.copy2(COVER_SRC, OUT / "cover.png")

    print(f"Wrote MarkBreak tree under {OUT}")
    for p in sorted(OUT.iterdir()):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
