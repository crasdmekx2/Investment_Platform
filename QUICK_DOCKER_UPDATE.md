# Quick Docker Update Guide

## TL;DR - How to Update Containers After Code Changes

### Option 1: Use Development Mode (Best for Active Development)

```powershell
# Start with hot-reload (Windows)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# API and Frontend will auto-update on code changes!
# Scheduler needs restart: docker-compose restart scheduler
```

### Option 2: Rebuild After Changes

```powershell
# Rebuild everything (Windows PowerShell)
.\scripts\docker-rebuild.ps1 -Service all

# Rebuild specific service
.\scripts\docker-rebuild.ps1 -Service api
.\scripts\docker-rebuild.ps1 -Service scheduler
.\scripts\docker-rebuild.ps1 -Service frontend
```

## What Updates Automatically?

| Service | Development Mode | Production Mode |
|---------|------------------|-----------------|
| **API** | ✅ Auto-reloads | ❌ Needs rebuild |
| **Frontend** | ✅ Auto-reloads | ❌ Needs rebuild |
| **Scheduler** | ⚠️ Needs restart | ❌ Needs rebuild |

## Quick Commands

### Development Mode
```powershell
# Start with hot-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Restart scheduler after code changes
docker-compose restart scheduler
```

### Production Mode
```powershell
# Rebuild and restart
.\scripts\docker-rebuild.ps1 -Service all

# Or manually
docker-compose build --no-cache api
docker-compose up -d api
```

## When to Rebuild vs Restart

**Rebuild needed:**
- New Python dependencies (requirements.txt)
- New Node dependencies (package.json)
- Dockerfile changes
- First time setup

**Restart sufficient (dev mode only):**
- Code changes in src/
- Code changes in frontend/src/
- Scheduler code changes (needs restart)

See `DOCKER_DEVELOPMENT.md` for full details.

