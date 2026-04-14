class SystemUpdater < Formula
  desc "Cross-platform system update script for Linux and macOS"
  homepage "https://github.com/waynelloyd/homebrew-system-updater"
  # NOTE: You will need to update the `url` and `sha256` for each new release.
  # 1. Create a new release tag in the `system-updater` repository (e.g., v1.0.1).
  # 2. Get the .tar.gz URL and its SHA256 hash from the new release page.
  # 3. Update the `url` and `sha256` below.
  url "https://github.com/waynelloyd/homebrew-system-updater/archive/refs/tags/v1.1.6.tar.gz"
  sha256 "497cfab381e28a306f9c2b101222b029b5036338790bbdaa0a8cd9d07af5f080"
  license "MIT"

  def install
    # Create a virtualenv using system Python
    venv = virtualenv_create(libexec, "/usr/bin/python3")

    # Install PyYAML for docker-compose support
    venv.pip_install "PyYAML>=6.0"

    # Install the script to libexec
    libexec.install "system-updater.py"

    # Install documentation
    doc.install "README.md"

    # Create a wrapper script in bin that uses the virtualenv
    (bin/"system-updater").write <<~EOS
      #!/bin/bash
      exec "#{venv}/bin/python3" "#{libexec}/system-updater.py" "$@"
    EOS
  end

  test do
    system "#{bin}/system-updater", "--help"
    assert_match "system-updater", shell_output("#{bin}/system-updater --version")
  end
end
