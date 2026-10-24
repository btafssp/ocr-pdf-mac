#!/usr/bin/env python3
# Copyright (C) 2026 Brian T. Austin
# SPDX-License-Identifier: GPL-3.0-only
"""Build an image-only one-page PDF for the ocr-pdf smoke test.

Ghostscript draws public-domain words into a grayscale image. PyMuPDF wraps
that image in a PDF with no text layer, so the OCR pipeline treats the page
as a scan.

The words are the opening of the United States Declaration of Independence
(4 July 1776), which is in the public domain. Punctuation is flattened to
ASCII. Nothing here is taken from a copyrighted book or scan.

  make-smoke-pdf.py OUTPUT.pdf
  make-smoke-pdf.py --check-text
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

WRAP = 68
MAX_LINES = 43
LEADING = 16
FONT_SIZE = 13
COMMON = ("the", "of", "and", "in", "to", "is")

TEXT = """\
This page is a public-domain smoke test for ocr-pdf. The text below is the opening of the Declaration of Independence of the United States, 4 July 1776, which is in the public domain.

When in the Course of human events, it becomes necessary for one people to dissolve the political bands which have connected them with another, and to assume among the powers of the earth, the separate and equal station to which the Laws of Nature and of Nature's God entitle them, a decent respect to the opinions of mankind requires that they should declare the causes which impel them to the separation.

We hold these truths to be self-evident, that all men are created equal, that they are endowed by their Creator with certain unalienable Rights, that among these are Life, Liberty and the pursuit of Happiness. That to secure these rights, Governments are instituted among Men, deriving their just powers from the consent of the governed. That whenever any Form of Government becomes destructive of these ends, it is the Right of the People to alter or to abolish it, and to institute new Government, laying its foundation on such principles and organizing its powers in such form, as to them shall seem most likely to effect their Safety and Happiness. Prudence, indeed, will dictate that Governments long established should not be changed for light and transient causes; and accordingly all experience hath shewn, that mankind are more disposed to suffer, while evils are sufferable, than to right themselves by abolishing the forms to which they are accustomed. But when a long train of abuses and usurpations, pursuing invariably the same Object evinces a design to reduce them under absolute Despotism, it is their right, it is their duty, to throw off such Government, and to provide new Guards for their future security. Such has been the patient sufferance of these Colonies; and such is now the necessity which constrains them to alter their former Systems of Government. The history of the present King of Great Britain is a history of repeated injuries and usurpations, all having in direct object the establishment of an absolute Tyranny over these States. To prove this, let Facts be submitted to a candid world.
"""


def wrapped_lines(text):
    lines = []
    for para in text.strip().split("\n"):
        if not para.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(para, width=WRAP) or [""])
    return lines


def stats(text):
    words = re.findall(r"[A-Za-z]+", text)
    common = sum(word.lower() in COMMON for word in words)
    return len(text), common


def ps_escape(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_ps(path, lines):
    if len(lines) > MAX_LINES:
        raise SystemExit(
            f"smoke text is {len(lines)} lines; the page holds {MAX_LINES}"
        )
    y = 750
    parts = [
        "%!PS-Adobe-3.0",
        "%%Pages: 1",
        "%%Page: 1 1",
        f"/Times-Roman findfont {FONT_SIZE} scalefont setfont",
    ]
    for line in lines:
        if line:
            parts.append(f"72 {y} moveto ({ps_escape(line)}) show")
        y -= LEADING
        if y < 48:
            raise SystemExit("smoke text ran off the page")
    parts.append("showpage")
    path.write_text("\n".join(parts) + "\n", encoding="ascii")


def find_gs():
    candidates = [
        os.environ.get("GS", ""),
        "/opt/homebrew/bin/gs",
        "/usr/local/bin/gs",
        shutil.which("gs") or "",
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise SystemExit("ghostscript (gs) was not found")


def build(out_path):
    lines = wrapped_lines(TEXT)
    work = Path(tempfile.mkdtemp(prefix="ocr-pdf-smoke-"))
    try:
        ps = work / "page.ps"
        png = work / "page.png"
        write_ps(ps, lines)
        subprocess.check_call(
            [
                find_gs(),
                "-dSAFER",
                "-dBATCH",
                "-dNOPAUSE",
                "-dQUIET",
                "-sPAPERSIZE=letter",
                "-sDEVICE=pnggray",
                "-r300",
                f"-sOutputFile={png}",
                str(ps),
            ]
        )
        if png.stat().st_size < 10000:
            raise SystemExit("rendered smoke page is unexpectedly small")
        import pymupdf

        pix = pymupdf.Pixmap(str(png))
        scale = 72.0 / 300.0
        doc = pymupdf.open()
        page = doc.new_page(width=pix.width * scale, height=pix.height * scale)
        page.insert_image(page.rect, filename=str(png))
        if any(item.get_text().strip() for item in doc):
            raise SystemExit("smoke PDF has a text layer before saving")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(out_path), garbage=3, deflate=True)
        doc.close()
        check = pymupdf.open(str(out_path))
        try:
            if len(check) != 1:
                raise SystemExit(f"smoke PDF has {len(check)} pages")
            if any(item.get_text().strip() for item in check):
                raise SystemExit("smoke PDF has a text layer")
        finally:
            check.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)


def check_text():
    chars, common = stats(TEXT)
    lines = wrapped_lines(TEXT)
    problems = []
    if chars < 1500:
        problems.append(f"chars={chars} (want at least 1500)")
    if common < 40:
        problems.append(f"common_words={common} (want at least 40)")
    if len(lines) > MAX_LINES:
        problems.append(f"lines={len(lines)} (page holds {MAX_LINES})")
    if problems:
        raise SystemExit("smoke text: " + "; ".join(problems))
    print(f"OK chars={chars} common={common} lines={len(lines)}")
    return 0


def main(argv):
    if argv == ["--check-text"]:
        return check_text()
    if len(argv) != 1 or argv[0].startswith("-"):
        print("usage: make-smoke-pdf.py OUTPUT.pdf | --check-text", file=sys.stderr)
        return 2
    build(Path(argv[0]))
    print(f"wrote {argv[0]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
