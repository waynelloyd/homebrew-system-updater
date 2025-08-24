class SystemUpdater < Formula
  desc "Cross-platform system update script for Linux and macOS"
  homepage "https://github.com/waynelloyd/homebrew-system-updater"
  url "https://github.com/waynelloyd/homebrew-system-updater/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "68a4ad8974006115f9fec757780d780e0b223456b9e42ddee15bc62878bdad40"
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
