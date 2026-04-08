# Root Cause Analysis: Docker-Compose Dependent Container Error

## The Problem
When updating docker-compose containers with services that depend on each other via `network_mode: service:gluetun`, the script should stop dependent containers before restarting the primary service. However, the error shows:

```
container 1853b5fcdcd4c0ef843370508e054ab365d7d09b8d52186c301e6d0684291bcb 
has dependent containers which must be removed before it: 
1a6a556027a5aa8ef7b5b91da8b9c74c9bbf9dc899aadb39e2ea36de136cb873: 
container already exists
```

This means the dependent containers (e.g., qbittorrent) were NOT stopped before `docker-compose up -d` tried to restart them.

## Root Causes Identified & Fixed

### 1. **Image Name Format Mismatch** (Most Likely Issue)
**Problem**: The script was only storing image names as-is from `docker images` output, but when comparing with the compose file, the formats didn't match.

**Example**:
- Compose file has: `ghcr.io/qdm12/gluetun:latest`  
- Docker images returns: `ghcr.io/qdm12/gluetun` (without tag after pull)
- Or docker might return a fully qualified name while compose uses a shorter form

**Fix Applied**:
- Store images by BOTH full name AND repository-only (without tag)
- Enhanced image matching to try exact match, then repository match, then partial match
- Better fallback logic for matching variations in image naming

**Code Change**:
```python
# Also store by repository-only (without tag) for better matching
repo_only = name.split(':')[0] if ':' in name else name
if repo_only not in pre_pull_digests:
    pre_pull_digests[repo_only] = digest
```

### 2. **Network Mode Dependency Detection**
**Problem**: The `network_mode: service:provider` parsing might fail silently if there are extra spaces or format variations.

**Fix Applied**:
- Added `.strip()` to handle whitespace after split
- Better error messages when provider can't be resolved
- Added check to exclude 'host' mode (not a dependency like 'service:')

**Code Change**:
```python
provider_ref = network_mode.split('service:')[1].strip()  # Added .strip()
elif network_mode and network_mode != 'bridge' and network_mode != 'host':
    # Better detection of problematic cases
```

### 3. **Enhanced Dependency Tracking**
**Problem**: Containers being identified weren't being matched correctly to the actual docker container names.

**Fix Applied**:
- Log which dependents are being added to the graph
- Better container ID resolution before stopping
- Verify container stops succeeded before proceeding

**Code Change**:
```python
network_dependents_graph[network_provider_svc_name].add(svc_name)
print(f"🔍 DEBUG: Added '{svc_name}' to dependents of '{network_provider_svc_name}'")
```

## Why No Updates Might Have Been Detected

If the script ran but didn't stop containers, it's likely because:

1. **Image name mismatch prevented update detection**
   - The updated gluetun image wasn't matched to the 'gluetun' service
   - Therefore no services were identified as needing dependent container stops

2. **Image stored with tag vs without tag**
   - Pre-pull: `ghcr.io/qdm12/gluetun:latest` (SHA: abc123)
   - Post-pull: `ghcr.io/qdm12/gluetun` (SHA: xyz789)
   - These don't match, so update wasn't detected

3. **Image registry normalization**
   - Docker might normalize registry names differently
   - Script now handles multiple formats

## New Debug Output Added

The script now provides detailed logging:

1. **Image matching attempts**:
   ```
   🔍 DEBUG: Image 'ghcr.io/qdm12/gluetun:latest' matched to service 'gluetun'
   ```

2. **Dependency detection**:
   ```
   🔍 DEBUG: Service 'qbittorrent' depends on service 'gluetun' via network_mode
   🔍 DEBUG: Service 'gluetun' has network consumers: {'qbittorrent'}
   ```

3. **Update detection**:
   ```
   🔍 DEBUG: Image updated (exact match): ghcr.io/qdm12/gluetun:latest
   🔍 DEBUG: Updated services: {'gluetun'}
   ```

4. **Container stopping**:
   ```
   Container ID: 1a6a556027a5aa8ef7b5b91da8b9c74c9bbf9dc899aadb39e2ea36de136cb873
   ```

## Testing the Fix

When the next docker-compose updates happen, look for:

1. ✅ `Updated images detected` showing gluetun was recognized as updated
2. ✅ `Service 'qbittorrent' depends on service 'gluetun'` - dependency detected
3. ✅ `Services to stop: {'qbittorrent'}` - dependent container identified
4. ✅ `Stopping qbittorrent...` - container actually being stopped
5. ✅ `Container ID: xxx` - verify the container was stopped
6. ✅ `Containers updated and restarted successfully` - docker-compose up succeeded

If you see "Could not match updated image" or "Services to stop: set()" for updated images, that indicates the issue wasn't fully resolved and the image matching logic needs further investigation.

## Summary

The fixes address the most likely cause: **image name format mismatches preventing the script from identifying which images were updated and therefore which containers needed to be stopped**. The enhanced matching logic and improved debug output will make it clear if this is still an issue when testing.

