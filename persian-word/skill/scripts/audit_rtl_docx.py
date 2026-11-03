#!/usr/bin/env python3
"""Audit Persian DOCX files for explicit paragraph, run, and table RTL."""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
VAL = W + "val"


def enabled(node: ET.Element | None) -> bool:
    return node is not None and node.get(VAL, "1") not in {"0", "false", "off"}


def audit_part(name: str, root: ET.Element) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    counts = {"paragraphs": 0, "text_runs": 0, "tables": 0}

    for index, paragraph in enumerate(root.iter(W + "p"), start=1):
        counts["paragraphs"] += 1
        ppr = paragraph.find(W + "pPr")
        bidi = None if ppr is None else ppr.find(W + "bidi")
        jc = None if ppr is None else ppr.find(W + "jc")
        if not enabled(bidi):
            errors.append(f"{name}: paragraph {index} lacks w:bidi=1")
        if jc is None or jc.get(VAL) != "start":
            errors.append(f"{name}: paragraph {index} lacks w:jc=start")

        for run_index, run in enumerate(paragraph.iter(W + "r"), start=1):
            text = "".join(node.text or "" for node in run.iter(W + "t"))
            if not text:
                continue
            counts["text_runs"] += 1
            rpr = run.find(W + "rPr")
            rtl = None if rpr is None else rpr.find(W + "rtl")
            if not enabled(rtl):
                errors.append(
                    f"{name}: paragraph {index}, text run {run_index} lacks w:rtl=1"
                )

    for index, table in enumerate(root.iter(W + "tbl"), start=1):
        counts["tables"] += 1
        tblpr = table.find(W + "tblPr")
        bidi_visual = None if tblpr is None else tblpr.find(W + "bidiVisual")
        if not enabled(bidi_visual):
            errors.append(f"{name}: table {index} lacks w:bidiVisual=1")

    return errors, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path, help="DOCX file to audit")
    args = parser.parse_args()

    if not args.docx.is_file():
        parser.error(f"file not found: {args.docx}")

    all_errors: list[str] = []
    totals = {"paragraphs": 0, "text_runs": 0, "tables": 0}
    with zipfile.ZipFile(args.docx) as package:
        part_names = [
            name
            for name in package.namelist()
            if name == "word/document.xml"
            or name.startswith("word/header") and name.endswith(".xml")
            or name.startswith("word/footer") and name.endswith(".xml")
        ]
        for name in sorted(part_names):
            errors, counts = audit_part(name, ET.fromstring(package.read(name)))
            all_errors.extend(errors)
            for key, value in counts.items():
                totals[key] += value

    print(
        "RTL audit: "
        f"paragraphs={totals['paragraphs']} "
        f"text_runs={totals['text_runs']} tables={totals['tables']} "
        f"errors={len(all_errors)}"
    )
    if all_errors:
        for error in all_errors:
            print(f"ERROR: {error}")
        return 1

    print("PASS: explicit Persian RTL structure is complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
