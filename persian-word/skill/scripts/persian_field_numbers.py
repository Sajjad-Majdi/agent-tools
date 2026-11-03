#!/usr/bin/env python3
"""Make PAGE and PAGEREF field numbers render as Persian digits.

Word has no Arabic-Indic page-number format, but the B fonts map ASCII 0-9 onto
Persian digit glyphs, so a field run set in `B Nazanin` prints ۲۳ and still
updates itself. Word rebuilds a field's result run from the formatting of its
code runs on every repagination, so every run from `fldChar begin` to
`fldChar end` has to carry the font, not just the one holding the digits.

Run this AFTER Word has updated the fields and saved, and export the PDF in a
second Word session that does not update fields.

    python persian_field_numbers.py report.docx
    python persian_field_numbers.py report.docx --font "B Zar" --dry-run
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import zipfile

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
PART_RE = re.compile(r"^word/(document|header\d+|footer\d+)\.xml$")


def set_latin_font(run, font):
    rpr = run.find(W + "rPr")
    if rpr is None:
        rpr = etree.Element(W + "rPr")
        run.insert(0, rpr)
    fonts = rpr.find(W + "rFonts")
    if fonts is None:
        fonts = etree.Element(W + "rFonts")
        after_style = len(rpr) and etree.QName(rpr[0]).localname == "rStyle"
        rpr.insert(1 if after_style else 0, fonts)
    fonts.set(W + "ascii", font)
    fonts.set(W + "hAnsi", font)


def patch_part(xml, font, codes):
    root = etree.fromstring(xml)
    hits = 0
    for p in root.iter(W + "p"):
        runs = list(p.iter(W + "r"))
        marks = []
        for run in runs:
            fld = run.find(W + "fldChar")
            marks.append((
                fld.get(W + "fldCharType") if fld is not None else None,
                "".join(t.text or "" for t in run.iter(W + "instrText")),
            ))
        for i, (_, instr) in enumerate(marks):
            if not any(c in instr for c in codes):
                continue
            start = i
            while start >= 0 and marks[start][0] != "begin":
                start -= 1
            end = i
            while end < len(marks) and marks[end][0] != "end":
                end += 1
            if start < 0 or end >= len(marks):
                continue
            for run in runs[start:end + 1]:
                set_latin_font(run, font)
            hits += 1
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8",
                          standalone=True), hits


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--font", default="B Nazanin")
    ap.add_argument("--codes", default="PAGE,PAGEREF",
                    help="field codes to patch, comma separated")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    codes = [c.strip() for c in args.codes.split(",") if c.strip()]
    with zipfile.ZipFile(args.docx) as zf:
        parts = {n: zf.read(n) for n in zf.namelist()}

    total = 0
    for name in list(parts):
        if not PART_RE.match(name):
            continue
        if not any(code.encode() in parts[name] for code in codes):
            continue
        parts[name], hits = patch_part(parts[name], args.font, codes)
        if hits:
            print(f"  {name}: {hits} field(s)")
        total += hits

    print(f"{total} field(s) set in {args.font}")
    if args.dry_run or not total:
        return
    if not args.no_backup:
        shutil.copyfile(args.docx, args.docx + ".bak")
    with zipfile.ZipFile(args.docx + ".tmp", "w", zipfile.ZIP_DEFLATED) as out:
        for name, data in parts.items():
            out.writestr(name, data)
    shutil.move(args.docx + ".tmp", args.docx)
    print("wrote", args.docx)


if __name__ == "__main__":
    main()
