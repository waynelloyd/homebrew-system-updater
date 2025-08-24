class SystemUpdater < Formula
  desc "Cross-platform system update script for Linux and macOS"
  homepage "https://github.com/waynelloyd/homebrew-system-updater"
  url "https://github.com/waynelloyd/homebrew-system-updater/archive/refs/tags/v1.1.0.tar.gz"
  sha256 "4b958d44b224afb50ddd09a4a13c02564976251ef53013ee58a0cb5e3403ff58"
  license "MIT"

  depends_on "python@3.11"

  def install
    # Install the Python script directly as executable
    bin.install "system_updater.py" => "system-updater"
    
    # Install documentation
    doc.install "README.md"
  end

  test do
    system "#{bin}/system-updater", "--help"
  end
end
