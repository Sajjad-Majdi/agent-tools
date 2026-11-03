#!/usr/bin/env python3
"""Writes a tiny Persian .docx whose paragraphs, runs and table carry explicit RTL markup.

Use it as a smoke test (audit_rtl_docx.py must print PASS) and as a minimal example of the invariants in SKILL.md.

    python make_sample.py sample.docx
    python audit_rtl_docx.py sample.docx
"""
import sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt


def rtl_paragraph(p):
    ppr = p._p.get_or_add_pPr()
    for tag, val in (("w:bidi", "1"), ("w:jc", "start")):
        el = ppr.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            ppr.append(el)
        el.set(qn("w:val"), val)
    for run in p.runs:
        rpr = run._r.get_or_add_rPr()
        rtl = rpr.find(qn("w:rtl"))
        if rtl is None:
            rtl = OxmlElement("w:rtl")
            rpr.append(rtl)
        rtl.set(qn("w:val"), "1")
        fonts = rpr.find(qn("w:rFonts"))
        if fonts is None:
            fonts = OxmlElement("w:rFonts")
            rpr.insert(0, fonts)
        fonts.set(qn("w:cs"), "B Nazanin")
        fonts.set(qn("w:ascii"), "Times New Roman")
        fonts.set(qn("w:hAnsi"), "Times New Roman")
        run.font.size = Pt(12)
        szcs = rpr.find(qn("w:szCs"))
        if szcs is None:
            szcs = OxmlElement("w:szCs")
            rpr.append(szcs)
        szcs.set(qn("w:val"), "24")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "sample.docx"
    doc = Document()
    normal_rpr = doc.styles["Normal"].element.get_or_add_rPr()
    normal_fonts = normal_rpr.find(qn("w:rFonts"))
    if normal_fonts is None:
        normal_fonts = OxmlElement("w:rFonts")
        normal_rpr.insert(0, normal_fonts)
    normal_fonts.set(qn("w:cs"), "B Nazanin")
    lang = OxmlElement("w:lang")
    lang.set(qn("w:bidi"), "fa-IR")
    normal_rpr.append(lang)

    title = doc.add_paragraph()
    title.add_run("نمونه سند فارسی")
    rtl_paragraph(title)

    body = doc.add_paragraph()
    body.add_run("این یک بند آزمایشی است و جهت راست‌به‌چپ آن صریح نوشته شده.")
    rtl_paragraph(body)

    table = doc.add_table(rows=2, cols=2)
    tblpr = table._tbl.tblPr
    bidi_visual = OxmlElement("w:bidiVisual")
    bidi_visual.set(qn("w:val"), "1")
    tblpr.append(bidi_visual)
    cells = [["عنوان", "مقدار"], ["نرخ", "۱۲"]]
    for r, row in enumerate(cells):
        for c, text in enumerate(row):
            cell = table.cell(r, c)
            cell.text = ""
            para = cell.paragraphs[0]
            para.add_run(text)
            rtl_paragraph(para)
    # a table is followed by an empty paragraph in Word; give it the same markup
    tail = doc.add_paragraph()
    rtl_paragraph(tail)
    doc.save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
