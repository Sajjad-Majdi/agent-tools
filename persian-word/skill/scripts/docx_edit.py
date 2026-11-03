#!/usr/bin/env python3
"""Surgical text edits inside an existing .docx, without rebuilding it.

Word stores paragraph text split across many `w:t` nodes, so a plain
search-and-replace on `document.xml` misses most phrases. This tool joins each
paragraph's own text nodes, matches against the joined string, and writes the
replacement back into the affected nodes only. Formatting of the first affected
run is kept and every other run in the match keeps its own remaining text.

    python docx_edit.py list report.docx --grep "L3" --limit 20
    python docx_edit.py find report.docx "\\d+ درصد" --regex
    python docx_edit.py apply report.docx ops.json --dry-run
    python docx_edit.py apply report.docx ops.json --out edited.docx

An ops file is a JSON list. Many edits therefore cost one tool call:

    [
      {"op": "replace", "find": "۹۵٪", "repl": "95%"},
      {"op": "replace", "where": "^جدول ۴", "find": "۱۲", "repl": "12"},
      {"op": "digits", "where": "arXiv", "to": "latin"},
      {"op": "replace", "para": 412, "find": "خطای واژه", "repl": "نرخ خطای واژه"},
      {"op": "insert_after", "where": "^در این بخش", "text": "یک بند تازه."}
    ]

Op fields
  op        replace | digits | ltr_terms | insert_after | insert_before |
            delete_para
  bidi      true = only RTL paragraphs, false = only LTR ones
  find      pattern to match inside the paragraph (literal unless regex:true)
  repl      replacement text; backreferences work when regex:true
  regex     treat find/where as regular expressions (default false for find,
            always true for where)
  where     only touch paragraphs whose joined text matches this regex
  para      only touch this paragraph index, as printed by `list`
  count     stop after this many replacements in each paragraph (default all)
  expect    fail the whole run unless exactly this many replacements happened
  to        for `digits`: latin or persian
  ltr       put the replacement in its own non-RTL run, so Word keeps Latin
            digits Latin; default true for digits->latin, false otherwise
  font      Latin face for an ltr run (default Times New Roman)
  text      for insert_after / insert_before: the new paragraph's text

Every op is checked before anything is written, and `expect` makes a silent
mismatch impossible. Nothing is written when any op fails or with --dry-run.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import zipfile

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
PERSIAN = "۰۱۲۳۴۵۶۷۸۹"
LATIN = "0123456789"
TO_LATIN = str.maketrans(PERSIAN, LATIN)
TO_PERSIAN = str.maketrans(LATIN, PERSIAN)
# A stretch of Latin/digit tokens, single-spaced, starting and ending on an
# alphanumeric so a trailing Persian sentence period is never swallowed. Only
# matches containing both a Latin letter and a digit are treated as terms.
TERM_PATTERN = (
    r"(?<![A-Za-z0-9۰-۹._-])"
    r"(?=[A-Za-z0-9۰-۹._ -]*[A-Za-z])"
    r"(?=[A-Za-z0-9۰-۹._ -]*[0-9۰-۹])"
    r"[A-Za-z0-9۰-۹][A-Za-z0-9۰-۹._-]*"
    r"(?: [A-Za-z0-9۰-۹][A-Za-z0-9۰-۹._-]*)*"
    r"(?<![._-])"
)

PART_RE = re.compile(r"^word/(document|header\d+|footer\d+|footnotes|endnotes)\.xml$")


# ---------------------------------------------------------------- reading

def load_parts(path, which):
    """Return [(part_name, xml_bytes)] plus the full name list of the archive."""
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if which == "all":
            wanted = [n for n in names if PART_RE.match(n)]
        else:
            wanted = [n for n in names if n == "word/document.xml"]
        return [(n, zf.read(n)) for n in wanted], names


def own_text_nodes(p):
    """`w:t` nodes belonging to this paragraph, not to one nested in a textbox."""
    out = []
    for node in p.iter(W + "t"):
        anc = node.getparent()
        while anc is not None and anc.tag != W + "p":
            anc = anc.getparent()
        if anc is p:
            out.append(node)
    return out


def para_is_rtl(p):
    """True unless the paragraph explicitly turns bidi off."""
    ppr = p.find(W + "pPr")
    if ppr is None:
        return True
    node = ppr.find(W + "bidi")
    if node is None:
        return True
    return node.get(W + "val", "1") not in ("0", "false")


def joined(nodes):
    return "".join(n.text or "" for n in nodes)


def spans(nodes):
    out, pos = [], 0
    for n in nodes:
        length = len(n.text or "")
        out.append((pos, pos + length, n))
        pos += length
    return out


# ---------------------------------------------------------------- writing

def ltr_run(src_run, text, font=None):
    """A copy of `src_run` carrying `text` as genuinely left-to-right content.

    Word re-substitutes Latin digits with Persian ones inside a run marked
    `w:rtl="1"`, so a number that must stay Latin needs its own run.
    """
    run = etree.fromstring(etree.tostring(src_run))
    for child in list(run):
        if child.tag != W + "rPr":
            run.remove(child)
    rpr = run.find(W + "rPr")
    if rpr is None:
        rpr = etree.SubElement(run, W + "rPr")
    for old in rpr.findall(W + "rtl"):
        rpr.remove(old)
    if font:
        for old in rpr.findall(W + "rFonts"):
            rpr.remove(old)
        fonts = etree.Element(W + "rFonts")
        fonts.set(W + "ascii", font)
        fonts.set(W + "hAnsi", font)
        fonts.set(W + "cs", font)
        rpr.insert(0, fonts)
    rtl = etree.SubElement(rpr, W + "rtl")
    rtl.set(W + "val", "0")
    node = etree.SubElement(run, W + "t")
    node.text = text
    node.set(XML_SPACE, "preserve")
    return run


def clone_run_with_text(src_run, text):
    run = etree.fromstring(etree.tostring(src_run))
    for child in list(run):
        if child.tag != W + "rPr":
            run.remove(child)
    node = etree.SubElement(run, W + "t")
    node.text = text
    node.set(XML_SPACE, "preserve")
    return run


def replace_span(nodes, start, end, new, ltr=False, font=None):
    """Put `new` in place of text[start:end] across however many runs it spans.

    With ltr=True the replacement is split out into its own non-RTL run so Word
    cannot re-shape its digits.
    """
    placed = False
    for s, e, node in spans(nodes):
        if e <= start or s >= end:
            continue
        txt = node.text or ""
        a = max(0, start - s)
        b = min(len(txt), end - s)
        if placed:
            node.text = txt[:a] + txt[b:]
            node.set(XML_SPACE, "preserve")
            continue
        run = node.getparent()
        if ltr and run is not None and run.tag == W + "r":
            node.text = txt[:a]
            node.set(XML_SPACE, "preserve")
            inserted = ltr_run(run, new, font)
            run.addnext(inserted)
            if txt[b:]:
                inserted.addnext(clone_run_with_text(run, txt[b:]))
        else:
            node.text = txt[:a] + new + txt[b:]
            node.set(XML_SPACE, "preserve")
        placed = True
    return placed


def substitute(p, pattern, repl, count, ltr=False, font=None):
    """Apply `pattern` to the paragraph. `repl` is a string or a callable."""
    nodes = own_text_nodes(p)
    if not nodes:
        return 0
    matches = list(pattern.finditer(joined(nodes)))
    if count:
        matches = matches[:count]
    # Last match first: an earlier match's offsets are then still valid.
    for m in reversed(matches):
        new = repl(m) if callable(repl) else m.expand(repl)
        replace_span(own_text_nodes(p), m.start(), m.end(), new, ltr, font)
    return len(matches)


def clone_paragraph(p, text):
    """Copy a paragraph, keeping its pPr and first run's rPr, with new text."""
    new = etree.fromstring(etree.tostring(p))
    for child in list(new):
        if child.tag not in (W + "pPr",):
            new.remove(child)
    src_run = p.find(W + "r")
    run = etree.SubElement(new, W + "r")
    if src_run is not None:
        rpr = src_run.find(W + "rPr")
        if rpr is not None:
            run.append(etree.fromstring(etree.tostring(rpr)))
    node = etree.SubElement(run, W + "t")
    node.text = text
    node.set(XML_SPACE, "preserve")
    return new


# ---------------------------------------------------------------- ops

def compile_find(op):
    find = op.get("find")
    if find is None:
        raise ValueError("op needs a 'find'")
    return re.compile(find if op.get("regex") else re.escape(find))


def run_ops(trees, ops, verbose=True):
    """Apply every op. Returns (total, failures)."""
    indexed = []
    for part, root in trees:
        for i, p in enumerate(root.iter(W + "p")):
            indexed.append((part, i, p))
    doc_paras = [(part, i, p) for part, i, p in indexed if part == "word/document.xml"]

    total, failures = 0, []
    for k, op in enumerate(ops):
        kind = op.get("op", "replace")
        where = re.compile(op["where"]) if op.get("where") else None
        target = doc_paras if op.get("para") is not None else indexed
        hits = 0
        touched = []

        for part, i, p in list(target):
            if op.get("para") is not None and i != op["para"]:
                continue
            text = joined(own_text_nodes(p))
            if where and not where.search(text):
                continue

            if op.get("bidi") is not None and para_is_rtl(p) != bool(op["bidi"]):
                continue

            if kind == "ltr_terms":
                n = substitute(p, re.compile(op.get("pattern", TERM_PATTERN)),
                               lambda m: m.group(0).translate(TO_LATIN),
                               op.get("count"), True, op.get("font"))
            elif kind == "replace":
                n = substitute(p, compile_find(op), op.get("repl", ""),
                               op.get("count"), op.get("ltr", False),
                               op.get("font"))
            elif kind == "digits":
                to = op.get("to", "latin")
                table = TO_LATIN if to == "latin" else TO_PERSIAN
                pattern = compile_find(op) if op.get("find") else re.compile(
                    "[" + (PERSIAN if to == "latin" else LATIN) + "][٫٬.,،0-9۰-۹]*")
                n = substitute(p, pattern, lambda m: m.group(0).translate(table),
                               op.get("count"), op.get("ltr", to == "latin"),
                               op.get("font"))
            elif kind in ("insert_after", "insert_before"):
                new = clone_paragraph(p, op["text"])
                if kind == "insert_after":
                    p.addnext(new)
                else:
                    p.addprevious(new)
                n = 1
            elif kind == "delete_para":
                p.getparent().remove(p)
                n = 1
            else:
                raise ValueError("unknown op: " + kind)

            if n:
                hits += n
                touched.append((part, i))

        expect = op.get("expect")
        ok = expect is None or hits == expect
        if not ok:
            failures.append((k, op, hits, expect))
        if verbose:
            mark = "ok " if ok else "FAIL"
            print(f"{mark} op[{k}] {kind}: {hits} change(s)"
                  + (f", expected {expect}" if expect is not None else ""))
            for part, i in touched[:6]:
                print(f"      {part} para {i}")
            if len(touched) > 6:
                print(f"      ... and {len(touched) - 6} more")
        total += hits
    return total, failures


# ---------------------------------------------------------------- output

def save(src, dst, edited):
    """Rewrite the archive, swapping only the parts that changed."""
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = edited.get(item.filename)
            if data is None:
                data = zin.read(item.filename)
            zout.writestr(item, data)


# ---------------------------------------------------------------- commands

def cmd_list(args):
    parts, _ = load_parts(args.docx, args.parts)
    grep = re.compile(args.grep) if args.grep else None
    shown = 0
    for name, blob in parts:
        root = etree.fromstring(blob)
        for i, p in enumerate(root.iter(W + "p")):
            text = joined(own_text_nodes(p))
            if not text.strip():
                continue
            if grep and not grep.search(text):
                continue
            print(f"{name} [{i}] {text[:args.width]}")
            shown += 1
            if args.limit and shown >= args.limit:
                return 0
    return 0


def cmd_find(args):
    parts, _ = load_parts(args.docx, args.parts)
    pattern = re.compile(args.pattern if args.regex else re.escape(args.pattern))
    shown = 0
    for name, blob in parts:
        root = etree.fromstring(blob)
        for i, p in enumerate(root.iter(W + "p")):
            text = joined(own_text_nodes(p))
            for m in pattern.finditer(text):
                lo = max(0, m.start() - 40)
                print(f"{name} [{i}] ...{text[lo:m.end() + 40]}...")
                shown += 1
                if args.limit and shown >= args.limit:
                    return 0
    print(f"matches shown: {shown}")
    return 0


def cmd_apply(args):
    ops = json.loads(open(args.ops, encoding="utf-8").read())
    if isinstance(ops, dict):
        ops = [ops]
    parts, _ = load_parts(args.docx, args.parts)
    trees = [(name, etree.fromstring(blob)) for name, blob in parts]
    total, failures = run_ops(trees, ops)

    if failures:
        print(f"\n{len(failures)} op(s) did not meet 'expect'; nothing written.")
        return 1
    if args.dry_run:
        print(f"\ndry run: {total} change(s), nothing written.")
        return 0
    if total == 0:
        print("\nno changes; nothing written.")
        return 1

    out = args.out or args.docx
    if out == args.docx and not args.no_backup:
        shutil.copyfile(args.docx, args.docx + ".bak")
        print(f"backup: {args.docx}.bak")
    edited = {name: etree.tostring(root, xml_declaration=True,
                                   encoding="UTF-8", standalone=True)
              for name, root in trees}
    save(args.docx, out + ".tmp", edited)
    shutil.move(out + ".tmp", out)
    print(f"\nwrote {out} ({total} change(s))")
    return 0


def main():
    # Windows consoles default to cp1252 and cannot print Persian.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = dict(parts=("--parts", {"default": "document",
                                     "choices": ["document", "all"],
                                     "help": "document.xml only, or headers and footers too"}))

    p_list = sub.add_parser("list", help="print paragraphs with their index")
    p_list.add_argument("docx")
    p_list.add_argument("--grep", help="only paragraphs matching this regex")
    p_list.add_argument("--limit", type=int, default=40)
    p_list.add_argument("--width", type=int, default=110)
    p_list.add_argument(*common["parts"][0:1], **common["parts"][1])
    p_list.set_defaults(func=cmd_list)

    p_find = sub.add_parser("find", help="show every match with context")
    p_find.add_argument("docx")
    p_find.add_argument("pattern")
    p_find.add_argument("--regex", action="store_true")
    p_find.add_argument("--limit", type=int, default=40)
    p_find.add_argument(*common["parts"][0:1], **common["parts"][1])
    p_find.set_defaults(func=cmd_find)

    p_apply = sub.add_parser("apply", help="apply a JSON list of ops")
    p_apply.add_argument("docx")
    p_apply.add_argument("ops")
    p_apply.add_argument("--out", help="write here instead of in place")
    p_apply.add_argument("--dry-run", action="store_true")
    p_apply.add_argument("--no-backup", action="store_true")
    p_apply.add_argument(*common["parts"][0:1], **common["parts"][1])
    p_apply.set_defaults(func=cmd_apply)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
