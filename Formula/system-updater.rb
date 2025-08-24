class SystemUpdater < Formula
  desc "Cross-platform system update script for Linux and macOS"
  homepage "https://github.com/waynelloyd/homebrew-system-updater"
  url "https://github.com/waynelloyd/homebrew-system-updater/archive/refs/tags/v1.1.0.tar.gz"
  sha256 "9a3796146aca7e4d9e031c92596b5adf05f32a6993875580ab8a32b1f0b5cb11"
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
