class SystemUpdater < Formula
  desc "Cross-platform system update script for Linux and macOS"
  homepage "https://github.com/YOUR_USERNAME/YOUR_REPO_NAME"
  url "https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "b011efcbf830315d629ac337822ce38c477db9ac52ca9a2de45c6917f3bd6d09"
  license "MIT"

  depends_on "python@3.11"

  def install
    # Install the main script
    bin.install "system_updater.py" => "system-updater"
    
    # Make it executable
    chmod 0755, bin/"system-updater"
    
    # Create a wrapper script to ensure proper Python execution
    (bin/"system-updater").write <<~EOS
      #!/bin/bash
      exec "#{Formula["python@3.11"].opt_bin}/python3" "#{libexec}/system_updater.py" "$@"
    EOS
    
    # Install the actual Python script
    libexec.install "system_updater.py"
    
    # Install documentation
    doc.install "README.md"
  end

  test do
    system "#{bin}/system-updater", "--help"
  end
end
