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
    print("Running: Checking for macOS system updates")
    print(f"Command: softwareupdate -l")
    print(f"{'='*50}")
    
    try:
        # Check for available updates
        result = subprocess.run(['softwareupdate', '-l'], 
                              check=True, capture_output=True, text=True)
        
        if "No new software available" in result.stdout:
            print("✅ No macOS system updates available")
            return True
        
        print("📋 Available macOS updates:")
        print(result.stdout)
        
        # Install all updates
        command = ['sudo', 'softwareupdate', '-ia']
        if auto_yes:
            # softwareupdate doesn't have a -y flag, but -i means install
            pass
        
        return run_command(command, "Installing macOS system updates")
        
    except subprocess.CalledProcessError as e:
        if "No new software available" in e.stdout:
            print("✅ No macOS system updates available")
            return True
        print(f"❌ Failed to check for macOS updates: {e.returncode}")
        return False

def update_homebrew_packages(auto_yes=False):
    """Update macOS packages using Homebrew"""
    # Check if brew is installed
    try:
        subprocess.run(['brew', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Homebrew not found, skipping brew updates")
        print("   Install Homebrew from: https://brew.sh/")
        return True
    
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
        print("⚠️  mas (Mac App Store CLI) not found, skipping App Store updates")
        print("   Install with: brew install mas")
        return True
    
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
    """Update Ruby gems"""
    # Check if gem is installed
    try:
        subprocess.run(['gem', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Ruby gems not found, skipping gem updates")
        return True
    
    print(f"\n{'='*50}")
    print("Running: Checking for outdated Ruby gems")
    print(f"Command: gem outdated")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(['gem', 'outdated'], 
                              check=True, capture_output=True, text=True)
        
        if not result.stdout.strip():
            print("✅ No outdated Ruby gems found")
            return True
        
        print("📋 Outdated Ruby gems:")
        print(result.stdout)
        
        # Update all gems
        return run_command(['gem', 'update'], "Updating Ruby gems")
        
    except subprocess.CalledProcessError:
        print("⚠️  Could not check Ruby gem updates")
        return True

def update_npm_packages(auto_yes=False):
    """Update global npm packages"""
    # Check if npm is installed
    try:
        subprocess.run(['npm', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  npm not found, skipping npm updates")
        return True
    
    print(f"\n{'='*50}")
    print("Running: Checking for outdated npm packages")
    print(f"Command: npm outdated -g")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(['npm', 'outdated', '-g'], 
                              check=True, capture_output=True, text=True)
        
        if not result.stdout.strip():
            print("✅ No outdated global npm packages found")
            return True
        
        print("📋 Outdated global npm packages:")
        print(result.stdout)
        
        # Update all global packages
        return run_command(['npm', 'update', '-g'], "Updating global npm packages")
        
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:  # npm outdated returns 1 when there are outdated packages
            if e.stdout.strip():
                print("📋 Outdated global npm packages:")
                print(e.stdout)
                return run_command(['npm', 'update', '-g'], "Updating global npm packages")
            else:
                print("✅ No outdated global npm packages found")
                return True
        else:
            print("⚠️  Could not check npm package updates")
            return True

def check_fedora_restart_needs(auto_yes=False):
    """Check for services and system restart needs on Fedora/RHEL systems"""
    # Check if dnf-utils (which provides needs-restarting) is available
    try:
        subprocess.run(['needs-restarting', '--help'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  needs-restarting command not found, install dnf-utils for restart detection")
        print("   Install with: sudo dnf install dnf-utils")
        return True
    
    print(f"\n{'='*50}")
    print("Running: Checking for restart requirements")
    print(f"Command: needs-restarting")
    print(f"{'='*50}")
    
    # Check for services that need restarting
    try:
        services_result = subprocess.run(['needs-restarting', '-s'], 
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
        reboot_result = subprocess.run(['needs-restarting', '-r'], 
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
        print("ℹ️  Snap not available on macOS, skipping")
        return True
    
    # Check if snap is installed
    try:
        subprocess.run(['snap', '--version'], check=True, capture_output=True)
        return run_command(['sudo', 'snap', 'refresh'], "Refreshing snap packages")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Snap not found or not installed, skipping snap refresh")
        return True

def update_flatpaks():
    """Update Flatpak packages (Linux only)"""
    os_type = detect_os()
    if os_type == 'macos':
        print("ℹ️  Flatpak not available on macOS, skipping")
        return True
    
    # Check if flatpak is installed
    try:
        subprocess.run(['flatpak', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Flatpak not found or not installed, skipping flatpak updates")
        print("   Install with: sudo apt install flatpak (Ubuntu) or sudo dnf install flatpak (Fedora)")
        return True
    
    success = True
    
    # Update flatpak repositories
    if not run_command(['flatpak', 'update', '--appstream'], "Updating Flatpak repositories"):
        success = False
    
    # Update flatpak applications
    if not run_command(['flatpak', 'update', '-y'], "Updating Flatpak applications"):
        success = False
    
    return success

def update_pip_packages():
    """Update pip packages (primarily for macOS)"""
    os_type = detect_os()
    
    # Check if pip3 is installed
    try:
        subprocess.run(['pip3', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  pip3 not found, skipping pip package updates")
        return True
    
    print(f"\n{'='*50}")
    print("Running: Updating pip packages")
    print(f"Command: pip3 list --outdated --format=columns | awk 'NR>2{{print $1}}' | xargs -n1 pip3 install -U")
    print(f"{'='*50}")
    
    try:
        # Get outdated packages and upgrade them
        result = subprocess.run(['pip3', 'list', '--outdated', '--format=columns'], 
                              check=True, capture_output=True, text=True)
        
        if not result.stdout.strip() or len(result.stdout.strip().split('\n')) <= 2:
            print("ℹ️  No outdated pip packages found")
            return True
        
        # Extract package names (skip header lines)
        lines = result.stdout.strip().split('\n')[2:]  # Skip first 2 header lines
        packages = [line.split()[0] for line in lines if line.strip()]
        
        if not packages:
            print("ℹ️  No outdated pip packages found")
            return True
        
        print(f"📋 Found {len(packages)} outdated packages: {', '.join(packages)}")
        
        # Upgrade each package
        for package in packages:
            subprocess.run(['pip3', 'install', '-U', package], check=True, capture_output=False)
        
        print("✅ Pip packages updated successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Pip package update failed with exit code {e.returncode}")
        return False

def update_mac_apps():
    """Update Mac applications using MacUpdater"""
    os_type = detect_os()
    if os_type != 'macos':
        print("ℹ️  MacUpdater only available on macOS, skipping")
        return True
    
    macupdater_path = '/Applications/MacUpdater.app/Contents/Resources/macupdater_client'
    
    if not os.path.exists(macupdater_path):
        print("⚠️  MacUpdater not found, skipping Mac app updates")
        print("   Install MacUpdater from: https://www.corecode.io/macupdater/")
        return True
    
    # Scan for updates
    if not run_command([macupdater_path, 'scan'], "Scanning for Mac app updates"):
        return False
    
    # Apply updates
    return run_command([macupdater_path, 'update'], "Updating Mac applications")

def update_firmware(auto_yes=False):
    """Update firmware using fwupdmgr (Linux only)"""
    os_type = detect_os()
    if os_type == 'macos':
        print("ℹ️  Firmware updates handled by macOS System Preferences, skipping")
        return True
    
    # Check if fwupdmgr is installed
    try:
        subprocess.run(['fwupdmgr', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
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
        command = ['fwupdmgr', 'update']
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

def docker_compose_pull():
    """Pull docker-compose images in ~/ganymede directory and restart if updates found"""
    ganymede_path = Path.home() / 'ganymede'
    
    if not ganymede_path.exists():
        print(f"❌ Directory {ganymede_path} does not exist")
        return False
    
    if not (ganymede_path / 'docker-compose.yml').exists() and not (ganymede_path / 'docker-compose.yaml').exists():
        print(f"❌ No docker-compose.yml/yaml found in {ganymede_path}")
        return False
    
    # Change to ganymede directory and run docker-compose pull
    original_cwd = os.getcwd()
    try:
        os.chdir(ganymede_path)
        
        # Run docker-compose pull and capture output to detect updates
        print(f"\n{'='*50}")
        print("Running: Pulling docker-compose images")
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
            print("✅ Docker-compose pull completed successfully")
            
            if updates_found:
                print("🔄 Updates detected, restarting containers...")
                restart_result = subprocess.run(['docker-compose', 'up', '-d'], 
                                              check=True, capture_output=False)
                print("✅ Containers restarted successfully")
            else:
                print("ℹ️  No updates found, containers not restarted")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Docker-compose pull failed with exit code {e.returncode}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False
        except FileNotFoundError:
            print("❌ docker-compose command not found")
            return False
            
    finally:
        os.chdir(original_cwd)

def docker_system_prune(auto_yes=False):
    """Run docker system prune to clean up unused resources"""
    command = ['docker', 'system', 'prune', '-a']
    if auto_yes:
        command.append('-f')  # Force, don't prompt for confirmation
    
    return run_command(command, "Cleaning up Docker system (prune -a)", auto_yes)

def main():
    parser = argparse.ArgumentParser(description='Cross-platform system update script for Linux/macOS with Docker maintenance')
    parser.add_argument('-y', '--yes', action='store_true', 
                       help='Automatically answer yes to prompts')
    parser.add_argument('--skip-system', action='store_true',
                       help='Skip system package updates')
    parser.add_argument('--skip-snap', action='store_true',
                       help='Skip snap refresh (Linux only)')
    parser.add_argument('--skip-flatpak', action='store_true',
                       help='Skip Flatpak updates (Linux only)')
    parser.add_argument('--skip-pip', action='store_true',
                       help='Skip pip package updates')
    parser.add_argument('--skip-mac-apps', action='store_true',
                       help='Skip Mac application updates (macOS only)')
    parser.add_argument('--skip-firmware', action='store_true',
                       help='Skip firmware updates (Linux only)')
    parser.add_argument('--skip-docker-pull', action='store_true',
                       help='Skip docker-compose pull')
    parser.add_argument('--skip-docker-prune', action='store_true',
                       help='Skip docker system prune')
    
    args = parser.parse_args()
    
    print("🚀 Starting system update process...")
    print(f"Auto-yes mode: {'ON' if args.yes else 'OFF'}")
    
    success_count = 0
    total_tasks = 0
    
    # Update system packages
    if not args.skip_system:
        total_tasks += 1
        if update_system_packages(args.yes):
            success_count += 1
    
    # Refresh snaps
    if not args.skip_snap:
        total_tasks += 1
        if refresh_snaps():
            success_count += 1
    
    # Update Flatpaks
    if not args.skip_flatpak:
        total_tasks += 1
        if update_flatpaks():
            success_count += 1
    
    # Update pip packages
    if not args.skip_pip:
        total_tasks += 1
        if update_pip_packages():
            success_count += 1
    
    # Update Mac applications
    if not args.skip_mac_apps:
        total_tasks += 1
        if update_mac_apps():
            success_count += 1
    
    # Update firmware
    if not args.skip_firmware:
        total_tasks += 1
        if update_firmware(args.yes):
            success_count += 1
    
    # Docker-compose pull
    if not args.skip_docker_pull:
        total_tasks += 1
        if docker_compose_pull():
            success_count += 1
    
    # Docker system prune
    if not args.skip_docker_prune:
        total_tasks += 1
        if docker_system_prune(args.yes):
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
