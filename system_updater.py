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

def run_command(command, description, auto_yes=False):
    """Run a command and handle output"""
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
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {command[0]}")
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
    
    choice = input("Choice (a/s/n): ").lower().strip()
    
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

def update_system_packages(auto_yes=False):
    """Update system packages based on operating system"""
    os_type = detect_os()
    print(f"Detected OS: {os_type}")
    
    if os_type == 'macos':
        return update_macos_packages(auto_yes)
    elif os_type == 'ubuntu':
        # Update package lists
        run_command(['sudo', 'apt', 'update'], "Updating package lists", auto_yes)
        # Upgrade packages
        run_command(['sudo', 'apt', 'upgrade'], "Upgrading packages", auto_yes)
    elif os_type == 'fedora':
        # Update packages
        run_command(['sudo', 'dnf', 'upgrade'], "Updating Fedora packages", auto_yes)
        # Check for services that need restarting
        check_fedora_restart_needs(auto_yes)
    elif os_type == 'rhel':
        # Update packages
        run_command(['sudo', 'yum', 'update'], "Updating RHEL/CentOS packages", auto_yes)
        # Check for services that need restarting
        check_fedora_restart_needs(auto_yes)
    else:
        print(f"❌ Unsupported OS: {os_type}")
        return False
    
    return True

def update_macos_packages(auto_yes=False):
    """Update macOS packages using multiple package managers"""
    success = True
    
    # Update macOS system software first
    if not update_macos_system_software(auto_yes):
        success = False
    
    # Update Homebrew packages
    if not update_homebrew_packages(auto_yes):
        success = False
    
    # Update Mac App Store apps
    if not update_mas_apps(auto_yes):
        success = False
    
    # Update Ruby gems
    if not update_ruby_gems(auto_yes):
        success = False
    
    # Update npm packages
    if not update_npm_packages(auto_yes):
        success = False
    
    return success

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

def check_fedora_restart_needs(auto_yes=False):
    """Check for services and system restart needs on Fedora/RHEL systems"""
    # Check if dnf is available (should be on all modern Fedora/RHEL systems)
    try:
        subprocess.run(['dnf', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return True  # Skip silently if dnf not available
    
    print(f"\n{'='*50}")
    print("Running: Checking for restart requirements")
    print(f"Command: dnf needs-restarting")
    print(f"{'='*50}")
    
    # Check for services that need restarting
    try:
        services_result = subprocess.run(['dnf', 'needs-restarting', '-s'], 
                                       check=True, capture_output=True, text=True)
        
        if services_result.stdout.strip():
            services = services_result.stdout.strip().split('\n')
            print(f"🔄 Found {len(services)} services that need restarting:")
            for service in services:
                print(f"   - {service}")
            
            if auto_yes or input("\n🤔 Restart these services automatically? (y/N): ").lower().startswith('y'):
                print("🔄 Restarting services...")
                for service in services:
                    service_name = service.strip()
                    if service_name:
                        run_command(['sudo', 'systemctl', 'restart', service_name], 
                                  f"Restarting {service_name}")
            else:
                print("ℹ️  Services not restarted. You can restart them manually later.")
        else:
            print("✅ No services need restarting")
            
    except subprocess.CalledProcessError:
        print("⚠️  Could not check service restart requirements")
    
    # Check if system reboot is needed
    try:
        reboot_result = subprocess.run(['dnf', 'needs-restarting', '-r'], 
                                     check=True, capture_output=True, text=True)
        print("✅ System reboot not required")
        
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:  # Exit code 1 means reboot is needed
            print("🚨 SYSTEM REBOOT REQUIRED")
            print("   Some updates require a system restart to take effect")
            
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
    
    return True

def refresh_snaps():
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

def update_flatpaks():
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

def update_pip_packages():
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

def update_mac_apps():
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

def update_firmware(auto_yes=False):
    """Update firmware using fwupdmgr (Linux only)"""
    os_type = detect_os()
    if os_type == 'macos':
        return True  # Skip silently on macOS
    
    # Check if fwupdmgr is installed
    try:
        subprocess.run(['fwupdmgr', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  fwupdmgr not found or not installed, skipping firmware updates")
        print("⚠️  fwupdmgr not found or not installed, skipping firmware updates")
        print("   Install with: sudo apt install fwupd (Ubuntu) or sudo dnf install fwupd (Fedora)")
        return True
    
    # Refresh firmware metadata
    print(f"\n{'='*50}")
    print("Running: Refreshing firmware metadata")
    print(f"Command: fwupdmgr refresh")
    print(f"{'='*50}")
    
    try:
        subprocess.run(['fwupdmgr', 'refresh'], check=True, capture_output=False)
        print("✅ Firmware metadata refreshed successfully")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Firmware metadata refresh failed with exit code {e.returncode}")
        # Continue anyway as this might not be critical
    
    # Check for available firmware updates
    print(f"\n{'='*50}")
    print("Running: Checking for firmware updates")
    print(f"Command: fwupdmgr get-updates")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(['fwupdmgr', 'get-updates'], 
                              check=True, capture_output=True, text=True)
        
        if "No updates available" in result.stdout or not result.stdout.strip():
            print("ℹ️  No firmware updates available")
            return True
        
        print("📋 Available firmware updates:")
        print(result.stdout)
        
        # Apply firmware updates
        command = ['sudo', 'fwupdmgr', 'update']
        if auto_yes:
            command.append('--assume-yes')
        
        print(f"\n{'='*50}")
        print("Running: Applying firmware updates")
        print(f"Command: {' '.join(command)}")
        print(f"{'='*50}")
        
        subprocess.run(command, check=True, capture_output=False)
        print("✅ Firmware updates completed successfully")
        print("⚠️  A reboot may be required for firmware updates to take effect")
        
        return True
        
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
            
            try:
                result = subprocess.run(['docker-compose', 'pull'], 
                                      check=True, capture_output=True, text=True)
                
                # Check if any images were actually pulled (updated)
                output = result.stdout + result.stderr
                updates_found = any(keyword in output.lower() for keyword in [
                    'pulling', 'downloaded', 'pull complete', 'status: downloaded newer image'
                ])
                
                print(output)
                print(f"✅ Docker-compose pull completed successfully in {compose_path}")
                
                if updates_found:
                    print("🔄 Updates detected, restarting containers...")
                    restart_result = subprocess.run(['docker-compose', 'up', '-d'], 
                                                  check=True, capture_output=False)
                    print("✅ Containers restarted successfully")
                else:
                    print("ℹ️  No updates found, containers not restarted")
                
            except subprocess.CalledProcessError as e:
                print(f"❌ Docker-compose pull failed in {compose_path} with exit code {e.returncode}")
                if e.stdout:
                    print("STDOUT:", e.stdout)
                if e.stderr:
                    print("STDERR:", e.stderr)
                overall_success = False
            except FileNotFoundError:
                print("❌ docker-compose command not found")
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

def main():
    parser = argparse.ArgumentParser(description='Cross-platform system update script for Linux/macOS with Docker maintenance')
    parser.add_argument('-i', '--interactive', action='store_true', 
                       help='Interactive mode - prompt for user input (default is auto-yes)')
    parser.add_argument('--skip-system', action='store_true',
                       help='Skip system package updates')
    parser.add_argument('--skip-snap', action='store_true',
                       help='Skip snap refresh (Linux only)')
    parser.add_argument('--skip-flatpak', action='store_true',
                       help='Skip Flatpak updates (Linux only)')
    parser.add_argument('--skip-pip', action='store_true',
                       help='Skip pip package updates')
    parser.add_argument('--macupdater', action='store_true',
                       help='Enable MacUpdater for Mac application updates (macOS only)')
    parser.add_argument('--skip-firmware', action='store_true',
                       help='Skip firmware updates (Linux only)')
    parser.add_argument('--skip-docker-pull', action='store_true',
                       help='Skip docker-compose pull')
    parser.add_argument('--skip-docker-prune', action='store_true',
                       help='Skip docker system prune')
    
    args = parser.parse_args()
    
    # Default to auto-yes unless interactive flag is set
    auto_yes = not args.interactive
    
    print("🚀 Starting system update process...")
    print(f"Mode: {'Interactive' if args.interactive else 'Auto-yes'}")
    
    success_count = 0
    total_tasks = 0
    
    # Update system packages
    if not args.skip_system:
        total_tasks += 1
        if update_system_packages(auto_yes):
            success_count += 1
    
    # Refresh snaps (Linux only)
    if not args.skip_snap and detect_os() != 'macos':
        total_tasks += 1
        if refresh_snaps():
            success_count += 1
    
    # Update Flatpaks (Linux only)
    if not args.skip_flatpak and detect_os() != 'macos':
        total_tasks += 1
        if update_flatpaks():
            success_count += 1
    
    # Update pip packages
    if not args.skip_pip:
        total_tasks += 1
        if update_pip_packages():
            success_count += 1
    
    # Update Mac applications (only if --macupdater flag is set)
    if args.macupdater:
        total_tasks += 1
        if update_mac_apps():
            success_count += 1
    
    # Update firmware (Linux only)
    if not args.skip_firmware and detect_os() != 'macos':
        total_tasks += 1
        if update_firmware(auto_yes):
            success_count += 1
    
    # Check if Docker is installed before any Docker operations
    docker_available = False
    try:
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
        docker_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Setup docker-compose configuration on first run (only if Docker available)
    if not args.skip_docker_pull and docker_available:
        compose_paths = setup_docker_compose_config(auto_yes)
        if compose_paths or load_config().get('docker_compose_enabled', False):
            total_tasks += 1
            if docker_compose_pull(auto_yes):
                success_count += 1
    
    # Docker system prune (only if Docker available)
    if not args.skip_docker_prune and docker_available:
        total_tasks += 1
        if docker_system_prune(auto_yes):
            success_count += 1
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 SUMMARY")
    print(f"{'='*50}")
    print(f"Tasks completed successfully: {success_count}/{total_tasks}")
    
    if success_count == total_tasks:
        print("🎉 All tasks completed successfully!")
        sys.exit(0)
    else:
        print("⚠️  Some tasks failed. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
