# PowerShell script to setup the PostgreSQL database with TimescaleDB

Write-Host "Setting up PostgreSQL database with TimescaleDB..." -ForegroundColor Cyan

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "Docker is running" -ForegroundColor Green
} catch {
    Write-Host "Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if docker-compose is available
try {
    docker-compose --version | Out-Null
    Write-Host "docker-compose is available" -ForegroundColor Green
} catch {
    Write-Host "docker-compose is not available. Please install docker-compose." -ForegroundColor Red
    exit 1
}

# Stop any existing containers
Write-Host ""
Write-Host "Stopping any existing containers..." -ForegroundColor Yellow
docker-compose down

# Start the database container
Write-Host ""
Write-Host "Starting database container..." -ForegroundColor Yellow
docker-compose up -d

# Wait for database to be ready
Write-Host ""
Write-Host "Waiting for database to be ready..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts) {
    try {
        $format = '{{.State.Health.Status}}'
        $health = docker inspect --format=$format investment_platform_db 2>$null
        if ($health -eq "healthy") {
            $ready = $true
            break
        }
    } catch {
        # Container might not be ready yet
    }
    
    Start-Sleep -Seconds 2
    $attempt++
    Write-Host "." -NoNewline
}

Write-Host ""

if ($ready) {
    Write-Host "Database is ready!" -ForegroundColor Green
} else {
    Write-Host "Database container started but health check timed out. It may still be initializing." -ForegroundColor Yellow
    Write-Host "You can check status with: docker-compose ps" -ForegroundColor Yellow
}

# Display connection information
Write-Host ""
Write-Host "Database connection information:" -ForegroundColor Cyan
Write-Host "  Host: localhost" -ForegroundColor White
Write-Host "  Port: 5432" -ForegroundColor White
Write-Host "  Database: investment_platform" -ForegroundColor White
Write-Host "  User: postgres" -ForegroundColor White
Write-Host "  Password: postgres" -ForegroundColor White

Write-Host ""
Write-Host "To test connectivity, run:" -ForegroundColor Cyan
Write-Host "  python tests/test_connection.py" -ForegroundColor White

Write-Host ""
Write-Host "To view logs:" -ForegroundColor Cyan
Write-Host "  docker-compose logs -f" -ForegroundColor White

Write-Host ""
Write-Host "To stop the database:" -ForegroundColor Cyan
Write-Host "  docker-compose down" -ForegroundColor White
