# Gutenberg → MarkBreak (Sketch of a New Esthetic of Music)

## Source

| File | Role |
|------|------|
| `../31799-0.txt` | UTF-8 plain text |
| `../metadata.yaml` | → `meta.md` |
| `../cover.png` | Copied to `cover.png` |

## Shape

This title is a short continuous essay (not numbered chapters). Structure:

| File | Role |
|------|------|
| `book.md` | `toc` + spine |
| `meta.md` | publication record |
| `00-epigraph.md` | `epigraph` (opening verse) |
| `01-sketch.md` | `chapter` (full essay) |
| `99-colophon.md` | `colophon` |

Asterisk ornaments (`*       *       *`) become MarkBreak thematic pauses (`---` on their own line), not `//break page`.

## Steps

```powershell
python markbreak/_convert_gutenberg.py
pandoc markbreak/book.md -f markdown -t docx -L path/to/markbreak/tools/markbreak.lua -o busoni.docx
```

## Mapping

- Strip PG START/END and both Transcriber’s Note blocks.
- Opening dialogue + cite → `role: epigraph`.
- Remaining literary text → one `role: chapter`.
- Soft-wrapped paragraphs joined; `_italics_` → `*italics*`.
- Indented verse / footnotes → Markdown blockquotes.
