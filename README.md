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

A file `letter.pdf` recognized as Latin and Italian becomes `letter_lat+ita.pdf` in the same folder.

The Quick Action uses spectre mode (300 dpi black and white). From Terminal:

```sh
ocr-pdf scan.pdf
MODE=spectre ocr-pdf scan.pdf
ocr-pdf --help
```

`OCR_LANGS=lat+ita` skips the language dialog. `FORCE=1` OCRs a PDF that already has real text. `NO_UI=1` turns off alerts. The comment at the top of `bin/ocr-pdf` lists the other settings.

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

Ghostscript and unpaper do the page image. The invisible-text font `pdf.ttf`, if [Tesseract](https://github.com/tesseract-ocr/tesseract) is installed, is used for the text layer. Otherwise Helvetica is used. Tesseract is not required.

## Releasing

To release a new version:

1. Tag `vX.Y.Z` and publish the GitHub release. The formula URL is the tag archive `vX.Y.Z.tar.gz`.
2. Set `sha256` in `packaging/homebrew/ocr-pdf.rb` from `shasum -a 256` of that tarball.
3. Copy the formula to `btafssp/homebrew-tap` as `Formula/ocr-pdf.rb`.

Keep `share/ocr-pdf/VERSION`, the `0.1.0` fallback in the scripts, and the formula version the same.
