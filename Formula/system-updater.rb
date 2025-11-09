class SystemUpdater < Formula
  desc "Cross-platform system update script for Linux and macOS"
  homepage "https://github.com/waynelloyd/homebrew-system-updater"
  # NOTE: You will need to update the `url` and `sha256` for each new release.
  # 1. Create a new release tag in the `system-updater` repository (e.g., v1.0.1).
  # 2. Get the .tar.gz URL and its SHA256 hash from the new release page.
  # 3. Update the `url` and `sha256` below.
  url "https://github.com/waynelloyd/homebrew-system-updater/archive/refs/tags/v1.0.4.tar.gz"
  sha256 "6a3aa0bd7da7945302558e3b7180aa8fccfdbd26cd7fa6ad3654f8406f3b2aa2"
  license "MIT"

  def install
    # Install the Python script directly as executable
    bin.install "system-updater.py" => "system-updater"

    # Install documentation
    doc.install "README.md"
  end

  test do
    system "#{bin}/system-updater", "--help"
    assert_match "system-updater #{version}", shell_output("#{bin}/system-updater --version")
  end
end
