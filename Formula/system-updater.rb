class SystemUpdater < Formula
  desc "Cross-platform system update script for Linux and macOS"
  homepage "https://github.com/waynelloyd/homebrew-system-updater"
  url "https://github.com/waynelloyd/homebrew-system-updater/archive/refs/tags/v1.1.0.tar.gz"
  sha256 "d1e67a022e20b5b462b94778008b476a8c4ac40d9aeaf8896e722719c5e21c54"
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
