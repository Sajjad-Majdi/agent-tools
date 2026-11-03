---
name: persian-word-documents
description: Create, edit, and verify Persian `.docx` and Microsoft Word documents with real right-to-left paragraphs, right-aligned text, RTL tables, clean diagrams, and Word-rendered visual QA. Use whenever a Word deliverable is mainly Persian or the user asks for correct Persian Word layout.
---

# Persian Word Documents

Use this skill together with any general document-creation skill or library (python-docx, docx-js). Follow the general document workflow, then apply the Persian-specific rules below. The helper scripts live in `scripts/` next to this file: `audit_rtl_docx.py`, `docx_edit.py`, `persian_field_numbers.py`, `render_docx.ps1`, `scan_pdf_pages.py`, and `make_sample.py` (a minimal compliant example that doubles as a smoke test).

## RTL invariants

- Apply RTL explicitly to every paragraph, including titles, headings, body text, table cells, headers, footers, image-anchor paragraphs, empty paragraphs, and page-break paragraphs.
- Set `w:bidi w:val="1"` on every paragraph.
- Set paragraph justification to `w:jc w:val="start"`. In a bidirectional Word paragraph this produces visual right alignment. Do not rely only on a library's `RIGHT` enum; Microsoft Word can display `w:jc="right"` on the left when the paragraph is bidirectional.
- Set `w:rtl w:val="1"` on every text run. Set the document language to `fa-IR` and use a readable installed Persian font.
- Do not use section-level `w:bidi` as a substitute for paragraph and table direction. Add it only when the page layout itself requires mirroring and verify the result in Word.

## Genuinely left-to-right content is the exception

Some blocks inside a Persian document are not Persian text and must not be bidi. Set `w:bidi w:val="0"` on the paragraph and `w:rtl w:val="0"` on its runs for:

- Latin bibliography entries in a reference list.
- Code listings and command lines.
- An English title page, abstract, or appendix.

Forcing RTL on these produces four specific, easy-to-miss defects: Latin digits render as Persian ones (`2022` becomes `۲۰۲۲`, and `arXiv:2110.13900` becomes unusable), a trailing period or comma jumps to the opposite end of the line, a trailing bracket or parenthesis moves to the front (`config(` renders as `)config`), and code indentation collapses. Keep leading spaces by setting `xml:space="preserve"` on the `w:t` node.

A Persian-digit label such as `[۷]` still renders correctly at the left of an LTR reference line, so in-text citations and the reference list can share one numbering style.

## RTL tables

- Set `w:bidiVisual w:val="1"` on every table and align the table to the right.
- Put the logical label or key column first so it appears as the rightmost visual column.
- Right-align all header and body cell paragraphs. Keep labels on the right in the rendered document.
- Set `w:cantSplit` on every row and `w:tblHeader` on the first row, so a row is never cut in half and a table that spans pages repeats its header.
- Inspect the rendered table. XML direction alone is not enough.

## Page and section mechanics

- A paragraph carrying `w:br w:type="page"` keeps its own paragraph mark on the page it leaves. On a full page that mark is pushed forward and produces an extra blank page. For fixed layouts such as a cover, a bismillah page, or a mandated blank verso, use an empty carrier paragraph with `w:pageBreakBefore` instead.
- `python-docx`'s `add_section` copies the previous `w:sectPr`. A `w:pgNumType w:start` set once is therefore inherited by every later section and silently restarts numbering. Strip `w:pgNumType` on each new section and re-add it only where a restart is intended.
- For a chapter that must begin on an odd page, use a section break of type `oddPage` with `titlePg`, an empty first-page header, and a centred page number in the first-page footer.

## Fonts

- For Iranian academic documents prefer `B Nazanin` for body text and `B Titr` for headings (the "B" font family, installed by the user, for example under `%LOCALAPPDATA%\Microsoft\Windows\Fonts`). Tahoma reads as an unstyled default and a supervisor will ask for it to be changed. Check which Persian fonts are installed before choosing.
- Set the Persian face through `w:rFonts w:cs` and the Latin face through `w:ascii` and `w:hAnsi`, and always set `w:szCs` alongside `w:sz`; complex-script size is a separate property and text stays at the default size without it.

## Diagrams and figures

- Build diagrams with complete, continuous connectors. Make each arrow touch its source path and target box.
- Prefer a single rendered diagram image when Word shapes or connectors can break during layout.
- For an RTL process flow, place the user-facing entry on the right and move the flow toward processing and storage on the left unless the content requires another direction.
- In matplotlib, pass raw Persian strings. Recent versions shape and reorder Arabic script themselves, so `arabic_reshaper` plus `python-bidi` double-processes the text into disconnected mirrored glyphs. Register the font with `font_manager.addfont` and give `fontfamily` a list such as `["B Nazanin", "Segoe UI"]`, including in `legend(prop=...)`, because the B-family fonts contain no Latin glyphs and a single-family setting renders Latin words as empty boxes.
- Put a Latin face with no Arabic coverage first in every matplotlib family list: `["Cambria", "B Nazanin", "Segoe UI"]`. Fallback is per character, so Latin letters and ASCII digits take the Latin face while Persian letters fall through to the B font, and text written with the Persian digits `۰-۹` is unaffected. `Times New Roman` and `Segoe UI` are the wrong choice for this slot; both cover Arabic and would capture the Persian text too.
- Write `ه` on its own. `ه` followed by U+0654 (the `هٔ` ezafe) renders as a broken glyph in the B fonts. Word's own text can carry it, but a figure cannot.
- A fixed-size box does not fit a two-line Persian label at the nominal size. Measure the drawn text with `get_window_extent`, convert to data coordinates, and shrink the font until it fits; the alternative is a caption sitting on or over the box border.
- Give free-floating labels a white `bbox`. A dashed band border or a connector otherwise runs straight through the words.
- When a template supplies its logo as an EMF, `python-docx` cannot embed it. Render the template's PDF cover and crop the logo to PNG instead.

## Titles and headers

- Show the document title once on the first page. Do not repeat the same title in the first-page header.
- Use a distinct first-page header or leave all running headers empty when they add no value.
- A section number written as `۲-۵-۳` is correct as typed. Word's bidi ordering renders it with `۲` on the right, which is what a Persian reader expects. Do not reverse it manually.

## Driving Microsoft Word from PowerShell

- Never write a Persian path as a literal inside a `.ps1` file. Windows PowerShell 5.1 reads the script as ANSI and the path becomes mojibake. Locate the file with `Get-ChildItem -LiteralPath $dir -Filter *.docx` instead.
- Delete any leftover `~$` lock file before opening, otherwise `Documents.Open` fails with a COM exception.
- Update fields twice around `TablesOfContents.Update()` so a table of contents, list of figures, and list of tables all resolve, then call `Repaginate()` before reading `ComputeStatistics(2)` for the page count.
- **Do not let Word save the DOCX.** Open it, update fields, export the PDF, and close with `SaveChanges = $false`. See the next section for why.
- Open with `ReadOnly = $false` even when only reading. With `Documents.Open($path, $false, $true)` the document opens and paginates normally but `ExportAsFixedFormat` never returns; it spins for as long as you let it, on a one-paragraph document as readily as on a long one.
- `SaveAs2` hangs the same way. When a document really must be written back, open the copy you intend to keep and call `Save()` on it, which returns in about a second.
- Force-killing a hung `WINWORD` leaves an entry under `HKCU:\Software\Microsoft\Office.0\Word\Resiliency\DocumentRecovery` for every abandoned document. Read those entries before clearing any; each one holds an unsaved copy of some document, which may belong to the user rather than to you.
- Updating a table of contents is the one case where Word must save. Sequence it as: edit the XML, copy the file to the name you want to keep, open that copy read-write, update fields, update each `TablesOfContents` item, update fields again, `Save()`, close. Then render the PDF in a separate run.

## Work in batches, not one change at a time

A full build plus a Word render is the slow step. Everything else should be
arranged so that step runs as few times as possible.

- Generate every figure in one process run. Splitting them across several
  scripts pays the font-registration and matplotlib start-up cost again each
  time and gives no benefit.
- Collect all layout defects first, then rebuild once. Fixing a cover overflow,
  rebuilding, spotting the next line to drop, rebuilding again turns one build
  into five. Render, scan every page, write the full list, then edit.
- Put the audit, the page scan, the page count and the file sizes in a single
  command. They are independent reads of the same output.
- Once the document is final, do not rebuild it for a small change. Edit it in
  place with `scripts/docx_edit.py` and batch the edits into one ops file.
- Independent shell commands belong in one call. So do independent file reads.

## Editing an existing document instead of rebuilding it

Rebuilding the whole document to change a number or add a sentence is slow and
re-runs every risk you already retired. For a small, targeted change edit the
`.docx` in place with `scripts/docx_edit.py`, the way you would edit source code.

- Word splits one paragraph's text across many `w:t` runs, so a plain
  search-and-replace on `document.xml` silently misses most phrases. The script
  joins each paragraph's own text nodes, matches on the joined string, and writes
  back only into the runs the match covers.
- Locate first: `docx_edit.py list file.docx --grep "..."` prints paragraph
  indexes, and `find` prints each match with context.
- Then put every change in one JSON ops file and apply it in a single call.
  `replace`, `digits`, `insert_after`, `insert_before` and `delete_para` can be
  mixed, scoped by `where` (a regex over the paragraph) or `para` (an index).
- Give each op an `expect` count. The script applies nothing at all if any op
  matches a different number of times than expected, which turns a silent wrong
  edit into a failed run. Confirm with `--dry-run` before writing.
- Figures can be replaced without rebuilding: the images live at `word/media/imageN.png`, and the N-th inline shape maps to the N-th figure in document order. Regenerate the PNGs, then swap those parts in the archive. Word stores each drawing's extent in the XML, so paste a new image of a different pixel size onto a white canvas of the old size instead of letting it stretch.
- Keep the generator authoritative. Fold anything you want to survive the next
  full build back into the Python source; treat in-place edits as a fast path,
  not as a second source of truth.
- Re-render after editing. A structurally valid archive is not proof of correct
  layout, and an insert can push a page.

## Latin digits inside a Persian run

The B-family fonts map ASCII `0-9` to Persian digit glyphs. Any text drawn in
`B Nazanin` therefore shows `Gemma 4 E4B` as `Gemma ۴ E۴B`, in Word and in
matplotlib alike. It looks like numeral substitution but it is font coverage, so
the fix is always to hand those characters to a Latin face.

In Word the complex-script face applies to a run marked `w:rtl="1"`, and the
`w:ascii` face applies to one marked `w:rtl="0"`. When a number must stay Latin,
put it in its own run with `w:rtl w:val="0"`. `docx_edit.py`
does this with `"ltr": true`, which is the default for a `digits` op converting
to Latin.

This affects every mixed term: `Gemma 4`, `E4B`, `Tesla T4`, `fp16`, `L3`.
`{"op": "ltr_terms", "bidi": true}` sweeps a whole document for them. It matches
a run of Latin and digit tokens that contains at least one letter and at least
one digit, converts any Persian digits inside it to Latin, and moves the whole
term into one non-RTL run. It never swallows a trailing sentence period, and
`bidi: true` keeps it away from reference lists and code blocks, which are
already left-to-right. Preview the term list before applying; every match should
be a real technical term.

Leave the run's `w:rFonts` alone when splitting. Forcing a Latin face would turn
a code listing's Consolas into Times New Roman; with `w:rtl="0"` Word already
uses the run's `w:ascii` face.

## Persian page numbers, and the field-run trap

Word cannot format page numbers as Persian digits: `w:pgNumType` offers Hindi and
Thai but nothing Arabic-Indic. Use the font instead. Because the B fonts map ASCII
`0-9` to Persian digit glyphs, a `PAGE` field whose run carries
`w:rFonts w:ascii="B Nazanin" w:hAnsi="B Nazanin"` prints `۲۳` and still updates
itself.

Patch every run of the field, from `fldChar begin` to `fldChar end`, not only the
run holding the digits. Word rebuilds a field's result run from the formatting of
its code runs whenever it repaginates, so a patch on the result run alone is
silently thrown away at export. `scripts/persian_field_numbers.py` does this for
`PAGE` in every header and footer and for every `PAGEREF` in the table of contents,
the list of figures and the list of tables.

Order matters, because the tool and Word undo each other:

1. edit the XML;
2. one Word session updates fields and the TOC, then saves;
3. run `persian_field_numbers.py`;
4. a second Word session exports the PDF **without** updating fields.

`render_docx.ps1` updates fields, so it cannot be the last step; use a plain
`Open` + `ExportAsFixedFormat` script instead. Warn the user that updating fields
in Word later reverts the TOC numbers, and that re-running the script fixes them.

## Justifying a Persian document

`w:jc w:val="both"` is what a supervisor means by "تراز از دو طرف". Add it to body
paragraphs only: skip anything already centred, anything inside a table, headings,
TOC entries, and code listings, whose lines would otherwise be stretched. Code
blocks are easy to spot by their monospace `w:rFonts`. In the generator, pass
`align="both"` from the body-paragraph helper rather than setting it per call.

## Verify a reference list before calling it done

A bibliography written from memory looks right and is not. Check it with a script,
not by reading it: batch the arXiv ids through
`export.arxiv.org/api/query?id_list=` twenty at a time and compare title and first
author, send older venue papers to `api.crossref.org/works?query.bibliographic=`,
and resolve model and dataset cards through `huggingface.co/api/models/<id>` and
`huggingface.co/api/datasets/<id>` (a 401 there means gated, not missing). Python's
default SSL store may fail behind a corporate proxy; pass `certifi.where()`.

Expect the failures to be a wrong author initial, an invented title for a real
paper, and a plausible-sounding technical report that was never published. Replace
an unverifiable citation with something that resolves, such as an official model
page with an access date, rather than leaving it in.

## Required verification

1. Build the DOCX with the generator, then run `scripts/audit_rtl_docx.py` on **that** file, before Word has ever opened it.
2. Render the same DOCX to PDF through Word without saving it: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/render_docx.ps1 -Dir "<folder>"`. It clears stale `~$` locks, updates fields and the tables of contents, prints the page and word count, and exports the PDF.
3. Scan the rendered pages with `scripts/scan_pdf_pages.py`. Running it on the PDF lists blank pages and pages whose content ends far above the bottom margin, which catches orphaned figures, split tables, and stray blank pages far faster than looking at every page. Use `--sheets DIR` for low-resolution contact sheets and `--page N --dpi 130 --out p.png` to re-render a suspect page at readable resolution.
4. Cross-check numbering programmatically: every `شکل n-m` and `جدول n-m` referenced in the text must have a caption, with no duplicates and no gaps.
5. After an in-place edit with `scripts/docx_edit.py`, re-render and re-scan. The
   edit does not change styles, so the RTL audit result should be unchanged.
6. Open or render the exact final copy after copying or renaming it. Do not assume a structurally valid DOCX is visually correct.

### Reading the audit output

Word strips direct formatting that duplicates the paragraph style. If the `Normal` style already sets `w:bidi` and `w:jc`, a file that audited clean before Word touched it will report thousands of findings after Word saves it, while rendering identically. This is the reason step 1 audits the generator's own output and step 2 forbids saving.

Zero findings is also the wrong target. Every centred paragraph is reported as a missing `w:jc="start"`, and centring is correct for figure captions, table captions, cover pages, formulas, table cells, and footer page numbers. Group the findings by cause, confirm each group is deliberate, and report the count with its explanation rather than editing correct layout to satisfy the script.

Treat the rendered Word output as the final truth. A DOCX that only looks correct in generated XML is not verified.

## Undoing a user's font-size change

Word's Shrink Font walks a fixed ladder — 8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24,
26, 28, 36, 48, 72 — so a document a user shrank by one step is restored by moving
every explicit `w:sz` and `w:szCs` up to the next value on that ladder. Do it on
`word/document.xml` only: Ctrl+A never selects headers and footers, so theirs were
never changed. Sizes off the ladder do not survive the round trip (11.5 shrinks to
11 and grows back to 12), which is usually acceptable but should be said out loud.

## Setup

`python -m pip install python-docx lxml pymupdf pillow`. Rendering to PDF needs Microsoft Word on Windows (`render_docx.ps1` drives it through COM); everything else works without Word. Smoke test: `python scripts/make_sample.py sample.docx` then `python scripts/audit_rtl_docx.py sample.docx` must print `PASS`.
