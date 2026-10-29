class OcrPdf < Formula
  desc "OCR scanned PDFs from Finder with Kraken"
  homepage "https://github.com/btafssp/ocr-pdf-mac"
  url "https://github.com/btafssp/ocr-pdf-mac/archive/refs/tags/v0.2.3.tar.gz"
  sha256 "35ef99d86447849cc49d1af8a80632801c425226d1874c182b66f91a84baa510"
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
    assert_match version.to_s, shell_output("#{bin}/ocr-pdf --version")
    assert_match version.to_s, shell_output("#{bin}/ocr-pdf-setup --version")
    assert_path_exists pkgshare/"requirements.txt"
    assert_path_exists pkgshare/"make-smoke-pdf.py"
    assert_path_exists pkgshare/"OCR PDF.workflow/Contents/document.wflow"
  end
end
