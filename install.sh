#!/bin/bash

# System Updater Installation Script
# This script installs the system-updater to /usr/local/bin

set -e

INSTALL_DIR="/usr/local/bin"
SCRIPT_NAME="system-updater"
REPO_URL="https://raw.githubusercontent.com/waynelloyd/homebrew-system-updater/main/system_updater.py"

echo "🚀 Installing System Updater..."

# Check if running as root for system-wide install
if [[ $EUID -eq 0 ]]; then
    echo "Installing system-wide to $INSTALL_DIR"
    INSTALL_PATH="$INSTALL_DIR/$SCRIPT_NAME"
else
    # Install to user's local bin
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
    echo "Installing to user directory: $INSTALL_DIR"
    INSTALL_PATH="$INSTALL_DIR/$SCRIPT_NAME"
fi

# Download the script
echo "📥 Downloading system_updater.py..."
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$REPO_URL" -o "$INSTALL_PATH"
elif command -v wget >/dev/null 2>&1; then
    wget -q "$REPO_URL" -O "$INSTALL_PATH"
else
    echo "❌ Error: curl or wget is required to download the script"
    exit 1
fi

# Make executable
chmod +x "$INSTALL_PATH"

# Add to PATH if not already there (for user install)
if [[ $EUID -ne 0 ]] && [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "📝 Adding $INSTALL_DIR to PATH..."
    
    # Detect shell and add to appropriate config file
    if [[ "$SHELL" == *"zsh"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
        echo "Added to ~/.zshrc - restart your terminal or run: source ~/.zshrc"
    elif [[ "$SHELL" == *"bash"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo "Added to ~/.bashrc - restart your terminal or run: source ~/.bashrc"
    else
        echo "Please add $INSTALL_DIR to your PATH manually"
    fi
fi

echo "✅ System Updater installed successfully!"
echo "📍 Installed to: $INSTALL_PATH"
echo ""
echo "Usage:"
echo "  $SCRIPT_NAME -y          # Run all updates with auto-confirmation"
echo "  $SCRIPT_NAME --help      # Show all options"
echo ""
echo "🎉 Installation complete!"
