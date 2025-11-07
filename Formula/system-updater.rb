class SystemUpdater < Formula
  desc "Cross-platform system update script for Linux and macOS"
  homepage "https://github.com/waynelloyd/homebrew-system-updater"
  # NOTE: You will need to update the `url` and `sha256` for each new release.
  # 1. Create a new release tag in the `system-updater` repository (e.g., v1.0.1).
  # 2. Get the .tar.gz URL and its SHA256 hash from the new release page.
  # 3. Update the `url` and `sha256` below.
  url "https://github.com/waynelloyd/homebrew-system-updater/archive/refs/tags/v1.0.4.tar.gz"
  sha256 "940cf710d87a543cc4b9a452f5435298921167d266a15e78a46c6cc54f30d7ac"
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
