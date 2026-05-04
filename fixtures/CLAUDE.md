# fixtures/ Module

## Role

Static binary inputs used by tests in `tests/vision/` and
`tests/documents/`. Kept here so tests stay byte-deterministic — the
same prompt + same fixture = same input regardless of who runs the
test.

## Files

- **`red_4x4.png`** — 4×4 solid red PNG. Used by `test_image_base64`
  and `test_image_multi`. Small enough that base64-encoding the entire
  file is trivial; large enough that the model can describe the color.
- **`sample.pdf`** — small text PDF for `test_pdf_document` and
  `test_pdf_with_citations`. Embeds detectable text so citations can
  point at it.

## Rules

- **No PII or sensitive content.** These files may be embedded in
  matrix.json output and committed to source control.
- **Keep small.** Tests embed these inline as base64; large fixtures
  bloat token counts. Current fixtures are under 1 KB each.
- **Generate green PNG inline** in `tests/vision/test_image_multi.py`
  rather than as a fixture — keeps the multi-image test
  self-contained.
- **Adding a new fixture** → add an entry to the table above with one
  line on what test uses it.
