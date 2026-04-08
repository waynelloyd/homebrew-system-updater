# Docker-Compose Dependency Debug Guide

## Overview
The script has been enhanced with detailed debugging output to help diagnose why dependent containers (like gluetun) are not being stopped before docker-compose up -d attempts to restart services.

## Debug Output Sections

### 1. Service and Image Discovery
```
🔍 DEBUG: Found N services in compose file
🔍 DEBUG: Image to service mapping: {...}
```
- Shows all services found in your docker-compose file
- Maps image names to service names for tracking which image belongs to which service

### 2. Network Dependency Detection
```
🔍 DEBUG: Service 'qbittorrent' depends on service 'gluetun' via network_mode
🔍 DEBUG: Service 'X' has network_mode='Y' but could not resolve provider
```
- **Expected for gluetun**: You should see lines like "service 'qbittorrent' depends on service 'gluetun'"
- This indicates that qbittorrent (or other services) use `network_mode: service:gluetun`
- If you see "could not resolve provider", there's a mismatch between the compose file and what the script found

### 3. Update Detection
```
🔍 DEBUG: Updated images detected: ['ghcr.io/qdm12/gluetun:latest']
🔍 DEBUG: Image 'ghcr.io/qdm12/gluetun:latest' matched to service 'gluetun'
```
- Shows which images were pulled with new versions
- Shows if the image was correctly matched to a service name

### 4. Dependency Resolution
```
🔍 DEBUG: Updated services: {'gluetun'}
🔍 DEBUG: Network dependency graph: {'gluetun': {'qbittorrent'}, 'qbittorrent': set(), ...}
🔍 DEBUG: Service 'gluetun' has network consumers: {'qbittorrent'}
🔍 DEBUG: Services to stop: {'qbittorrent'}
🔍 DEBUG: Containers to stop (by name): {'qbittorrent'}
```
- **Updated services**: Services whose images changed
- **Network dependency graph**: Shows the full dependency structure
- **Network consumers**: Services that depend on the updated service (should be stopped)
- **Services/Containers to stop**: Final list that will be stopped

### 5. Container Stopping
```
🔄 Network-dependent sidecar(s) detected. Stopping 1 container(s): qbittorrent
  ⏹️  Stopping qbittorrent...
       Container ID: 1a6a556027a5aa8ef7b5b91da8b9c74c9bbf9dc899aadb39e2ea36de136cb873
       (successful or error message)
```
- Shows which containers are being stopped
- Shows the actual container ID being stopped
- Shows if the stop command succeeded or failed

## What Each Error Means

### Problem: "could not resolve provider"
```
🔍 DEBUG: Service 'qbittorrent' has network_mode='service:gluetun' but could not resolve provider
```
**Cause**: The service reference in `network_mode` doesn't match any service name in the compose file.
**Solution**: Check your compose file - ensure the referenced service name exactly matches.

### Problem: No network consumers detected
```
🔍 DEBUG: Network dependency graph: {...all empty...}
🔍 DEBUG: Services to stop: set()
ℹ️  No network-dependent sidecars detected for updated images
```
**Cause**: The script didn't identify any services depending on gluetun.
**Possible reasons**:
1. Services use `network_mode: container:gluetun` instead of `network_mode: service:gluetun`
2. Custom container_name mismatches
3. Services defined at compose file level vs being read correctly

### Problem: Image not matched to service
```
🔍 DEBUG: Updated images detected: ['ghcr.io/qdm12/gluetun:latest']
(no "Image matched to service" line for gluetun)
```
**Cause**: The pulled image name doesn't match what's in the compose file.
**Solution**: Check docker-compose.yml for the exact image specification.

## How to Use This Information

When the error occurs:
1. Run the script and capture the debug output
2. Check the "Services to stop" line
3. Verify it includes all services that depend on updated images
4. If gluetun is updated but qbittorrent isn't in the "Services to stop" list, there's a dependency detection issue
5. Look at the "Network dependency graph" to understand the relationship

## Example Output (Success Case)
```
🔍 DEBUG: Found 5 services in compose file
🔍 DEBUG: Image to service mapping: {'ghcr.io/qdm12/gluetun:latest': 'gluetun', 'linuxserver/qbittorrent:latest': 'qbittorrent', ...}
🔍 DEBUG: Service 'qbittorrent' depends on service 'gluetun' via network_mode
✅ Docker-compose pull completed successfully in /home/waynelloyd/ganymede
🔍 DEBUG: Updated images detected: ['ghcr.io/qdm12/gluetun:latest']
🔍 DEBUG: Image 'ghcr.io/qdm12/gluetun:latest' matched to service 'gluetun'
🔍 DEBUG: Updated services: {'gluetun'}
🔍 DEBUG: Network dependency graph: {'gluetun': {'qbittorrent'}, 'qbittorrent': set(), ...}
🔍 DEBUG: Service 'gluetun' has network consumers: {'qbittorrent'}
🔍 DEBUG: Services to stop: {'qbittorrent'}
🔍 DEBUG: Containers to stop (by name): {'qbittorrent'}
🔄 Network-dependent sidecar(s) detected. Stopping 1 container(s): qbittorrent
  ⏹️  Stopping qbittorrent...
       Container ID: 1a6a556027a5aa8ef7b5b91da8b9c74c9bbf9dc899aadb39e2ea36de136cb873
```

This would indicate everything is working correctly!

