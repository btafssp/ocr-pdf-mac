#!/usr/bin/env python3
# Copyright (C) 2026 Brian T. Austin
# SPDX-License-Identifier: GPL-3.0-only
"""Graywhite: OCR stays on the 300 dpi grey; the JPEG is the 260 dpi image.

Checks three things, without running Kraken:

1. The default log line is OCR_DPI=300, PROCESS_DPI=300, output DPI=260.
   An explicit OCR_DPI=250 is still kept.
2. topage writes Kraken's PNG at the process resolution and downsamples
   only the JPEG.
3. A word drawn on the 300 dpi grey lands on the 260 dpi page. Width and
   height use their own pixel ratios, because the two axes round separately.

    test-graywhite-align.py
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "bin" / "ocr-pdf"
ZSH = "/bin/zsh" if Path("/bin/zsh").exists() else shutil.which("zsh")
PY = Path.home() / ".venvs" / "kraken" / "bin" / "python"
if not PY.exists():
    PY = Path(sys.executable)


def extract(name):
    text = SCRIPT.read_text()
    m = re.search(rf"cat >\"\$WORK/{re.escape(name)}\" <<'PY'\n(.*?)\nPY\n", text, re.S)
    if not m:
        raise SystemExit(f"could not find {name} in {SCRIPT}")
    return m.group(1) + "\n"


def check(cond, message):
    if not cond:
        raise SystemExit("FAIL: " + message)


def defaults():
    check(ZSH, "zsh is not installed")
    empty = Path(tempfile.mkdtemp()) / "empty.pdf"
    empty.write_bytes(b"")
    env = os.environ.copy()
    env.update(MODE="graywhite", NO_UI="1")
    r = subprocess.run(
        [ZSH, str(SCRIPT), str(empty)],
        env=env, capture_output=True, text=True,
    )
    log = r.stderr + r.stdout
    check("OCR_DPI=300" in log and "DPI=260" in log and "PROCESS_DPI=300" in log,
          "graywhite default log is not OCR 300 / process 300 / output 260:\n" + log)
    env.update(OCR_DPI="250")
    r = subprocess.run(
        [ZSH, str(SCRIPT), str(empty)],
        env=env, capture_output=True, text=True,
    )
    log = r.stderr + r.stdout
    check("OCR_DPI=250" in log and "DPI=260" in log,
          "explicit OCR_DPI=250 was not kept:\n" + log)
    help_text = subprocess.run(
        [ZSH, str(SCRIPT), "--help"],
        capture_output=True, text=True,
    ).stderr
    check("OCR_DPI (default 300)" in help_text, "help does not say OCR_DPI default 300")
    check("default 250" not in help_text, "help still says default 250")


def pipeline():
    from PIL import Image
    import pymupdf

    # 300 by 101 process pixels. 260/300 does not land on an integer height,
    # so the JPEG height ratio is not the width ratio.
    gw, gh = 300, 101
    proc, out_dpi = 300, 260
    ow = max(1, int(round(gw * out_dpi / proc)))
    oh = max(1, int(round(gh * out_dpi / proc)))
    check(ow == 260 and oh == 88, f"unexpected jpeg size {ow}x{oh}")
    kx = 72.0 / out_dpi * (ow / gw)
    ky = 72.0 / out_dpi * (oh / gh)
    # A width-only scale would miss the height by this many points over 70 px.
    width_only_dy = 70 * (72.0 / out_dpi) * (ow / gw)
    right_dy = 70 * ky
    check(abs(right_dy - width_only_dy) > 0.05, "test page does not separate the axes")

    work = Path(tempfile.mkdtemp())
    (work / "fontsubset.py").write_text(extract("fontsubset.py"))
    (work / "topage.py").write_text(extract("topage.py"))
    (work / "altolayer.py").write_text(extract("altolayer.py"))
    src = work / "sheet.png"
    Image.new("L", (gw, gh), 210).save(src)
    pages, gray, alto = work / "pages", work / "gray", work / "alto"
    for d in (pages, gray, alto):
        d.mkdir()
    subprocess.check_call(
        [str(PY), str(work / "topage.py"), str(src), str(pages / "p1"),
         str(gray / "p1.png"), "graywhite", "165", "55", str(out_dpi), "0", str(proc)],
        cwd=work,
    )
    g = Image.open(gray / "p1.png")
    j = Image.open(pages / "p1.jpg")
    check(g.size == (gw, gh), f"Kraken grey was downsampled: {g.size}")
    check(j.size == (ow, oh), f"JPEG size {j.size}, expected {(ow, oh)}")

    alto_xml = """<?xml version="1.0"?>
<alto><Layout><Page><PrintSpace><TextBlock>
<TextLine HPOS="30" VPOS="10" WIDTH="120" HEIGHT="20">
  <String CONTENT="Prot." HPOS="30" VPOS="10" WIDTH="50" HEIGHT="20"/>
  <String CONTENT="58652" HPOS="90" VPOS="10" WIDTH="60" HEIGHT="20"/>
</TextLine>
<TextLine HPOS="30" VPOS="80" WIDTH="80" HEIGHT="20">
  <String CONTENT="Roma" HPOS="30" VPOS="80" WIDTH="80" HEIGHT="20"/>
</TextLine>
</TextBlock></PrintSpace></Page></Layout></alto>"""
    (alto / "p1.xml").write_text(alto_xml)
    subprocess.check_call(
        [str(PY), str(work / "altolayer.py"), str(pages), str(alto),
         str(work / "out.pdf"), str(out_dpi), "", str(gray)],
        cwd=work,
    )
    doc = pymupdf.open(work / "out.pdf")
    page = doc[0]
    check(abs(page.rect.width - ow * 72.0 / out_dpi) < 0.02, "page width")
    check(abs(page.rect.height - oh * 72.0 / out_dpi) < 0.02, "page height")
    words = {w[4]: w for w in page.get_text("words")}
    check(set(words) == {"Prot.", "58652", "Roma"}, f"words {sorted(words)}")
    for label, hpos in (("Prot.", 30), ("58652", 90), ("Roma", 30)):
        got = words[label][0]
        exp = hpos * kx
        check(abs(got - exp) < 0.05, f"{label} x0 {got:.3f}, expected {exp:.3f}")
    dy = words["Roma"][1] - words["Prot."][1]
    check(abs(dy - right_dy) < 0.03, f"line spacing {dy:.3f}, expected {right_dy:.3f}")
    check(abs(dy - width_only_dy) > 0.04, "vertical scale followed the width ratio")
    text = page.get_text()
    check("Prot." in text and "58652" in text and "Roma" in text, text)


def main():
    defaults()
    pipeline()
    print("ok")


if __name__ == "__main__":
    main()
