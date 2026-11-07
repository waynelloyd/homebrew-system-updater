class SystemUpdater < Formula
  desc "Cross-platform system update script for Linux and macOS"
  homepage "https://github.com/waynelloyd/homebrew-system-updater"
  # NOTE: You will need to update the `url` and `sha256` for each new release.
  # 1. Create a new release tag in the `system-updater` repository (e.g., v1.0.1).
  # 2. Get the .tar.gz URL and its SHA256 hash from the new release page.
  # 3. Update the `url` and `sha256` below.
  url "https://github.com/waynelloyd/homebrew-system-updater/archive/refs/tags/v1.1.13.tar.gz"
  sha256 "e0cb7b5fab40760b0837e06eaf224151d1d56a92e3bd73e33a3b2e15e085b63a"
  license "MIT"

  def install
    # Create a virtualenv using system Python
    venv_path = libexec/"venv"
    system "python3", "-m", "venv", venv_path

    # Install PyYAML for docker-compose support
    system "#{venv_path}/bin/pip", "install", "--upgrade", "pip"
    system "#{venv_path}/bin/pip", "install", "PyYAML>=6.0"

    # Install the script to libexec
    libexec.install "system-updater.py"

    # Install documentation
    doc.install "README.md"

    # Create a wrapper script in bin that uses the virtualenv
    (bin/"system-updater").write <<~EOS
      #!/bin/bash
      exec "#{venv_path}/bin/python3" "#{libexec}/system-updater.py" "$@"
    EOS
  end

  test do
    system "#{bin}/system-updater", "--help"
    assert_match "system-updater", shell_output("#{bin}/system-updater --version")
  end
end
