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
- **Pending Actions Summary**: Provides a clear, consolidated list of required follow-up actions, such as system reboots, at the end of the script.
- **Docker Container Management**: Only restarts containers when updates are detected
- **Vim Plugin Management**: Automatically updates Vim plugins (Vundle).
- **Tmux Plugin Management**: Automatically updates tmux plugins via TPM if `~/.tmux/plugins/tpm` is present.
- **Oh My Zsh**: Keeps your Oh My Zsh installation up-to-date (macOS only).
- **Graceful Fallbacks**: Skips unavailable package managers without errors

## Functionality by Operating System

### 🐧 Linux (Ubuntu/Debian)

#### System Packages
- `sudo apt update` - Update package lists
- `sudo apt upgrade` - Upgrade installed packages

#### Additional Package Managers
- **Snap Packages**: `sudo snap refresh`
- **Flatpak**: `flatpak update --appstream && flatpak update -y`
- **Firmware**: `fwupdmgr refresh && fwupdmgr get-updates` — the script defaults to auto-yes and will automatically apply firmware updates when detected (it will run `fwupdmgr refresh --force` then `fwupdmgr update` when applying). If you prefer prompts, run the script with `-i/--interactive` to confirm before applying. Use `--apply-firmware` or set `"apply-firmware": true` in the config to enable unattended apply; use `--skip-firmware` to skip firmware checks entirely.

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
  - **Automatic service restart with user confirmation** (or use `--service-restart` to skip confirmation)
  - System reboot prompt with 10-second countdown

#### Additional Package Managers
- **Snap Packages**: `sudo snap refresh`
- **Flatpak**: `flatpak update --appstream && flatpak update -y`
- **Firmware**: `fwupdmgr refresh && fwupdmgr get-updates` — the script defaults to auto-yes and will automatically apply firmware updates when detected (it will run `fwupdmgr refresh --force` then `fwupdmgr update` when applying). If you prefer prompts, run the script with `-i/--interactive` to confirm before applying. Use `--apply-firmware` or set `"apply-firmware": true` in the config to enable unattended apply; use `--skip-firmware` to skip firmware checks entirely.

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

#### Developer Tools
- **Ruby Gems**: `gem outdated --user-install && gem update --user-install` (user gems only)
- **npm**: Global and user packages (`npm outdated -g && npm update -g`, `npm outdated && npm update`)
- **pip3**: System and user Python packages with separate handling
- **Vim Plugins**: `vim +PluginUpdate +qall` (Vundle, if installed)
- **Tmux Plugins**: `~/.tmux/plugins/tpm/update_plugins all` (TPM, if installed)
- **Oh My Zsh**: `omz update` (if installed)
- **Docker**: Compose pull/restart + system prune

---
## Docker Operations (All Platforms)

### Docker Compose (searches ~/ directory and prompts to add compose.yml)
- **Smart Pull**: `docker-compose pull` with update detection
- **Conditional Restart**: Only restarts containers when updates are detected
- **Update Detection**: Scans pull output for actual image updates

### Restart Behaviour
When container image updates are detected the script performs a targeted restart:

1. Parses the `docker-compose.yml` to build a dependency graph
2. Identifies which containers use the updated images
3. Walks the dependency graph to find all affected dependents
4. Stops only those containers in reverse dependency order
5. Runs `docker-compose up -d` to bring everything back up in the correct order with full health check awareness

This means unrelated containers are never restarted, minimising downtime.

If the compose file cannot be parsed, the script falls back to a full stack restart automatically.

> ℹ️ **Note:** PyYAML is required for docker-compose dependency graph parsing and is automatically installed with the Homebrew formula.

### Docker Maintenance
- **System Cleanup**: `docker system prune` with auto-confirmation (dangling images only — layer cache is preserved to ensure accurate update detection on subsequent runs)

---

## Installation

### Option 1: Homebrew (macOS/Linux)
```bash
# Add the tap
brew tap waynelloyd/system-updater

# Install system-updater (includes PyYAML for docker-compose support)
brew install system-updater

# Run it
system-updater
```

### Option 2: Manual Installation
```bash
# Download and make executable
curl -fsSL https://raw.githubusercontent.com/waynelloyd/homebrew-system-updater/refs/heads/main/system-updater.py -o system-updater
chmod +x system-updater
sudo mv system-updater /usr/local/bin/

# Install PyYAML for docker-compose support
pip3 install PyYAML>=6.0
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
system-updater --skip-os-updates

# Skip snap packages (Linux)
system-updater --skip-snap

# Skip Flatpak updates (Linux)
system-updater --skip-flatpak

# Skip firmware updates (Linux)
system-updater --skip-firmware

# Skip pip package updates
system-updater --skip-pip

# Skip Vim plugin updates
system-updater --skip-vim

# Skip Tmux plugin updates (TPM)
system-updater --skip-tmux

# Skip Oh My Zsh update (macOS)
system-updater --skip-omz


# Skip Docker operations
system-updater --skip-docker-pull --skip-docker-prune
```

## Configuration file

The script supports a per-user config file at `~/.config/system-updater/config.json`. Keys in this file are used as defaults for command-line flags (you can still pass flags on the command-line to override them).

Example `~/.config/system-updater/config.json`:

```json
{
  "skip-docker-prune": true,
  "skip-tmux": true,
  "apply-firmware": false
}
```

Both hyphenated and underscored key styles are accepted (e.g. `skip-docker-prune` or `skip_docker_prune`).

Tip: run `system-updater --help` to see a short config-file example in the help output.

### Interactive Configuration

You can run an interactive configuration wizard to write `~/.config/system-updater/config.json`:

```bash
system-updater --configure
```

To print the effective configuration (config file merged with CLI flags):

```bash
system-updater --print-config
```

### Tmux plugin updates

Tmux plugin updates are performed automatically when TPM is installed at `~/.tmux/plugins/tpm`. They run by default as part of the normal update flow unless you explicitly skip them with `--skip-tmux` or set `skip-tmux` in the config file. Example:

```json
{
  "skip-tmux": true
}
```

Note: TPM updates run by default (no separate "run-only" flag). To skip them permanently set `skip-tmux` in `~/.config/system-updater/config.json` or pass `--skip-tmux` on the command-line.

### Command Line Options
```bash
system-updater --help
```

**Available Options:**
- `-i, --interactive` - Interactive mode with prompts (default is auto-yes)
- `--skip-os-updates` - Skip system package updates
- `--skip-snap` - Skip snap refresh (Linux only)
- `--skip-flatpak` - Skip Flatpak updates (Linux only)
- `--skip-pip` - Skip pip package updates
- `--skip-vim` - Skip Vim plugin updates
- `--skip-tmux` - Skip tmux plugin updates (TPM)
- `--skip-omz` - Skip Oh My Zsh update (macOS only)
- `--skip-firmware` - Skip firmware updates (Linux only)
- `--skip-docker-pull` - Skip docker-compose pull
- `--skip-docker-prune` - Skip docker system prune
- `--apply-firmware` - Automatically apply firmware updates when detected (runs a forced refresh and applies updates). Use with caution on servers.
- `--service-restart` - **Fedora/RHEL only**. Automatically restart services detected by `dnf needs-restarting` without confirmation. If not set, you will be prompted to confirm service restarts (y/n).
- `--print-config` - Print the effective configuration (config file merged with CLI flags) and exit.
- `--configure` - Launch the interactive configurator to create or update `~/.config/system-updater/config.json` and exit.

**Failure summary behavior:** The script now collects failures and issues encountered during individual tasks and prints an "ISSUES / FAILURES" section at the end of the run. If any failures were recorded the script will exit with a non-zero exit code so you can detect problems in automation.

## Examples

### Complete System Update
```bash
# Update everything (auto-yes by default)
system-updater
```

### Development Environment Update
```bash
# Update only development tools
system-updater --skip-os-updates --skip-firmware
```

### Server Maintenance
```bash
# Update system packages and Docker, skip desktop apps
system-updater --skip-snap --skip-flatpak
```

## Safety Features

- **Service Restart Confirmation**: Always prompts before restarting services (unless `--service-restart` is used)
- **System Reboot Safety**: Requires manual confirmation even with `-y` flag
- **Pending Actions Summary**: Summarizes all required manual steps (like reboots) at the end, so you don't miss anything.
- **Graceful Failures**: Continues operation if individual package managers fail, and records failures for later review.
- **Update Detection**: Only restarts Docker containers when actual updates occur
- **Comprehensive Logging**: Clear output showing what's being updated and why

## Output Example

```
🚀 Starting system update process...
Mode: Auto-yes
Detected OS: macos

==================================================
Running: Updating Homebrew
Command: brew update
==================================================
✅ Updating Homebrew completed successfully

...
(other updates)
...

==================================================
🔔 PENDING ACTIONS
==================================================
  - A restart is required to complete the installation of some macOS updates.

==================================================
🔧 ISSUES / FAILURES
==================================================
  - Docker-compose pull failed in /home/user/projects/app with exit code 1 (command: docker-compose pull)

📊 SUMMARY
==================================================
Tasks completed successfully: 10/11
⚠️  Some tasks failed or need attention. Check the 'ISSUES / FAILURES' and output above for details.
```

## Requirements

- **Python 3.6+**
- **sudo privileges** (for system package updates)
- **Docker** (optional, for Docker operations)
- **PyYAML** (required for docker-compose operations, automatically installed with Homebrew)
- **Searches ~/ directory for compose.yml** (optional, for Docker compose operations)

## License

This script is provided as-is for system maintenance purposes. Use at your own discretion and always test in a safe environment first.

## Changelog

### v1.1.8
- **Added**: Progress bar (spinner) for docker-compose up -d operations to show activity during container updates
- **Improved**: Service restart logic now detects user services (systemctl --user) vs. system services (sudo systemctl) and uses the appropriate command

### v1.1.7
- **Fixed**: Docker-compose updates now properly remove stopped dependent containers before recreating providers, preventing "container already exists" errors during sidecar dependant container updates

### v1.1.6
- **Changed**: PyYAML is now a required dependency instead of optional, simplifying installation and removing runtime error handling
- **Removed**: MacUpdater support completely removed from the script and documentation
- **Homebrew**: Updated to use system Python instead of requiring Homebrew's Python version, and always install PyYAML>=6.0 in the virtualenv
- **Simplified**: Removed optional dependency checks and error handling for missing PyYAML

### v1.1.5
- Fixed: `:latest` tag stripped from image names in digest comparison to match compose file references that omit the tag, ensuring correct restart target identification

### v1.1.4
- Added: `import yaml` to handle docker-compose parsing correctly
- Fixed: Improved targeted restart logic — now only explicitly stops network-dependent sidecars (`network_mode: service:` or `network_mode: container:`) of updated services
- Fixed: Reliably use `docker-compose up -d` to handle recreation of updated services and restart of dependents in the correct order, avoiding unnecessary full-stack restarts
- Improved: Code cleanup — removed unused variables and redundant function parameters
- Fixed: Removed debug output lines for cleaner production release
- Fixed: Prevented duplicate image entries in updated containers summary by adding deduplication logic

### v1.1.3
- Fixed:  Fixed detect when sidecar containers in podman are in the restart targets and fall back to a full docker-compose down/up to fix dependant containers error

### v1.1.2
- Fixed: Digest-pinned images with `@sha256:` references (e.g. immich-app/postgres) no longer appear as `<none>` in the updated containers list or trigger false restarts

### v1.1.1
- Fixed: Image update detection completely reworked — now uses pre/post pull image ID comparison via `docker images` instead of parsing Podman pull output, eliminating false positives on every run
- Fixed: Digest-pinned images (e.g. containers with `@sha256:` tag) now tracked correctly by stripping `<none>` tags and using repository name as key
- Fixed: `docker.io/library/` prefix normalised so official Docker Hub images (nginx, redis, postgres etc.) are compared correctly
- Fixed: Removed unreliable `Pulling fs layer` based live progress tracking which caused duplicate download messages due to parallel pull interleaving
- Simplified: `stream_reader` and `plain_reader` merged into single function since progress tracking moved to digest comparison
- Simplified: `downloading_images` and `current_image` tracking removed as no longer needed

### v1.1.0
- Added: Targeted container restart — only stops containers affected by updates and their dependents, leaving unrelated containers running
- Added: Compose file dependency graph parser using PyYAML to determine restart scope
- Added: `network_mode: container:` awareness in dependency graph. podman-docker comptibility doesn't handle this well 
- Added: Live pull progress output — shows which images are downloading with spinner between updates
- Fixed: Image update detection now tracks layer-level activity (`Pulling fs layer`) rather than matching `Image ... Pulled` which fired for all checked images
- Fixed: Duplicate image entries in updated containers summary caused by thread race condition
- Fixed: Garbled Podman terminal output during pull by setting `TERM=dumb` and `NO_COLOR=1`
- Fixed: stdout and stderr both being parsed for pull progress causing duplicate detections — stdout now uses a plain reader
- Changed: `docker system prune -a` replaced with `docker system prune` to preserve image layer cache and prevent false positive update detection on consecutive runs
- Changed: Restart logic no longer requires full `docker-compose down` — targeted stop followed by `docker-compose up -d` handles all runtimes including Podman
