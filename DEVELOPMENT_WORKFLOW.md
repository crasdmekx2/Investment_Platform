# Development Workflow - Fast Testing Guide

## Current Status

✅ **Your containers have source code volume-mounted** - This is good!
❌ **But the API container may not have hot-reload enabled** - Need to check/restart

## Best Practice: Use Development Mode

### Option 1: Development Mode with Hot Reload (FASTEST - Recommended)

This is the **fastest way** to test changes. No rebuilds needed!

```powershell
# Stop current containers
docker-compose down

# Start in development mode (with hot-reload)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**What this does:**
- ✅ API auto-reloads when you change Python files (no rebuild needed!)
- ✅ Frontend auto-rebuilds when you change React/TypeScript files
- ✅ Source code is volume-mounted (changes are immediate)
- ⚠️ Scheduler needs restart: `docker-compose restart scheduler`

**After making code changes:**
- API: Just wait 2-3 seconds - it auto-reloads!
- Frontend: Just wait 2-3 seconds - Vite rebuilds!
- Scheduler: Run `docker-compose restart scheduler`

### Option 2: Restart API Container (Quick Fix for Current Setup)

If you're already running and just need to pick up the latest change:

```powershell
# Restart API to pick up code changes (if volume-mounted)
docker-compose restart api

# Or restart scheduler if you changed scheduler code
docker-compose restart scheduler
```

### Option 3: Rebuild (Only When Needed)

Only rebuild when:
- Adding new Python dependencies (`requirements.txt`)
- Adding new Node dependencies (`package.json`)
- Changing Dockerfiles
- First time setup

```powershell
# Rebuild specific service
docker-compose build api
docker-compose up -d api

# Or use the helper script
.\scripts\docker-rebuild.ps1 -Service api
```

## Recommended Workflow

### For Active Development (Daily Use)

1. **Start once in dev mode:**
   ```powershell
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
   ```

2. **Make code changes** - API and Frontend auto-update!

3. **For scheduler changes:**
   ```powershell
   docker-compose restart scheduler
   ```

4. **Test in browser** - Changes are already live!

### For Testing Specific Changes

1. Make your code change
2. Wait 2-3 seconds (auto-reload)
3. Test in browser
4. No rebuild needed!

## Current Issue: Your Change Not Active

The fix I made to `scheduler.py` isn't active yet. Here's how to activate it:

**Quick fix (if volume-mounted):**
```powershell
docker-compose restart api
```

**Better long-term (use dev mode):**
```powershell
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Speed Comparison

| Method | Time | When to Use |
|--------|------|-------------|
| **Dev Mode (hot-reload)** | 2-3 seconds | ✅ Daily development |
| **Restart container** | 5-10 seconds | Quick fix |
| **Rebuild container** | 1-3 minutes | New dependencies |

## Verification

After restarting, verify your changes are active:

```powershell
# Check if your code change is in the container
docker exec investment_platform_api cat /app/src/investment_platform/api/routers/scheduler.py | Select-String -Pattern "Add job to scheduler so it can be triggered"
```

If you see the new comment, your change is active!

## Summary

**Best practice:** Use `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up` for development. This gives you:
- Instant code updates (2-3 seconds)
- No rebuilds needed
- Faster iteration cycle

**Current fix needed:** Restart the API container to pick up the scheduler.py change:
```powershell
docker-compose restart api
```

