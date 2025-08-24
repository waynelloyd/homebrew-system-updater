class SystemUpdater < Formula
  desc "Cross-platform system update script for Linux and macOS"
  homepage "https://github.com/waynelloyd/homebrew-system-updater"
  url "https://github.com/waynelloyd/homebrew-system-updater/archive/refs/tags/v1.1.0.tar.gz"
  sha256 "bca7c1c6f4ecac1e1565b9f476b76b701ce10c2d6dd2d4d189c792b1495d2de4"
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
