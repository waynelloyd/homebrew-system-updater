# System Updater Script

A comprehensive cross-platform system update script that handles package management, service restarts, and Docker maintenance across Linux and macOS systems. Features auto-yes by default with optional interactive mode and granular control over update operations.

## Features

### 🖥️ Cross-Platform Support
- **Linux**: Ubuntu, Fedora, RHEL/CentOS
- **macOS**: Full macOS support with multiple package managers
- **Automatic OS Detection**: Runs appropriate commands based on detected system

### 🔄 Intelligent Updates
- **Smart Service Restart**: Detects and restarts services that need it (Fedora/RHEL)
- **System Reboot Detection**: Prompts for reboot when required
- **Docker Container Management**: Only restarts containers when updates are detected
- **Graceful Fallbacks**: Skips unavailable package managers without errors

## Functionality by Operating System

### 🐧 Linux (Ubuntu/Debian)

#### System Packages
- `sudo apt update` - Update package lists
- `sudo apt upgrade` - Upgrade installed packages

#### Additional Package Managers
- **Snap Packages**: `sudo snap refresh`
- **Flatpak**: `flatpak update --appstream && flatpak update -y`
- **Firmware**: `fwupdmgr refresh && fwupdmgr update`

#### Developer Tools
- **pip3**: Updates outdated Python packages
- **Docker**: Compose pull/restart + system prune

---

### 🐧 Linux (Fedora/RHEL)

#### System Packages
- `sudo dnf upgrade` - Update all packages
- **Smart Restart Detection**: Uses `needs-restarting` to detect:
  - Services requiring restart (`needs-restarting -s`)
  - System reboot requirements (`needs-restarting -r`)
  - Automatic service restart with user confirmation
  - System reboot prompt with 10-second countdown

#### Additional Package Managers
- **Snap Packages**: `sudo snap refresh`
- **Flatpak**: `flatpak update --appstream && flatpak update -y`
- **Firmware**: `fwupdmgr refresh && fwupdmgr update`

#### Developer Tools
- **pip3**: Updates outdated Python packages
- **Docker**: Compose pull/restart + system prune

---

### 🍎 macOS

#### System Updates
- `softwareupdate -ia` - Install all available macOS system updates

#### Package Managers
- **Homebrew**: 
  - `brew update` - Update Homebrew itself
  - `brew upgrade` - Upgrade formulae
  - `brew upgrade --cask` - Upgrade casks
  - `brew autoremove` - Remove outdated downloads
  - `brew cleanup` - Clean up old versions

#### App Stores & Applications
- **Mac App Store**: `mas outdated && mas upgrade` (via mas CLI)
- **MacUpdater**: Scan and update Mac applications (opt-in with `--macupdater` flag)

#### Developer Tools
- **Ruby Gems**: `gem outdated --user-install && gem update --user-install` (user gems only)
- **npm**: Global and user packages (`npm outdated -g && npm update -g`, `npm outdated && npm update`)
- **pip3**: System and user Python packages with separate handling
- **Docker**: Compose pull/restart + system prune

---

## Docker Operations (All Platforms)

### Docker Compose (searches ~/ directory and prompts to add compose.yml)
- **Smart Pull**: `docker-compose pull` with update detection
- **Conditional Restart**: `docker-compose up -d` only if updates found
- **Update Detection**: Scans pull output for actual image updates

### Docker Maintenance
- **System Cleanup**: `docker system prune -a` with auto-confirmation

---

## Installation

### Option 1: Homebrew (macOS/Linux)
```bash
# Add the tap
brew tap waynelloyd/system-updater

# Install the package
brew install system-updater

# Run it
system-updater
```

### Option 2: Direct Install Script
```bash
# System-wide install (requires sudo)
curl -fsSL https://raw.githubusercontent.com/waynelloyd/homebrew-system-updater/main/install.sh | sudo bash


# User install (no sudo required)
curl -fsSL https://raw.githubusercontent.com/waynelloyd/homebrew-system-updater/main/install.sh | bash
```

### Option 3: Manual Install
```bash
# Download and make executable
curl -fsSL https://raw.githubusercontent.com/waynelloyd/homebrew-system-updater/main/system_updater.py -o system-updater
chmod +x system-updater
sudo mv system-updater /usr/local/bin/
```

## System Requirements

### Linux
```bash
# Ubuntu/Debian
sudo apt install flatpak fwupd

# Fedora/RHEL  
sudo dnf install flatpak fwupd
```

### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install optional tools
brew install mas  # Mac App Store CLI
# MacUpdater: Download from https://www.corecode.io/macupdater/
```

## Usage

### Basic Usage
```bash
# Run all updates (auto-yes is default)
system-updater

# Run with manual confirmation prompts
system-updater -i
# or
system-updater --interactive
```

### Skip Specific Operations
```bash
# Skip system package updates
system-updater --skip-system

# Skip snap packages (Linux)
system-updater --skip-snap

# Skip Flatpak updates (Linux)
system-updater --skip-flatpak

# Skip firmware updates (Linux)
system-updater --skip-firmware

# Skip pip package updates
system-updater --skip-pip

# Enable MacUpdater (opt-in only)
system-updater --macupdater

# Skip Docker operations
system-updater --skip-docker-pull --skip-docker-prune
```

### Command Line Options
```bash
system-updater --help
```

**Available Options:**
- `-i, --interactive` - Interactive mode with prompts (default is auto-yes)
- `--skip-system` - Skip system package updates
- `--skip-snap` - Skip snap refresh (Linux only)
- `--skip-flatpak` - Skip Flatpak updates (Linux only)
- `--skip-pip` - Skip pip package updates
- `--macupdater` - Enable MacUpdater for Mac applications (macOS only, opt-in)
- `--skip-firmware` - Skip firmware updates (Linux only)
- `--skip-docker-pull` - Skip docker-compose pull
- `--skip-docker-prune` - Skip docker system prune

## Examples

### Complete System Update
```bash
# Update everything (auto-yes by default)
system-updater

# Update everything including MacUpdater
system-updater --macupdater
```

### Development Environment Update
```bash
# Update only development tools
system-updater --skip-system --skip-firmware
```

### Server Maintenance
```bash
# Update system packages and Docker, skip desktop apps
system-updater --skip-snap --skip-flatpak
```

## Safety Features

- **Service Restart Confirmation**: Always prompts before restarting services
- **System Reboot Safety**: Requires manual confirmation even with `-y` flag
- **Graceful Failures**: Continues operation if individual package managers fail
- **Update Detection**: Only restarts Docker containers when actual updates occur
- **Comprehensive Logging**: Clear output showing what's being updated and why

## Output Example

```
🚀 Starting system update process...
Mode: Auto-yes
Detected OS: ubuntu

==================================================
Running: Updating package lists
Command: sudo apt update
==================================================
✅ Updating package lists completed successfully

==================================================
Running: Upgrading packages
Command: sudo apt upgrade
==================================================
✅ Upgrading packages completed successfully

📊 SUMMARY
==================================================
Tasks completed successfully: 8/8
🎉 All tasks completed successfully!
```

## Requirements

- **Python 3.6+**
- **sudo privileges** (for system package updates)
- **Docker** (optional, for Docker operations)
- **Searches ~/ directory for compose.yml** (optional, for Docker compose operations)

## License

This script is provided as-is for system maintenance purposes. Use at your own discretion and always test in a safe environment first.
