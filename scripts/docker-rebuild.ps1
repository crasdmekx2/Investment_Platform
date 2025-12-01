# PowerShell script to rebuild Docker containers after code changes
# This script rebuilds and restarts containers to pick up code changes

param(
    [string]$Service = "all"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Rebuilding Docker Containers" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if we're in development or production mode
$devMode = Test-Path "docker-compose.dev.yml"
if ($devMode) {
    Write-Host "Detected development mode. Using docker-compose.dev.yml" -ForegroundColor Yellow
    $composeFiles = "-f docker-compose.yml -f docker-compose.dev.yml"
} else {
    Write-Host "Using production mode" -ForegroundColor Yellow
    $composeFiles = "-f docker-compose.yml"
}

# Determine which services to rebuild
switch ($Service.ToLower()) {
    "all" {
        Write-Host "Rebuilding all services..." -ForegroundColor Green
        docker-compose $composeFiles.Split(' ') build --no-cache
        docker-compose $composeFiles.Split(' ') up -d
    }
    "api" {
        Write-Host "Rebuilding API service..." -ForegroundColor Green
        docker-compose $composeFiles.Split(' ') build --no-cache api
        docker-compose $composeFiles.Split(' ') up -d api
    }
    "frontend" {
        Write-Host "Rebuilding Frontend service..." -ForegroundColor Green
        docker-compose $composeFiles.Split(' ') build --no-cache frontend
        docker-compose $composeFiles.Split(' ') up -d frontend
    }
    "scheduler" {
        Write-Host "Rebuilding Scheduler service..." -ForegroundColor Green
        docker-compose $composeFiles.Split(' ') build --no-cache scheduler
        docker-compose $composeFiles.Split(' ') up -d scheduler
    }
    "api-scheduler" {
        Write-Host "Rebuilding API and Scheduler services..." -ForegroundColor Green
        docker-compose $composeFiles.Split(' ') build --no-cache api scheduler
        docker-compose $composeFiles.Split(' ') up -d api scheduler
    }
    default {
        Write-Host "Invalid service. Use: all, api, frontend, scheduler, or api-scheduler" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Rebuild complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Container status:" -ForegroundColor Yellow
docker-compose $composeFiles.Split(' ') ps

