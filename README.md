# ocr-pdf-mac

Right-click OCR for scanned PDFs on a Mac. A Finder Quick Action named OCR PDF reads a scan with Kraken and writes a new PDF next to the original, with an invisible text layer you can search and copy. The original file is left alone.

A PDF that already has real publisher text is skipped. An old invisible OCR layer is replaced.

Copyright (C) 2026 Brian T. Austin. Licensed under the GNU General Public License, version 3 only. See [LICENSE](LICENSE).

## Install

On an Apple Silicon Mac, with [Homebrew](https://brew.sh):

```sh
brew install btafssp/tap/ocr-pdf
ocr-pdf-setup
```

`ocr-pdf-setup` is safe to run again. It reuses `~/.venvs/kraken` when that environment already runs on Homebrew Python 3.13. It does not delete a working environment. If it has to replace one, it moves the old one to `~/.venvs/kraken.backup-<date>` and leaves it there. At the end it OCRs a one-page public-domain test and stops if that fails.

The first setup downloads PyTorch into that virtualenv, so it needs a network connection and a few gigabytes of disk.

The formula lives in the tap [btafssp/homebrew-tap](https://github.com/btafssp/homebrew-tap) as `Formula/ocr-pdf.rb`. Daily `brew upgrade` picks up new releases. [packaging/homebrew/ocr-pdf.rb](packaging/homebrew/ocr-pdf.rb) is the copy kept in this repository.

## Use

In Finder, right-click a scanned PDF, then Quick Actions, then OCR PDF. Choose the languages. They are used in the new file's name. The recognizer itself is multilingual.

Batch: select several PDFs, or a folder, and run OCR PDF once. A folder means the PDFs directly inside it (not subfolders); other files and earlier outputs such as `name_lat.pdf` are ignored. You choose the languages once and, if any of the PDFs already have text, answer one Yes/No question for all of them. One summary at the end lists how many were done, skipped and failed.

A file `letter.pdf` recognized as Latin and Italian becomes `letter_lat+ita.pdf` in the same folder.

The Quick Action uses spectre mode (300 dpi black and white). From Terminal:

```sh
ocr-pdf scan.pdf
MODE=spectre ocr-pdf scan.pdf
MODE=graywhite ocr-pdf scan.pdf
ocr-pdf --help
```

`MODE` chooses the page image. The default is `bw`.

- `bw` is a black and white PNG. `BW_THRESHOLD` (default 165) is the cutoff.
- `dither` is a Floyd-Steinberg black and white PNG.
- `gray` is a greyscale JPEG. `JPEG_QUALITY` defaults to 32.
- `spectre` is 300 dpi Otsu black and white, then JBIG2. The resolution is `SPECTRE_DPI` (default 300).
- `graywhite` is a greyscale JPEG with a white background and grey type, in the manner of a ScanTailor greyscale export. Ghostscript renders at `PROCESS_DPI` (default 300). Illumination is flattened on that same raster, with no blur. Kraken reads that plain grey, at `OCR_DPI` (default 300), so recognition is not done on the smaller export. The page is Lanczos-downsampled to `DPI` (default 260) only when the JPEG is saved. Word positions from the 300 dpi grey are scaled onto that JPEG, using each axis's real pixel ratio. `JPEG_QUALITY` defaults to 55 and `SHARPEN` defaults to 0, so a full letter stays near the size of the ScanTailor prototype. `SHARPEN=1` is a mild unsharp mask on the type only. `SHARPEN=2` is stronger. The light seal is not sharpened. Unpaper is not run, so the page is not recropped or shifted. Set `OCR_DPI` to use a different grey for Kraken.

`share/ocr-pdf/test-graywhite-align.py` checks that Kraken's grey stays at 300 dpi, that only the JPEG is 260 dpi, and that a word on the 300 dpi grey lands on that JPEG.

`OCR_LANGS=lat+ita` skips the language dialog. `FORCE=1` OCRs a PDF that already has real text. From the Quick Action, such a PDF brings up a Yes/No question, "Would you like me to OCR it anyway?"; Yes runs the full cleanup, shrink and Kraken OCR and replaces the old text, No leaves the file alone. `OCR_PDF_ANSWER=yes` or `no` answers it without a dialog (for testing). After a file is OCRed and the new PDF checks out (it exists, opens, and has at least as many pages), the original is moved to the Trash, so it can be put back. It is never trashed on a failure or a skip. `KEEP_ORIGINAL=1` keeps originals where they are. At the end, one notification sums up the run, for example "3 files complete; 82% compression; 4.1 MB saved; 1 skipped." `NO_UI=1` turns off alerts. The comment at the top of `bin/ocr-pdf` lists the other settings.

The invisible text stays selectable and searchable, and it stays lined up with the words on the page. In every mode, the font for that layer is reduced to the characters actually used, instead of embedding a whole face, so the file is smaller. That subset is built with fontTools. Re-run `ocr-pdf-setup` if the Kraken virtualenv was created before fonttools was pinned; without it the face stays larger.

Log: `~/Library/Logs/pdf_inbox_pipeline.log`

Ghostscript renders each page, unpaper cleans it, and Kraken reads it. OCRmyPDF only compresses the result. It is not asked to recognize text.

## Monthly update

`ocr-pdf-setup` loads a LaunchAgent that runs `ocr-pdf-update` on the 1st of the month at 4:47 AM, after a daily 4:00 AM `brew upgrade`. The updater snapshots the virtualenv, upgrades Kraken (keeping PyMuPDF below 2), smoke-tests OCR, and rolls back if the smoke test fails. The model is not modified.

```sh
ocr-pdf-update --dry-run
ocr-pdf-update --smoke-only
```

Log: `~/Library/Logs/kraken_update.log`

The smoke test draws a one-page image-only PDF of public-domain text (the opening of the Declaration of Independence) and OCRs that. It does not use a file of yours.

## Uninstall

```sh
launchctl bootout gui/$(id -u) "$HOME/Library/LaunchAgents/local.kraken.update.plist"
rm "$HOME/Library/LaunchAgents/local.kraken.update.plist"
rm -rf "$HOME/Library/Services/OCR PDF.workflow"
/System/Library/CoreServices/pbs -update
brew uninstall ocr-pdf
```

That leaves the virtualenv, the model, your PDFs, and the logs. To remove the virtualenv and the model as well:

```sh
rm -rf "$HOME/.venvs/kraken"
rm -rf "$HOME/Library/Application Support/htrmopo"
```

Package snapshots, if you want those gone too, are under `~/Library/Application Support/pdf_inbox_pipeline/`.

## Credits

- [Kraken](https://kraken.re), by Benjamin Kiessling and contributors. Apache License 2.0.
- [CATMuS-Print](https://doi.org/10.5281/zenodo.10592716) (Large), by Simon Gabay, Thibault Clérice, and contributors. DOI [10.5281/zenodo.10592716](https://doi.org/10.5281/zenodo.10592716). License [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF), by James R. Barlow and contributors. Mozilla Public License 2.0.

Ghostscript and unpaper do the page image. `graywhite` does not use unpaper. The invisible-text font `pdf.ttf`, if [Tesseract](https://github.com/tesseract-ocr/tesseract) is installed, is the first choice for the text layer. Otherwise Helvetica is used. Tesseract is not required. When that font has no outlines for a character, the embedded face can be a system font such as Noto Serif. fontTools subsets it to the characters on the page. Re-run `ocr-pdf-setup` so an older virtualenv installs fonttools.

## Releasing

To release a new version:

1. Tag `vX.Y.Z` and publish the GitHub release. The formula URL is the tag archive `vX.Y.Z.tar.gz`.
2. Set `sha256` in `packaging/homebrew/ocr-pdf.rb` from `shasum -a 256` of that tarball.
3. Copy the formula to `btafssp/homebrew-tap` as `Formula/ocr-pdf.rb`.

Keep `share/ocr-pdf/VERSION` and the version fallback in the scripts the same. Update the formula URL and sha256 when you tag the release.
