# Persian Word skill

A skill for creating and editing Persian Word files with correct right-to-left layout. It lays out tables, figures, captions
and Persian digits and checks the output with Word's own render. Written in Python.

## What it gives an agent

- The rules that make a Persian `.docx` really right-to-left: explicit bidi on every paragraph and run, `start`
  justification, right-to-left tables, section and page-break mechanics, fonts and complex-script sizes.
- How to keep Latin terms and digits correct inside Persian runs, how to give page numbers and table-of-contents numbers
  Persian digits, and how to justify body text without touching headings, tables or code.
- Scripts (in `skill/scripts/`):
  - `make_sample.py`: writes a tiny compliant document, a minimal example and a smoke test.
  - `audit_rtl_docx.py`: checks paragraphs, runs and tables for explicit right-to-left markup.
  - `docx_edit.py`: surgical edits of an existing `.docx` (find, replace, digits, insert, delete) with expected counts and a
    dry run.
  - `persian_field_numbers.py`: Persian digits for page numbers and table-of-contents numbers.
  - `render_docx.ps1`: renders the document to PDF through Microsoft Word without saving it.
  - `scan_pdf_pages.py`: finds blank and half-empty pages and builds contact sheets.
- Required verification steps, and how to verify a reference list against real sources.

## Requirements

Python 3.9+ with `python-docx`, `lxml`, `pymupdf` and `pillow`. Rendering to PDF needs Microsoft Word on Windows; everything
else works without it. Iranian academic documents usually use the "B" fonts (B Nazanin, B Titr), which you install yourself.

## Install prompt

```text
Install the "Persian Word skill" for me. It teaches AI agents to create and edit Persian Word (.docx) files with correct right-to-left layout and ships helper scripts to audit, edit and render them. Project: https://github.com/Sajjad-Majdi/agent-tools (folder persian-word).

Requirements: Python 3.9+ and pip. Microsoft Word on Windows is optional (only needed to render a PDF). Check them first and tell me what is missing instead of guessing.

Steps:
1. Download https://github.com/Sajjad-Majdi/agent-tools/archive/refs/heads/main.zip into a temp folder and extract it. Download nothing else without asking me. If github.com is blocked on my network, tell me and ask which mirror or proxy to use.
2. Install the Python packages: python -m pip install python-docx lxml pymupdf pillow (if PyPI is slow or blocked for me, ask for a mirror and use pip's -i option).
3. Install the skill: copy the contents of persian-word/skill (SKILL.md and the scripts folder) to <skills folder>\persian-word-documents\ for every one of these folders that exists: %USERPROFILE%\.claude\skills, %USERPROFILE%\.agents\skills, %USERPROFILE%\.codex\skills. If none exists, create %USERPROFILE%\.claude\skills and tell me which agents will see it.
4. Smoke test, in a scratch folder: run python <skill folder>\scripts\make_sample.py sample.docx and then python <skill folder>\scripts\audit_rtl_docx.py sample.docx. The audit must print PASS. Then run python <skill folder>\scripts\docx_edit.py list sample.docx, which must list three paragraphs and the table cells. Delete the scratch files afterwards.
5. Tell me which Persian fonts you found installed (for example B Nazanin, Vazirmatn) so I know what documents will use.

Safety: edit my documents in place only when I ask, and keep a backup copy first. Never let Word save a document you only render.
```

## Files

| Path | What |
|---|---|
| `skill/SKILL.md` | The skill |
| `skill/scripts/` | The helper scripts listed above |
