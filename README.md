# System Updater Script

A comprehensive cross-platform system update script that handles package management, service restarts, and Docker maintenance across Linux and macOS systems.

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
- **MacUpdater**: Scan and update Mac applications

#### Developer Tools
- **Ruby Gems**: `gem outdated && gem update`
- **npm**: `npm outdated -g && npm update -g` (global packages)
- **pip3**: Updates outdated Python packages
- **Docker**: Compose pull/restart + system prune

---

## Docker Operations (All Platforms)

### Docker Compose (~/ganymede directory)
- **Smart Pull**: `docker-compose pull` with update detection
- **Conditional Restart**: `docker-compose up -d` only if updates found
- **Update Detection**: Scans pull output for actual image updates

### Docker Maintenance
- **System Cleanup**: `docker system prune -a` with auto-confirmation

---

## Installation Requirements

### Linux
```bash
# Ubuntu/Debian
sudo apt install python3 flatpak fwupd dnf-utils

# Fedora/RHEL
sudo dnf install python3 flatpak fwupd dnf-utils
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
# Run all updates with auto-confirmation
python3 system_updater.py -y

# Run with manual confirmation prompts
python3 system_updater.py
```

### Skip Specific Operations
```bash
# Skip system package updates
python3 system_updater.py --skip-system

# Skip snap packages (Linux)
python3 system_updater.py --skip-snap

# Skip Flatpak updates (Linux)
python3 system_updater.py --skip-flatpak

# Skip firmware updates (Linux)
python3 system_updater.py --skip-firmware

# Skip pip package updates
python3 system_updater.py --skip-pip

# Skip Mac App Store updates (macOS)
python3 system_updater.py --skip-mac-apps

# Skip Docker operations
python3 system_updater.py --skip-docker-pull --skip-docker-prune
```

### Command Line Options
```bash
python3 system_updater.py --help
```

**Available Options:**
- `-y, --yes` - Automatically answer yes to prompts
- `--skip-system` - Skip system package updates
- `--skip-snap` - Skip snap refresh (Linux only)
- `--skip-flatpak` - Skip Flatpak updates (Linux only)
- `--skip-pip` - Skip pip package updates
- `--skip-mac-apps` - Skip Mac application updates (macOS only)
- `--skip-firmware` - Skip firmware updates (Linux only)
- `--skip-docker-pull` - Skip docker-compose pull
- `--skip-docker-prune` - Skip docker system prune

## Examples

### Complete System Update
```bash
# Update everything with auto-confirmation
python3 system_updater.py -y
```

### Development Environment Update
```bash
# Update only development tools
python3 system_updater.py --skip-system --skip-firmware -y
```

### Server Maintenance
```bash
# Update system packages and Docker, skip desktop apps
python3 system_updater.py --skip-snap --skip-flatpak --skip-mac-apps -y
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
Auto-yes mode: ON
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
- **~/ganymede directory with docker-compose.yml** (optional, for Docker compose operations)

## License

This script is provided as-is for system maintenance purposes. Use at your own discretion and always test in a safe environment first.
