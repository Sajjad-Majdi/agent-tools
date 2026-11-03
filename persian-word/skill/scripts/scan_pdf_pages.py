#!/usr/bin/env python3
"""Scan a rendered PDF for layout problems and build contact sheets.

Finds pages that end far above the bottom margin (orphaned figures, split
tables, stray blank pages) so the visual pass only needs to look at suspects.

    python scan_pdf_pages.py report.pdf
    python scan_pdf_pages.py report.pdf --sheets outdir
    python scan_pdf_pages.py report.pdf --page 39 --dpi 130 --out page39.png

Requires PyMuPDF, plus Pillow for contact sheets.
"""
from __future__ import annotations

import argparse
import os
import sys

import pymupdf

A4_HEIGHT_PT = 841.92
HEADER_PT = 90.0          # ignore running headers above this y
FOOTER_PT = 790.0         # ignore footers below this y


def content_bottom(page: pymupdf.Page) -> float:
    """Lowest point of real content, ignoring header and footer bands."""
    bottom = 0.0
    for block in page.get_text("blocks"):
        if block[4].strip() and HEADER_PT < block[1] < FOOTER_PT:
            bottom = max(bottom, block[3])
    for image in page.get_images():
        for rect in page.get_image_rects(image[0]):
            if rect.y0 > HEADER_PT:
                bottom = max(bottom, rect.y1)
    for drawing in page.get_drawings():
        rect = drawing["rect"]
        if HEADER_PT < rect.y0 < FOOTER_PT:
            bottom = max(bottom, rect.y1)
    return bottom


def report(path: str, threshold: float) -> int:
    doc = pymupdf.open(path)
    blanks, sparse = [], []
    for index, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        bottom = content_bottom(page)
        if not text and bottom == 0:
            blanks.append(index)
        elif 0 < bottom < threshold:
            head = text[:70].replace("\n", " | ")
            sparse.append((index, round(bottom), head))
    print(f"pages={len(doc)}")
    print(f"blank pages ({len(blanks)}): {blanks}")
    print(f"pages ending above {threshold:.0f}pt ({len(sparse)}):")
    for index, bottom, head in sparse:
        print(f"  p{index:>4}  bottom={bottom:<4}  {head}")
    print("\nBlank pages are expected where a template mandates a blank verso.")
    print("Sparse pages are expected at the end of a chapter or before a figure.")
    return 0


def sheets(path: str, out_dir: str, per: int, dpi: int, cols: int) -> int:
    from PIL import Image

    os.makedirs(out_dir, exist_ok=True)
    doc = pymupdf.open(path)
    total = len(doc)
    rows = (per + cols - 1) // cols
    for start in range(0, total, per):
        images = []
        for index in range(start, min(start + per, total)):
            pix = doc[index].get_pixmap(dpi=dpi)
            images.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        width, height = images[0].size
        sheet = Image.new("RGB", (width * cols, height * rows), "#BBBBBB")
        for k, image in enumerate(images):
            sheet.paste(image, ((k % cols) * width, (k // cols) * height))
        name = os.path.join(out_dir, "sheet_%03d.png" % (start + 1))
        sheet.save(name)
        print("wrote", name, "pages", start + 1, "to", min(start + per, total))
    return 0


def single(path: str, page: int, dpi: int, out: str) -> int:
    doc = pymupdf.open(path)
    doc[page - 1].get_pixmap(dpi=dpi).save(out)
    print("wrote", out)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("--threshold", type=float, default=600.0,
                        help="flag pages whose content ends above this y in points")
    parser.add_argument("--sheets", metavar="DIR", help="write contact sheets here")
    parser.add_argument("--per", type=int, default=24, help="pages per contact sheet")
    parser.add_argument("--cols", type=int, default=6, help="columns per contact sheet")
    parser.add_argument("--dpi", type=int, default=52, help="contact sheet or page dpi")
    parser.add_argument("--page", type=int, help="render one page instead")
    parser.add_argument("--out", default="page.png", help="output file for --page")
    args = parser.parse_args()

    if args.page:
        return single(args.pdf, args.page, args.dpi, args.out)
    if args.sheets:
        return sheets(args.pdf, args.sheets, args.per, args.dpi, args.cols)
    return report(args.pdf, args.threshold)


if __name__ == "__main__":
    sys.exit(main())
