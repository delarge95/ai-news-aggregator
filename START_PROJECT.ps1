# Start AI News Aggregator Project
# Script to start all services in the correct order

$PROJECT_DIR = "e:\Portafolios-aplicaciones_laborales-plan_de_estudio\job-search-strategy\projects\ai-news-aggregator"
$DOCKER_COMPOSE_FILE = "$PROJECT_DIR\docker-compose.yml"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Starting AI News Aggregator Project" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if docker is running
Write-Host "✓ Checking Docker..." -ForegroundColor Yellow
$dockerCheck = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker is running" -ForegroundColor Green
Write-Host ""

# Stop existing containers
Write-Host "Stopping any existing containers..." -ForegroundColor Yellow
docker-compose -f $DOCKER_COMPOSE_FILE down 2>&1 | Out-Null
Start-Sleep -Seconds 2

# Start services
Write-Host "Starting services..." -ForegroundColor Yellow
cd $PROJECT_DIR
docker-compose -f docker-compose.yml up -d

Write-Host ""
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check status
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Service Status:" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host ""
Write-Host "Access Points:" -ForegroundColor Green
Write-Host "  • Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "  • API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  • PostgreSQL: localhost:5432" -ForegroundColor Green
Write-Host "  • Redis: localhost:6379" -ForegroundColor Green

Write-Host ""
Write-Host "To view logs:" -ForegroundColor Yellow
Write-Host "  • All logs: docker-compose logs -f" -ForegroundColor Gray
Write-Host "  • Backend: docker-compose logs -f backend" -ForegroundColor Gray
Write-Host "  • Frontend: docker-compose logs -f frontend" -ForegroundColor Gray
Write-Host ""
