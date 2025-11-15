#!/usr/bin/env python3
"""
System Update Script
Handles updates for Fedora/Ubuntu, snap refresh, docker-compose pull, and docker system prune
"""

import subprocess
import sys
import os
import argparse
import platform
import json
from pathlib import Path
import time
import itertools

# Define the script version. Remember to update this for each new release.
__version__ = "1.0.6"

# Global list to store pending actions
pending_actions = []
# Global list to store failures/issues that need attention
failures = []

def run_command(command, description, auto_yes=False):
    """Run a command and handle output, recording failures into `failures`"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*50}")
    
    try:
        if auto_yes and '-y' not in command:
            # Add -y flag for commands that support it
            if any(cmd in command for cmd in ['apt', 'dnf', 'yum']):
                command.append('-y')
        
        result = subprocess.run(command, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        msg = f"{description} failed with exit code {e.returncode} (command: {' '.join(command)})"
        print(f"❌ {msg}")
        failures.append(msg)
        return False
    except FileNotFoundError:
        msg = f"Command not found: {command[0]} (command: {' '.join(command)})"
        print(f"❌ {msg}")
        failures.append(msg)
        return False

def get_config_file():
    """Get the path to the configuration file"""
    config_dir = Path.home() / '.config' / 'system-updater'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'config.json'

def load_config():
    """Load configuration from file"""
    config_file = get_config_file()
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}

def save_config(config):
    """Save configuration to file"""
    config_file = get_config_file()
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError:
        print(f"⚠️  Could not save config to {config_file}")
        return False

def find_docker_compose_files():
    """Find docker-compose files in user's home directory"""
    home = Path.home()
    compose_files = []
    
    # Common compose file names
    compose_names = ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']
    
    # Search in home directory and common subdirectories
    search_paths = [
        home,
        home / 'docker',
        home / 'projects',
        home / 'dev',
        home / 'development',
    ]
    
    # Add any directories that contain docker-compose files
    for search_path in search_paths:
        if search_path.exists() and search_path.is_dir():
            try:
                for compose_name in compose_names:
                    compose_files.extend(search_path.glob(f'**/{compose_name}'))
            except PermissionError:
                continue
    
    # Remove duplicates and filter out container overlay paths
    unique_dirs = list(set(f.parent for f in compose_files))
    
    # Filter out container storage overlay paths (podman/docker internal paths)
    filtered_dirs = []
    for dir_path in unique_dirs:
        path_str = str(dir_path)
        # Skip container overlay storage paths
        if '/.local/share/containers/storage/overlay/' in path_str:
            continue
        # Skip other temporary/cache paths
        if any(skip in path_str for skip in ['/tmp/', '/.cache/', '/var/tmp/']):
            continue
        filtered_dirs.append(dir_path)
    
    return sorted(filtered_dirs)

def setup_docker_compose_config(auto_yes=False):
    """Setup docker-compose configuration on first run"""
    config = load_config()
    
    if 'docker_compose_setup_done' in config:
        return config.get('docker_compose_paths', [])
    
    print(f"\n{'='*60}")
    print("🐳 DOCKER-COMPOSE SETUP")
    print(f"{'='*60}")
    print("Searching for docker-compose files in your home directory...")
    
    compose_dirs = find_docker_compose_files()
    
    if not compose_dirs:
        print("ℹ️  No docker-compose files found in common locations")
        if not auto_yes:
            enable_docker = input("Would you like to enable Docker operations anyway? (y/N): ").lower().startswith('y')
        else:
            enable_docker = False
        
        config['docker_compose_setup_done'] = True
        config['docker_compose_enabled'] = enable_docker
        config['docker_compose_paths'] = []
        save_config(config)
        return []
    
    print(f"\n📋 Found docker-compose files in {len(compose_dirs)} location(s):")
    for i, path in enumerate(compose_dirs, 1):
        compose_files = []
        for name in ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']:
            if (path / name).exists():
                compose_files.append(name)
        print(f"  {i}. {path} ({', '.join(compose_files)})")
    
    # Always prompt on first setup, regardless of auto-yes mode
    print(f"\nWould you like to enable docker-compose operations for these locations?")
    print("Options:")
    print("  a) Enable all locations")
    print("  s) Select specific locations")
    print("  n) Disable docker-compose operations")
    
    choice = input("Choice (a/s/n): ")


    if choice == 'n':
        selected_paths = []
    elif choice == 's':
        selected_paths = []
        for i, path in enumerate(compose_dirs, 1):
            enable = input(f"Enable {path}? (y/N): ").lower().startswith('y')
            if enable:
                selected_paths.append(path)
    else:  # 'a' or default
        selected_paths = compose_dirs
    
    config['docker_compose_setup_done'] = True
    config['docker_compose_enabled'] = len(selected_paths) > 0
    config['docker_compose_paths'] = [str(p) for p in selected_paths]
    save_config(config)
    
    if selected_paths:
        print(f"✅ Docker-compose operations enabled for {len(selected_paths)} location(s)")
    else:
        print("ℹ️  Docker-compose operations disabled")
    
    return selected_paths

def detect_os():
    """Detect the operating system"""
    system = platform.system().lower()
    
    if system == 'darwin':
        return 'macos'
    elif system == 'linux':
        return detect_linux_distro()
    else:
        return 'unknown'

def detect_linux_distro():
    """Detect the Linux distribution"""
    try:
        with open('/etc/os-release', 'r') as f:
            content = f.read().lower()
            if 'ubuntu' in content or 'debian' in content:
                return 'ubuntu'
            elif 'fedora' in content:
                return 'fedora'
            elif 'centos' in content or 'rhel' in content:
                return 'rhel'
    except FileNotFoundError:
        pass
    
    # Fallback detection
    if os.path.exists('/usr/bin/apt'):
        return 'ubuntu'
    elif os.path.exists('/usr/bin/dnf'):
        return 'fedora'
    elif os.path.exists('/usr/bin/yum'):
        return 'rhel'
    
    return 'linux_unknown'

def update_vim_plugins(auto_yes=False):
    """Update Vim plugins using Vundle"""
    vundle_path = Path.home() / '.vim' / 'bundle' / 'Vundle.vim'
    if not vundle_path.exists():
        return True # Skip silently if Vundle not installed
        
    return run_command(['vim', '+PluginUpdate', '+qall'], "Updating Vim plugins")

# New: update tmux plugins via TPM if present (~/.tmux/plugins/tpm)
def update_tmux_plugins(auto_yes=False):
    """Update tmux plugins using TPM if installed (~/.tmux/plugins/tpm).

    This locates the TPM update_plugins script in common locations (including
    ~/.tmux/plugins/tpm/bin/update_plugins), ensures the tmux server is started,
    and runs the script with bash. Failures are recorded in the global
    `failures` list but don't stop the rest of the run.
    """
    tpm_base = Path.home() / '.tmux' / 'plugins' / 'tpm'
    if not tpm_base.exists():
        return True  # TPM not installed, skip silently

    # Common candidate locations for the update script
    candidates = [
        tpm_base / 'bin' / 'update_plugins',
        tpm_base / 'update_plugins',
        tpm_base / 'scripts' / 'update_plugins',
    ]

    update_script = None
    for cand in candidates:
        if cand.exists():
            update_script = cand
            break

    if not update_script:
        # Not found, skip silently but record a warning for visibility
        msg = f"TPM update script not found in {tpm_base} (checked {', '.join(str(p) for p in candidates)})"
        print(f"⚠️  {msg}")
        failures.append(msg)
        return False

    print(f"\n{'='*50}")
    print("Running: Updating tmux plugins (TPM)")
    print(f"Script: {update_script} all")
    print(f"{'='*50}")

    # Ensure tmux server is available - start it if necessary (no-op if already running)
    try:
        subprocess.run(['tmux', 'start-server'], check=False, capture_output=True)
    except FileNotFoundError:
        msg = "tmux command not found; cannot update tmux plugins"
        print(f"❌ {msg}")
        failures.append(msg)
        return False

    # Execute the update script using bash (more portable than direct exec)
    try:
        subprocess.run(['bash', str(update_script), 'all'], check=True, capture_output=False)
        print("✅ tmux plugins updated successfully")
        return True
    except subprocess.CalledProcessError as e:
        msg = f"tmux plugin update failed with exit code {e.returncode} (command: {update_script} all)"
        print(f"❌ {msg}")
        failures.append(msg)
        return False
    except Exception as e:
        msg = f"tmux plugin update encountered an error: {e}"
        print(f"⚠️  {msg}. Continuing...")
        failures.append(msg)
        return False

def update_oh_my_zsh(auto_yes=False):
    """Update Oh My Zsh framework"""
    from pathlib import Path
    oh_my_zsh_path = Path.home() / '.oh-my-zsh'
    upgrade_script = oh_my_zsh_path / 'tools' / 'upgrade.sh'
    if not oh_my_zsh_path.exists() or not upgrade_script.exists():
        return True # Skip silently if not installed or upgrade script missing

    # Run the upgrade script directly with zsh
    command = ['zsh', str(upgrade_script)]
    try:
        result = subprocess.run(command, check=False, capture_output=False)
        print("✅ Oh My Zsh update completed (exit code: {}), continuing...".format(result.returncode))
        return True
    except Exception as e:
        print(f"⚠️  Oh My Zsh update encountered an error: {e}. Continuing...")
        return True

def update_macos_system_software(auto_yes=False):
    """Update macOS system software using softwareupdate"""
    print(f"\n{'='*50}")
    print("Running: Installing macOS system updates")
    print(f"Command: softwareupdate -ia")
    print(f"{'='*50}")
    
    try:
        # Install all updates (softwareupdate -ia checks and installs)
        result = subprocess.run(['softwareupdate', '-ia'], 
                              check=True, capture_output=True, text=True)
        
        # Check if a restart is required
        if any(phrase in result.stdout for phrase in ["restart", "reboot"]):
            pending_actions.append("A restart is required to complete the installation of some macOS updates.")

        # Only print success if updates were actually installed
        if "No new software available" not in result.stdout and result.stdout.strip():
            print("✅ macOS system updates installed successfully")
        
        return True
        
    except subprocess.CalledProcessError as e:
        # Check if it's just "no updates available"
        if e.stdout and "No new software available" in e.stdout:
            return True  # No updates, return silently
        print(f"❌ Installing macOS system updates failed with exit code {e.returncode}")
        return False

def update_homebrew_packages(auto_yes=False):
    """Update macOS packages using Homebrew"""
    # Check if brew is installed
    try:
        subprocess.run(['brew', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return True  # Skip silently if not installed
    
    success = True
    
    # Update Homebrew itself
    if not run_command(['brew', 'update'], "Updating Homebrew"):
        success = False
    
    # Upgrade formulae
    if not run_command(['brew', 'upgrade'], "Upgrading Homebrew formulae"):
        success = False
    
    # Upgrade casks
    if not run_command(['brew', 'upgrade', '--cask'], "Upgrading Homebrew casks"):
        success = False
    
    # Remove outdated downloads
    if not run_command(['brew', 'autoremove'], "Removing outdated Homebrew downloads"):
        success = False
    
    # Cleanup old versions
    if not run_command(['brew', 'cleanup'], "Cleaning up Homebrew"):
        success = False
    
    return success

def update_mas_apps(auto_yes=False):
    """Update Mac App Store applications using mas CLI"""
    # Check if mas is installed
    try:
        subprocess.run(['mas', 'version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return True  # Skip silently if not installed
    
    # Check for outdated apps
    print(f"\n{'='*50}")
    print("Running: Checking for Mac App Store updates")
    print(f"Command: mas outdated")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(['mas', 'outdated'], 
                              check=True, capture_output=True, text=True)
        
        if not result.stdout.strip():
            print("✅ No Mac App Store updates available")
            return True
        
        print("📋 Available App Store updates:")
        print(result.stdout)
        
        # Update all apps
        return run_command(['mas', 'upgrade'], "Updating Mac App Store applications")
        
    except subprocess.CalledProcessError:
        print("⚠️  Could not check Mac App Store updates")
        return True

def update_ruby_gems(auto_yes=False):
    """Update Ruby gems (user only)"""
    # Check if gem is installed
    try:
        subprocess.run(['gem', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return True  # Skip silently if not installed
    
    # Check if user has any gems installed first
    try:
        list_result = subprocess.run(['gem', 'list', '--user-install'], 
                                   check=True, capture_output=True, text=True)
        if not list_result.stdout.strip() or "no gems" in list_result.stdout.lower():
            return True  # No user gems installed, skip silently
    except subprocess.CalledProcessError:
        return True  # Can't check, skip silently
    
    # Update user gems only (avoid system permission issues)
    print(f"\n{'='*50}")
    print("Running: Checking for outdated user Ruby gems")
    print(f"Command: gem outdated --user-install")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(['gem', 'outdated', '--user-install'], 
                              check=True, capture_output=True, text=True)
        
        if result.stdout.strip():
            print("📋 Outdated user Ruby gems:")
            print(result.stdout)
            return run_command(['gem', 'update', '--user-install'], "Updating user Ruby gems")
        else:
            print("✅ No outdated user Ruby gems found")
            return True
        
    except subprocess.CalledProcessError:
        return True  # Skip silently if command fails

def update_npm_packages(auto_yes=False):
    """Update global and user npm packages"""
    # Check if npm is installed
    try:
        subprocess.run(['npm', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return True  # Skip silently if not installed
    
    success = True
    
    # Update global packages
    print(f"\n{'='*50}")
    print("Running: Checking for outdated global npm packages")
    print(f"Command: npm outdated -g")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(['npm', 'outdated', '-g'], 
                              check=True, capture_output=True, text=True)
        
        if result.stdout.strip():
            print("📋 Outdated global npm packages:")
            print(result.stdout)
            if not run_command(['npm', 'update', '-g'], "Updating global npm packages"):
                success = False
        else:
            print("✅ No outdated global npm packages found")
        
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:  # npm outdated returns 1 when there are outdated packages
            if e.stdout.strip():
                print("📋 Outdated global npm packages:")
                print(e.stdout)
                if not run_command(['npm', 'update', '-g'], "Updating global npm packages"):
                    success = False
            else:
                print("✅ No outdated global npm packages found")
        else:
            success = False
    
    # Update user packages (check if package.json exists in current directory)
    import os
    
    # Only check current directory for package.json (most common use case)
    has_local_packages = os.path.exists("package.json")
    
    if has_local_packages:
        print(f"\n{'='*50}")
        print("Running: Checking for outdated user npm packages")
        print(f"Command: npm outdated")
        print(f"{'='*50}")
        
        try:
            result = subprocess.run(['npm', 'outdated'], 
                                  check=True, capture_output=True, text=True)
            
            if result.stdout.strip():
                print("📋 Outdated user npm packages:")
                print(result.stdout)
                if not run_command(['npm', 'update'], "Updating user npm packages"):
                    success = False
            else:
                print("✅ No outdated user npm packages found")
            
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:  # npm outdated returns 1 when there are outdated packages
                if e.stdout.strip():
                    print("📋 Outdated user npm packages:")
                    print(e.stdout)
                    if not run_command(['npm', 'update'], "Updating user npm packages"):
                        success = False
                else:
                    print("✅ No outdated user npm packages found")
            # Don't fail overall for user package issues
    
    return success

def check_fedora_restart_needs(auto_yes=False, service_restart=False):
    """Check for services and system restart needs on Fedora/RHEL systems"""
    # Check if dnf is available
    try:
        subprocess.run(['dnf', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return True  # Skip silently if dnf not available

    print(f"\n{'='*50}")
    print("Running: Checking for restart requirements")
    print(f"Command: dnf needs-restarting")
    print(f"{'='*50}")

    # Check for services that need restarting
    services_result = subprocess.run(['dnf', 'needs-restarting', '-s'],
                                     capture_output=True, text=True, check=False)

    if services_result.returncode == 0:
        print("✅ No services need restarting")
    elif services_result.returncode == 1:
        if services_result.stdout.strip():
            services = services_result.stdout.strip().split('\n')
            print(f"🔄 Found {len(services)} services that need restarting:")
            for service in services:
                print(f"   - {service}")

            # Prompt for confirmation unless --service-restart is set
            if service_restart or (auto_yes and service_restart):
                restart_confirmed = True
            else:
                restart_confirmed = input("\n🤔 Restart these services automatically? (y/N): ").lower().startswith('y')
            if restart_confirmed:
                print("🔄 Restarting services...")
                for service in services:
                    service_name = service.strip()
                    if service_name:
                        run_command(['sudo', 'systemctl', 'restart', service_name],
                                  f"Restarting {service_name}")
            else:
                print("ℹ️  Services not restarted. You can restart them manually later.")
                pending_actions.append("Some services on your Fedora/RHEL system were not restarted. You may want to restart them manually.")
        else:
            print("✅ No services need restarting")
    else:
        print("⚠️  Could not check service restart requirements")
        if services_result.stderr:
            print(f"Error details: {services_result.stderr.strip()}")

    # Check if system reboot is needed
    reboot_result = subprocess.run(['dnf', 'needs-restarting', '-r'],
                                   capture_output=True, text=True, check=False)

    if reboot_result.returncode == 0:
        print("✅ System reboot not required")
    elif reboot_result.returncode == 1:
        print("🚨 SYSTEM REBOOT REQUIRED")
        print("   Some updates require a system restart to take effect")
        pending_actions.append("A system reboot is required for some updates to take effect on your Fedora/RHEL system.")

        if auto_yes:
            print("⚠️  Auto-yes mode enabled, but system reboot requires manual confirmation")
            print("   Please reboot your system when convenient")
        else:
            reboot_choice = input("\n🤔 Reboot system now? (y/N): ").lower()
            if reboot_choice.startswith('y'):
                print("🔄 Initiating system reboot in 10 seconds...")
                print("   Press Ctrl+C to cancel")
                try:
                    subprocess.run(['sleep', '10'], check=True)
                    subprocess.run(['sudo', 'reboot'], check=True)
                except KeyboardInterrupt:
                    print("\n❌ Reboot cancelled")
                except subprocess.CalledProcessError:
                    print("❌ Failed to initiate reboot")
            else:
                print("ℹ️  System reboot postponed. Please reboot when convenient.")
    else:
        print("⚠️  Could not determine if system reboot is needed")
        if reboot_result.stderr:
            print(f"Error details: {reboot_result.stderr.strip()}")

    return True

def refresh_snaps(auto_yes=False):
    """Refresh snap packages (Linux only)"""
    os_type = detect_os()
    if os_type == 'macos':
        return True  # Skip silently on macOS
    
    # Check if snap is installed
    try:
        subprocess.run(['snap', '--version'], check=True, capture_output=True)
        return run_command(['sudo', 'snap', 'refresh'], "Refreshing snap packages")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return True  # Skip silently if not installed

def update_flatpaks(auto_yes=False):
    """Update Flatpak packages (Linux only)"""
    os_type = detect_os()
    if os_type == 'macos':
        return True  # Skip silently on macOS
    
    # Check if flatpak is installed
    try:
        subprocess.run(['flatpak', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return True  # Skip silently if not installed
    
    success = True
    
    # Update flatpak repositories
    if not run_command(['flatpak', 'update', '--appstream'], "Updating Flatpak repositories"):
        success = False
    
    # Update flatpak applications
    if not run_command(['flatpak', 'update', '-y'], "Updating Flatpak applications"):
        success = False
    
    return success

def update_pip_packages(auto_yes=False):
    """Update pip packages (system and user)"""
    # Check if pip3 is installed
    try:
        subprocess.run(['pip3', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return True  # Skip silently if not installed
    
    success = True
    
    # Update system pip packages
    print(f"\n{'='*50}")
    print("Running: Updating system pip packages")
    print(f"Command: pip3 list --outdated --format=columns")
    print(f"{'='*50}")
    
    try:
        # Get outdated system packages
        result = subprocess.run(['pip3', 'list', '--outdated', '--format=columns'], 
                              check=True, capture_output=True, text=True)
        
        if result.stdout.strip() and len(result.stdout.strip().split('\n')) > 2:
            # Extract package names (skip header lines)
            lines = result.stdout.strip().split('\n')[2:]  # Skip first 2 header lines
            packages = [line.split()[0] for line in lines if line.strip()]
            
            if packages:
                print(f"📋 Found {len(packages)} outdated system packages: {', '.join(packages)}")
                
                # Upgrade each package
                for package in packages:
                    try:
                        subprocess.run(['pip3', 'install', '-U', package], check=True, capture_output=False)
                    except subprocess.CalledProcessError:
                        print(f"⚠️  Failed to update {package}")
                        success = False
                
                print("✅ System pip packages updated")
            else:
                print("✅ No outdated system pip packages found")
        else:
            print("✅ No outdated system pip packages found")
        
    except subprocess.CalledProcessError:
        print("⚠️  Could not check system pip packages")
        success = False
    
    # Update user pip packages
    print(f"\n{'='*50}")
    print("Running: Updating user pip packages")
    print(f"Command: pip3 list --user --outdated --format=columns")
    print(f"{'='*50}")
    
    try:
        # Get outdated user packages
        result = subprocess.run(['pip3', 'list', '--user', '--outdated', '--format=columns'], 
                              check=True, capture_output=True, text=True)
        
        if result.stdout.strip() and len(result.stdout.strip().split('\n')) > 2:
            # Extract package names (skip header lines)
            lines = result.stdout.strip().split('\n')[2:]  # Skip first 2 header lines
            packages = [line.split()[0] for line in lines if line.strip()]
            
            if packages:
                print(f"📋 Found {len(packages)} outdated user packages: {', '.join(packages)}")
                
                # Upgrade each package
                for package in packages:
                    try:
                        subprocess.run(['pip3', 'install', '--user', '-U', package], check=True, capture_output=False)
                    except subprocess.CalledProcessError:
                        print(f"⚠️  Failed to update user package {package}")
                        # Don't fail overall for user package failures
                
                print("✅ User pip packages updated")
            else:
                print("✅ No outdated user pip packages found")
        else:
            print("✅ No outdated user pip packages found")
        
    except subprocess.CalledProcessError:
        print("⚠️  Could not check user pip packages")
        # Don't fail overall if user packages check fails
    
    return success

def update_mac_apps(auto_yes=False):
    """Update Mac applications using MacUpdater"""
    os_type = detect_os()
    if os_type != 'macos':
        return True  # Skip silently on non-macOS
    
    macupdater_path = '/Applications/MacUpdater.app/Contents/Resources/macupdater_client'
    
    if not os.path.exists(macupdater_path):
        return True  # Skip silently if MacUpdater not installed
    
    # Scan for updates
    if not run_command([macupdater_path, 'scan'], "Scanning for Mac app updates"):
        return False
    
    # Apply updates
    return run_command([macupdater_path, 'update'], "Updating Mac applications")

def update_firmware(auto_yes=False, apply_firmware=False):
    """Update firmware using fwupdmgr (Linux only).

    Behavior:
      - Run `fwupdmgr refresh` (non-forced) and handle exit codes (treat 2 as warning).
      - Run `fwupdmgr get-updates` to detect available updates.
      - If updates are available, prompt the user to confirm applying them (unless auto_yes).
      - If confirmed, perform a forced refresh (`fwupdmgr refresh --force`) for robustness, then apply updates.
    """
    os_type = detect_os()
    if os_type == 'macos':
        return True  # Skip silently on macOS
    
    # Check if fwupdmgr is installed
    try:
        subprocess.run(['sudo', 'fwupdmgr', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        msg = "fwupdmgr not found or not installed. Install with: sudo apt install fwupd (Ubuntu) or sudo dnf install fwupd (Fedora)"
        print(f"⚠️  {msg}")
        failures.append(msg)
        return True
    
    # Refresh firmware metadata (normal refresh)
    print(f"\n{'='*50}")
    print("Running: Refreshing firmware metadata")
    refresh_cmd = ['sudo', 'fwupdmgr', 'refresh']
    print(f"Command: {' '.join(refresh_cmd)}")
    print(f"{'='*50}")
    
    try:
        # Run without raising on non-zero so we can handle specific fwupdmgr exit codes gracefully
        refresh_result = subprocess.run(refresh_cmd, check=False, capture_output=True, text=True)

        if refresh_result.returncode == 0:
            print("✅ Firmware metadata refreshed successfully")
        elif refresh_result.returncode == 2:
            # Exit code 2 is commonly used by fwupdmgr to indicate non-fatal conditions
            # (e.g. UEFI capsule updates not available). Treat this as a warning and continue.
            print("⚠️  Firmware metadata refresh returned exit code 2 - non-fatal (capsules unsupported or similar). Continuing...")
            if refresh_result.stdout:
                print(refresh_result.stdout.strip())
            if refresh_result.stderr:
                print(refresh_result.stderr.strip())
        else:
            # Other non-zero exit codes are unexpected; record as a failure for visibility
            print(f"⚠️  Firmware metadata refresh failed with exit code {refresh_result.returncode}")
            if refresh_result.stdout:
                print("STDOUT:", refresh_result.stdout)
            if refresh_result.stderr:
                print("STDERR:", refresh_result.stderr)
            failures.append(f"Firmware metadata refresh failed with exit code {refresh_result.returncode}")
    except Exception as e:
        # Catch any unexpected exception from subprocess.run so the script can continue
        print(f"⚠️  Exception while refreshing firmware metadata: {e}")
        failures.append(f"fwupdmgr refresh exception: {e}")

    # Check for available firmware updates
    print(f"\n{'='*50}")
    print("Running: Checking for firmware updates")
    get_updates_cmd = ['sudo', 'fwupdmgr', 'get-updates']
    print(f"Command: {' '.join(get_updates_cmd)}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(get_updates_cmd, 
                              check=True, capture_output=True, text=True)
        
        if "No updates available" in result.stdout or not result.stdout.strip():
            print("ℹ️  No firmware updates available")
            return True
        
        print("📋 Available firmware updates:")
        print(result.stdout)
        
        # Decide whether to apply updates: apply if --apply-firmware was set, or in auto_yes mode,
        # otherwise prompt the user for confirmation.
        if apply_firmware or auto_yes:
            apply_confirm = True
        else:
            apply_confirm = input("\n🤔 Apply these firmware updates now? (y/N): ").lower().startswith('y')

        if not apply_confirm:
            print("ℹ️  Firmware updates were not applied. You can run 'fwupdmgr update' manually later.")
            pending_actions.append("Firmware updates are available but were not applied automatically.")
            return True

        # User confirmed: perform a forced refresh before applying updates for robustness
        print(f"\n{'='*50}")
        print("Running: Refreshing firmware metadata (forced)")
        force_refresh_cmd = ['sudo', 'fwupdmgr', 'refresh', '--force']
        print(f"Command: {' '.join(force_refresh_cmd)}")
        print(f"{'='*50}")
        try:
            subprocess.run(force_refresh_cmd, check=False, capture_output=True, text=True)
        except Exception:
            # Non-fatal; we'll attempt to apply updates anyway and capture failures
            pass

        # Apply firmware updates
        command = ['sudo', 'fwupdmgr', 'update']
        if auto_yes:
            command.append('--assume-yes')

        print(f"\n{'='*50}")
        print("Running: Applying firmware updates")
        print(f"Command: {' '.join(command)}")
        print(f"{'='*50}")

        try:
            subprocess.run(command, check=True, capture_output=False)
            print("✅ Firmware updates completed successfully")
            pending_actions.append("A reboot may be required for firmware updates to take effect.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Firmware update failed with exit code {e.returncode}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            failures.append(f"Firmware update failed with exit code {e.returncode}")
            return False
    except subprocess.CalledProcessError as e:
        if e.returncode == 2:  # No updates available
            print("ℹ️  No firmware updates available")
            return True
        else:
            print(f"❌ Firmware update failed with exit code {e.returncode}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False
    except Exception as e:
        print(f"⚠️  An error occurred while checking or applying firmware updates: {e}")
        return False

def docker_compose_pull(auto_yes=False):
    """Pull docker-compose images in configured directories and restart if updates found"""
    config = load_config()
    compose_paths = config.get('docker_compose_paths', [])
    
    if not compose_paths:
        print("ℹ️  No docker-compose directories configured, skipping")
        return True
    
    # Filter out invalid paths (container overlay paths, etc.)
    valid_paths = []
    for path_str in compose_paths:
        # Skip container overlay storage paths
        if '/.local/share/containers/storage/overlay/' in path_str:
            continue
        # Skip other temporary/cache paths
        if any(skip in path_str for skip in ['/tmp/', '/.cache/', '/var/tmp/']):
            continue
        valid_paths.append(path_str)
    
    # Update config to remove invalid paths
    if len(valid_paths) != len(compose_paths):
        config['docker_compose_paths'] = valid_paths
        save_config(config)
        print(f"🧹 Cleaned up {len(compose_paths) - len(valid_paths)} invalid docker-compose paths")
    
    if not valid_paths:
        print("ℹ️  No valid docker-compose directories configured, skipping")
        return True
    
    overall_success = True
    
    for path_str in valid_paths:
        compose_path = Path(path_str)
        
        if not compose_path.exists():
            print(f"⚠️  Directory {compose_path} no longer exists, skipping")
            continue
        
        # Find the compose file in this directory
        compose_file = None
        for name in ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']:
            if (compose_path / name).exists():
                compose_file = name
                break
        
        if not compose_file:
            print(f"⚠️  No compose file found in {compose_path}, skipping")
            continue
        
        # Change to compose directory and run docker-compose pull
        original_cwd = os.getcwd()
        try:
            os.chdir(compose_path)
            
            print(f"\n{'='*50}")
            print(f"Running: Pulling docker-compose images in {compose_path}")
            print(f"Command: docker-compose pull")
            print(f"{'='*50}")
            
            spinner = itertools.cycle(['-', '/', '|', '\\'])
            process = subprocess.Popen(['docker-compose', 'pull'], 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE, 
                                       text=True)
            
            while process.poll() is None:
                sys.stdout.write(f"\r{next(spinner)} Pulling images...")
                sys.stdout.flush()
                time.sleep(0.1)
            
            sys.stdout.write("\r") # Clear the spinner
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                print(f"❌ Docker-compose pull failed in {compose_path} with exit code {process.returncode}")
                if stdout:
                    print("STDOUT:", stdout)
                if stderr:
                    print("STDERR:", stderr)
                overall_success = False
            else:
                # Check if any images were actually pulled (updated)
                output = stdout + stderr
                updates_found = any(keyword in output.lower() for keyword in [
                    'pulling', 'downloaded', 'pull complete', 'status: downloaded newer image'
                ])
                
                print(f"✅ Docker-compose pull completed successfully in {compose_path}")
                
                if updates_found:
                    print("🔄 Updates detected, restarting containers...")
                    restart_result = subprocess.run(['docker-compose', 'up', '-d'], 
                                                  check=True, capture_output=False)
                    print("✅ Containers restarted successfully")
                else:
                    print("ℹ️  No updates found, containers not restarted")
                
        except FileNotFoundError:
            print("❌ docker-compose command not found")
            overall_success = False
        except Exception as e:
            print(f"An error occurred: {e}")
            overall_success = False
            
        finally:
            os.chdir(original_cwd)
    
    return overall_success

def docker_system_prune(auto_yes=False):
    """Run docker system prune to clean up unused resources"""
    # Check if docker is installed
    try:
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return True  # Skip silently if not installed
    
    command = ['docker', 'system', 'prune', '-a']
    if auto_yes:
        command.append('-f')  # Force, don't prompt for confirmation
    
    return run_command(command, "Cleaning up Docker system (prune -a)", auto_yes)

def config_get_bool(config, *keys, default=False):
    """Return a boolean from the config for any of the provided keys.
    Keys may be provided with hyphens or underscores (e.g. 'skip-docker-prune' or 'skip_docker_prune').
    Handles string values like 'true'/'yes' as well as booleans.
    """
    for key in keys:
        if key in config:
            val = config[key]
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.strip().lower() in ('1', 'true', 'yes', 'y')
            try:
                return bool(val)
            except Exception:
                continue
    return default


def interactive_configure(config, os_type):
    """Interactive configuration writer. Prompts the user for common flags and saves them to config file."""
    print(f"\n{'='*60}")
    print("🛠  Interactive configuration for system-updater")
    print(f"{'='*60}\n")

    def ask_bool(prompt, current=False):
        default_hint = 'Y/n' if current else 'y/N'
        resp = input(f"{prompt} ({default_hint}): ").strip().lower()
        if not resp:
            return bool(current)
        return resp[0] in ('y', '1', 't')

    # Build new config starting from existing config
    new_config = dict(config)

    def set_config_val(key, value):
        # Preserve string representation if original config used strings
        if key in config and isinstance(config[key], str):
            new_config[key] = 'true' if bool(value) else 'false'
        else:
            new_config[key] = value

    # Common options
    set_config_val('skip-os-updates', ask_bool('Skip OS updates by default?', config_get_bool(config, 'skip-os-updates', 'skip_os_updates', False)))
    set_config_val('skip-vim', ask_bool('Skip vim plugin updates by default?', config_get_bool(config, 'skip-vim', 'skip_vim', False)))
    set_config_val('skip-tmux', ask_bool('Skip tmux plugin updates (TPM) by default?', config_get_bool(config, 'skip-tmux', 'skip_tmux', False)))
    set_config_val('skip-pip', ask_bool('Skip pip package updates by default?', config_get_bool(config, 'skip-pip', 'skip_pip', False)))
    set_config_val('skip-docker-pull', ask_bool('Skip docker-compose pull by default?', config_get_bool(config, 'skip-docker-pull', 'skip_docker_pull', False)))
    set_config_val('skip-docker-prune', ask_bool('Skip docker system prune by default?', config_get_bool(config, 'skip-docker-prune', 'skip_docker_prune', False)))
    set_config_val('skip-tmux', ask_bool('Skip tmux plugin updates (TPM) by default?', config_get_bool(config, 'skip-tmux', 'skip_tmux', False)))
    set_config_val('skip-pip', ask_bool('Skip pip package updates by default?', config_get_bool(config, 'skip-pip', 'skip_pip', False)))
    set_config_val('skip-docker-pull', ask_bool('Skip docker-compose pull by default?', config_get_bool(config, 'skip-docker-pull', 'skip_docker_pull', False)))
    set_config_val('skip-docker-prune', ask_bool('Skip docker system prune by default?', config_get_bool(config, 'skip-docker-prune', 'skip_docker_prune', False)))

    # Platform specific
    if os_type == 'macos':
        set_config_val('skip-homebrew', ask_bool('Skip Homebrew updates by default?', config_get_bool(config, 'skip-homebrew', 'skip_homebrew', False)))
        set_config_val('skip-mas', ask_bool('Skip Mac App Store updates by default?', config_get_bool(config, 'skip-mas', 'skip_mas', False)))
        set_config_val('macupdater', ask_bool('Enable MacUpdater by default?', config_get_bool(config, 'macupdater', 'mac_updater', False)))
        set_config_val('skip-omz', ask_bool('Skip Oh My Zsh updates by default?', config_get_bool(config, 'skip-omz', 'skip_omz', False)))
    else:
        set_config_val('skip-snap', ask_bool('Skip snap refresh by default?', config_get_bool(config, 'skip-snap', 'skip_snap', False)))
        set_config_val('skip-flatpak', ask_bool('Skip Flatpak updates by default?', config_get_bool(config, 'skip-flatpak', 'skip_flatpak', False)))
        set_config_val('skip-firmware', ask_bool('Skip firmware updates by default?', config_get_bool(config, 'skip-firmware', 'skip_firmware', False)))
        set_config_val('apply-firmware', ask_bool('Automatically apply firmware updates when detected?', config_get_bool(config, 'apply-firmware', 'apply_firmware', False)))
        set_config_val('skip-omz', ask_bool('Skip Oh My Zsh updates by default?', config_get_bool(config, 'skip-omz', 'skip_omz', False)))
        set_config_val('service-restart', ask_bool('Automatically restart services detected by dnf needs-restarting?', config_get_bool(config, 'service-restart', 'service_restart', False)))

    # Docker compose setup question
    enable_docker = ask_bool('Enable docker-compose operations by default?', config.get('docker_compose_enabled', False))
    set_config_val('docker_compose_enabled', enable_docker)

    if enable_docker:
        # Offer to discover compose paths
        if ask_bool('Auto-discover docker-compose paths now and save them in config?', False):
            discovered = [str(p) for p in find_docker_compose_files()]
            print(f"Found {len(discovered)} docker-compose directory(ies)")
            # Preserve list type
            new_config['docker_compose_paths'] = discovered

    # Save the new config
    if save_config(new_config):
        cfg_path = get_config_file()
        print(f"\n✅ Configuration saved to: {cfg_path}")
    else:
        print("\n❌ Failed to save configuration")

    print("\nYou can always edit the file manually or run `system-updater --print-config` to see the effective settings.")
    sys.exit(0)

def main():
    # Detect OS before building the CLI parser so we can expose only relevant flags in --help
    os_type = detect_os()

    # Load user config early so config values can be used as defaults for CLI flags
    config = load_config()

    epilog = """
Example config file (~/.config/system-updater/config.json):

  {
    "skip-docker-prune": true,
    "skip-tmux": true
  }

Keys accept hyphen or underscore styles (e.g. `skip-docker-prune` or `skip_docker_prune`).
Command-line flags override config when provided. Run `--help` to see platform-specific flags.
"""

    parser = argparse.ArgumentParser(
        description='Cross-platform system update script for Linux/macOS with Docker maintenance',
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('-i', '--interactive', action='store_true', default=config_get_bool(config, 'interactive', 'interactive_mode', False),
                        help='Interactive mode - prompt for user input (default is auto-yes)')

    # Common flags for all platforms (defaults pulled from config)
    parser.add_argument('--skip-os-updates', action='store_true', default=config_get_bool(config, 'skip-os-updates', 'skip_os_updates', False),
                        help='Skip operating system updates (e.g., macOS softwareupdate, apt/dnf upgrade)')
    parser.add_argument('--skip-vim', action='store_true', default=config_get_bool(config, 'skip-vim', 'skip_vim', False),
                        help='Skip vim plugin updates')
    parser.add_argument('--skip-pip', action='store_true', default=config_get_bool(config, 'skip-pip', 'skip_pip', False),
                        help='Skip pip package updates')
    parser.add_argument('--skip-docker-pull', action='store_true', default=config_get_bool(config, 'skip-docker-pull', 'skip_docker_pull', False),
                        help='Skip docker-compose pull')
    parser.add_argument('--skip-docker-prune', action='store_true', default=config_get_bool(config, 'skip-docker-prune', 'skip_docker_prune', False),
                        help='Skip docker system prune')
    parser.add_argument('--skip-tmux', action='store_true', default=config_get_bool(config, 'skip-tmux', 'skip_tmux', False),
                        help='Skip tmux plugin updates (TPM)')
    parser.add_argument('--print-config', action='store_true', default=False,
                        help='Print the effective configuration (config file merged with CLI flags) and exit')
    parser.add_argument('--configure', action='store_true', default=False,
                        help='Run interactive configuration wizard and exit')

    # Platform-specific flags (defaults pulled from config)
    if os_type == 'macos':
        parser.add_argument('--skip-homebrew', action='store_true', default=config_get_bool(config, 'skip-homebrew', 'skip_homebrew', False),
                            help='Skip Homebrew updates (macOS only)')
        parser.add_argument('--skip-mas', action='store_true', default=config_get_bool(config, 'skip-mas', 'skip_mas', False),
                            help='Skip Mac App Store updates (macOS only)')
        parser.add_argument('--skip-omz', action='store_true', default=config_get_bool(config, 'skip-omz', 'skip_omz', False),
                            help='Skip Oh My Zsh update')
        parser.add_argument('--macupdater', action='store_true', default=config_get_bool(config, 'macupdater', 'mac_updater', False),
                            help='Enable MacUpdater for Mac application updates (macOS only)')
    elif os_type in ['ubuntu', 'fedora', 'rhel']:
        parser.add_argument('--skip-snap', action='store_true', default=config_get_bool(config, 'skip-snap', 'skip_snap', False),
                            help='Skip snap refresh (Linux only)')
        parser.add_argument('--skip-flatpak', action='store_true', default=config_get_bool(config, 'skip-flatpak', 'skip_flatpak', False),
                            help='Skip Flatpak updates (Linux only)')
        parser.add_argument('--skip-firmware', action='store_true', default=config_get_bool(config, 'skip-firmware', 'skip_firmware', False),
                            help='Skip firmware updates (Linux only)')
        parser.add_argument('--apply-firmware', action='store_true', default=config_get_bool(config, 'apply-firmware', 'apply_firmware', False),
                            help='Automatically apply firmware updates when detected (runs a forced refresh and applies updates)')
        parser.add_argument('--skip-omz', action='store_true', default=config_get_bool(config, 'skip-omz', 'skip_omz', False),
                            help='Skip Oh My Zsh update')
        parser.add_argument('--service-restart', action='store_true', default=config_get_bool(config, 'service-restart', 'service_restart', False),
                            help='Automatically restart services detected by dnf needs-restarting without confirmation')

    args = parser.parse_args()

    # Print effective config and exit if --print-config is set
    if args.print_config:
        # Reload config to ensure latest values are used
        config = load_config()

        # Compute effective config: start with defaults, override with config file, then CLI flags
        effective_config = {
            'skip_os_updates': config_get_bool(config, 'skip-os-updates', 'skip_os_updates', False),
            'skip_vim': config_get_bool(config, 'skip-vim', 'skip_vim', False),
            'skip_pip': config_get_bool(config, 'skip-pip', 'skip_pip', False),
            'skip_docker_pull': config_get_bool(config, 'skip-docker-pull', 'skip_docker_pull', False),
            'skip_docker_prune': config_get_bool(config, 'skip-docker-prune', 'skip_docker_prune', False),
            'skip_tmux': config_get_bool(config, 'skip-tmux', 'skip_tmux', False),
            'interactive': config_get_bool(config, 'interactive', 'interactive_mode', False),
            'macupdater': config_get_bool(config, 'macupdater', 'mac_updater', False),
            # Linux-specific options
            'skip_firmware': config_get_bool(config, 'skip-firmware', 'skip_firmware', False),
            'apply_firmware': config_get_bool(config, 'apply-firmware', 'apply_firmware', False),
            'service_restart': config_get_bool(config, 'service-restart', 'service_restart', False),
            'skip_snap': config_get_bool(config, 'skip-snap', 'skip_snap', False),
            'skip_flatpak': config_get_bool(config, 'skip-flatpak', 'skip_flatpak', False),
             # Add any other flags you want to include in the config printout
        }

        # Print the effective config
        print(json.dumps(effective_config, indent=2))
        sys.exit(0)

    # Run interactive configuration wizard and exit if --configure is set
    if args.configure:
        interactive_configure(config, os_type)


    # Default to auto-yes unless interactive flag is set
    auto_yes = not args.interactive

    print("🚀 Starting system update process...")
    print(f"Mode: {'Interactive' if args.interactive else 'Auto-yes'}")
    print(f"Detected OS: {os_type}")

    success_count = 0
    total_tasks = 0

    if os_type == 'macos':
        # Define macOS tasks
        macos_tasks = [
            (update_macos_system_software, not args.skip_os_updates, auto_yes),
            (update_homebrew_packages, not args.skip_homebrew, auto_yes),
            (update_mas_apps, not args.skip_mas, auto_yes),
            (update_ruby_gems, not args.skip_pip, auto_yes),
            (update_npm_packages, not args.skip_pip, auto_yes),
            (update_vim_plugins, not args.skip_vim, auto_yes),
            (update_oh_my_zsh, not args.skip_omz, auto_yes),
            (update_tmux_plugins, not args.skip_tmux, auto_yes),
            (update_mac_apps, args.macupdater, auto_yes),
        ]

        for task, should_run, *task_args in macos_tasks:
            if should_run:
                total_tasks += 1
                if task(*task_args):
                    success_count += 1

    elif os_type in ['ubuntu', 'fedora', 'rhel']:
        # System packages
        if not args.skip_os_updates:
            total_tasks += 1
            if os_type == 'ubuntu':
                run_command(['sudo', 'apt', 'update'], "Updating package lists", auto_yes)
                if run_command(['sudo', 'apt', 'upgrade'], "Upgrading packages", auto_yes):
                    success_count += 1
            elif os_type in ['fedora', 'rhel']:
                if run_command(['sudo', 'dnf', 'upgrade'], f"Updating {os_type.capitalize()} packages", auto_yes):
                    success_count += 1
        # Other Linux tasks
        linux_tasks = [
            (refresh_snaps, not args.skip_snap, auto_yes),
            (update_flatpaks, not args.skip_flatpak, auto_yes),
            (update_pip_packages, not args.skip_pip, auto_yes),
            (update_tmux_plugins, not args.skip_tmux, auto_yes),
            (update_firmware, not args.skip_firmware, auto_yes, args.apply_firmware),
        ]
        for task, should_run, *task_args in linux_tasks:
            if should_run:
                total_tasks += 1
                if task(*task_args):
                    success_count += 1
    else:
        print(f"❌ Unsupported OS: {os_type}")

    # Docker operations (cross-platform)
    docker_available = False
    try:
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
        docker_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    if docker_available:
        if not args.skip_docker_pull:
            compose_paths = setup_docker_compose_config(auto_yes)
            if compose_paths or load_config().get('docker_compose_enabled', False):
                total_tasks += 1
                if docker_compose_pull(auto_yes):
                    success_count += 1
        
        if not args.skip_docker_prune:
            total_tasks += 1
            if docker_system_prune(auto_yes):
                success_count += 1

    # Check for service restarts at the very end
    if os_type in ['fedora', 'rhel']:
        check_fedora_restart_needs(auto_yes, service_restart=args.service_restart)

    # Pending actions summary
    if pending_actions:
        print(f"\n{'='*50}")
        print("🔔 PENDING ACTIONS")
        print(f"{'='*50}")
        for action in pending_actions:
            print(f"  - {action}")

    # Issues / failures summary
    if failures:
        print(f"\n{'='*50}")
        print("🔧 ISSUES / FAILURES")
        print(f"{'='*50}")
        for issue in failures:
            print(f"  - {issue}")

    # Final summary
    print(f"\n{'='*50}")
    print("📊 SUMMARY")
    print(f"{'='*50}")
    print(f"Tasks completed successfully: {success_count}/{total_tasks}")
    
    if success_count == total_tasks and not failures:
        print("🎉 All tasks completed successfully!")
        sys.exit(0)
    else:
        print("⚠️  Some tasks failed or need attention. Check the 'ISSUES / FAILURES' and output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
