# Docker Development Guide

## Overview

This guide explains how Docker containers handle code changes and how to ensure your changes are reflected in running containers.

## Container Update Behavior

### Development Mode (Hot Reload)

When using `docker-compose.dev.yml`, containers are configured for **automatic hot-reload**:

- **API**: Code changes in `src/` are automatically detected and the server reloads
- **Frontend**: Code changes in `frontend/src/` trigger automatic rebuilds via Vite
- **Scheduler**: Requires manual restart to pick up changes (see below)

### Production Mode

In production mode (`docker-compose.yml`), containers do **NOT** automatically update:
- Code is copied into the image at build time
- Changes require rebuilding and restarting containers

## Quick Start

### Development Mode (Recommended for Active Development)

```bash
# Start with hot-reload enabled
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Or use the helper script
./scripts/docker-dev.sh
```

**Benefits:**
- ✅ API auto-reloads on code changes
- ✅ Frontend auto-rebuilds on code changes
- ✅ No need to rebuild containers for most changes

**Limitations:**
- Scheduler requires restart for code changes
- New Python dependencies require rebuild

### Production Mode

```bash
# Start production containers
docker-compose up --build
```

**Note:** Code changes require rebuilding containers.

## Ensuring Containers Are Updated

### Method 1: Use Development Mode (Recommended)

For active development, always use development mode:

```bash
# Windows PowerShell
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Linux/Mac
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Method 2: Rebuild After Changes

If you're in production mode or made significant changes:

**Windows PowerShell:**
```powershell
# Rebuild all services
.\scripts\docker-rebuild.ps1 -Service all

# Rebuild specific service
.\scripts\docker-rebuild.ps1 -Service api
.\scripts\docker-rebuild.ps1 -Service frontend
.\scripts\docker-rebuild.ps1 -Service scheduler
.\scripts\docker-rebuild.ps1 -Service api-scheduler
```

**Linux/Mac:**
```bash
# Rebuild all services
./scripts/docker-rebuild.sh

# Or manually
docker-compose build --no-cache api
docker-compose up -d api
```

### Method 3: Restart Services (Development Mode Only)

In development mode, you can restart services without rebuild:

```bash
# Restart API (picks up code changes via volume mount)
docker-compose restart api

# Restart Scheduler (picks up code changes via volume mount)
docker-compose restart scheduler

# Restart Frontend (picks up code changes via volume mount)
docker-compose restart frontend
```

## What Gets Updated Automatically

### ✅ Automatic Updates (Development Mode)

- **API Python code** (`src/investment_platform/**/*.py`)
  - Uvicorn auto-reload detects file changes
  - Server restarts automatically

- **Frontend React/TypeScript** (`frontend/src/**/*.{ts,tsx,js,jsx}`)
  - Vite dev server watches for changes
  - Browser auto-refreshes

- **Frontend assets** (`frontend/public/**`)
  - Changes reflected immediately

### ⚠️ Requires Restart (Development Mode)

- **Scheduler code** (`src/investment_platform/ingestion/**`)
  - Volume mount provides code, but scheduler needs restart
  - Run: `docker-compose restart scheduler`

### 🔄 Requires Rebuild

- **New Python dependencies** (`requirements*.txt`)
  - Run: `docker-compose build api scheduler`
  - Then: `docker-compose up -d api scheduler`

- **New Node dependencies** (`frontend/package.json`)
  - Run: `docker-compose build frontend`
  - Then: `docker-compose up -d frontend`

- **Dockerfile changes**
  - Always requires rebuild

- **Environment variable changes** (in docker-compose.yml)
  - Requires restart: `docker-compose restart <service>`

## Workflow Recommendations

### During Active Development

1. **Always use development mode:**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
   ```

2. **After making code changes:**
   - API/Frontend: Changes are automatic (just wait a few seconds)
   - Scheduler: Run `docker-compose restart scheduler`

3. **After adding dependencies:**
   - Python: Rebuild API/Scheduler containers
   - Node: Rebuild Frontend container

### Before Committing

1. Test in production mode to ensure everything works:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up
   ```

## Troubleshooting

### Changes Not Reflecting

1. **Check if you're in development mode:**
   ```bash
   docker-compose ps
   # Look for volume mounts in docker inspect
   ```

2. **Verify volume mounts:**
   ```bash
   docker inspect investment_platform_api | grep -A 10 Mounts
   ```

3. **Check file permissions:**
   - Ensure files are readable by the container user

4. **Restart the service:**
   ```bash
   docker-compose restart <service>
   ```

### Scheduler Not Picking Up Changes

The scheduler doesn't auto-reload. After code changes:

```bash
# In development mode
docker-compose restart scheduler

# In production mode
docker-compose build scheduler
docker-compose up -d scheduler
```

### Frontend Not Updating

1. Check if Vite dev server is running:
   ```bash
   docker-compose logs frontend
   ```

2. Clear browser cache or hard refresh (Ctrl+Shift+R)

3. Rebuild if needed:
   ```bash
   docker-compose build frontend
   docker-compose up -d frontend
   ```

## Best Practices

1. **Use development mode for active development**
   - Enables hot-reload
   - Faster iteration cycle

2. **Rebuild before important tests**
   - Ensures all changes are included
   - Catches build-time issues

3. **Check container logs after changes:**
   ```bash
   docker-compose logs -f api
   docker-compose logs -f scheduler
   ```

4. **Use the helper scripts:**
   - `scripts/docker-rebuild.sh` (Linux/Mac)
   - `scripts/docker-rebuild.ps1` (Windows)

## Summary

| Mode | API Updates | Frontend Updates | Scheduler Updates |
|------|------------|------------------|-------------------|
| **Development** | ✅ Auto-reload | ✅ Auto-reload | ⚠️ Restart needed |
| **Production** | 🔄 Rebuild needed | 🔄 Rebuild needed | 🔄 Rebuild needed |

**Recommendation:** Use development mode (`docker-compose.dev.yml`) for active development to get automatic updates for API and Frontend.

