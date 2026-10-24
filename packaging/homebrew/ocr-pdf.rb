# Review copy for btafssp/homebrew-verbamac, to be added later as Formula/ocr-pdf.rb.
# Version 0.1.0 is a placeholder. There is no release tarball yet.
# TODO: replace the all-zero sha256 below with the sha256 of the v0.1.0
# GitHub release tarball before copying this file into the tap:
#   shasum -a 256 v0.1.0.tar.gz
# `brew audit` will reject the zero hash. That is intentional until the
# real tarball exists. Do not tag or publish a release from this change.
class OcrPdf < Formula
  desc "OCR scanned PDFs from Finder with Kraken"
  homepage "https://github.com/btafssp/ocr-pdf-mac"
  url "https://github.com/btafssp/ocr-pdf-mac/archive/refs/tags/v0.1.0.tar.gz"
  # TODO: replace this placeholder with the v0.1.0 release tarball sha256.
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"
  license "GPL-3.0-only"

  depends_on arch: :arm64
  depends_on "ghostscript"
  depends_on :macos
  depends_on "ocrmypdf"
  depends_on "python@3.13"
  depends_on "unpaper"

  def install
    bin.install "bin/ocr-pdf"
    bin.install "bin/ocr-pdf-setup"
    bin.install "bin/ocr-pdf-update"
    pkgshare.install "share/ocr-pdf/VERSION"
    pkgshare.install "share/ocr-pdf/requirements.txt"
    pkgshare.install "share/ocr-pdf/make-smoke-pdf.py"
    pkgshare.install "share/ocr-pdf/local.kraken.update.plist"
    pkgshare.install "share/ocr-pdf/OCR PDF.workflow"
  end

  def caveats
    <<~EOS
      The formula installs the commands only. Finish setup once (safe to repeat):

        ocr-pdf-setup

      That creates the Kraken virtualenv, downloads the CATMuS-Print model
      if it is not already installed, installs the Finder Quick Action, and
      loads the monthly updater.

      Then in Finder: right-click a scanned PDF, then Quick Actions, then OCR PDF.
    EOS
  end

  test do
    assert_match "0.1.0", shell_output("#{bin}/ocr-pdf --version")
    assert_match "0.1.0", shell_output("#{bin}/ocr-pdf-setup --version")
    assert_path_exists pkgshare/"requirements.txt"
    assert_path_exists pkgshare/"make-smoke-pdf.py"
    assert_path_exists pkgshare/"OCR PDF.workflow/Contents/document.wflow"
  end
end
