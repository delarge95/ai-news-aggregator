#!/bin/bash

# AI News Aggregator - Production Deployment Script
# Manages the complete production deployment lifecycle

set -e

COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning "Environment file $ENV_FILE not found!"
        log_info "Creating $ENV_FILE from example..."
        if [[ -f ".env.prod.example" ]]; then
            cp .env.prod.example $ENV_FILE
            log_warning "Please edit $ENV_FILE with your production values!"
        else
            log_error ".env.prod.example not found!"
            exit 1
        fi
    fi
}

init_environment() {
    log_info "Initializing production environment..."
    if [[ -f "init-docker-prod.sh" ]]; then
        chmod +x init-docker-prod.sh
        ./init-docker-prod.sh
    else
        log_error "init-docker-prod.sh not found!"
        exit 1
    fi
}

build_images() {
    log_info "Building Docker images..."
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE build --no-cache
    log_success "Images built successfully!"
}

deploy() {
    log_info "Starting production services..."
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d
    log_success "Services started successfully!"
}

status() {
    log_info "Checking service status..."
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE ps
}

logs() {
    log_info "Showing service logs..."
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE logs -f --tail=50
}

stop() {
    log_info "Stopping production services..."
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE down
    log_success "Services stopped!"
}

cleanup() {
    log_warning "Cleaning up Docker resources..."
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE down -v --remove-orphans
    docker system prune -f
    log_success "Cleanup completed!"
}

health_check() {
    log_info "Performing health checks..."
    
    # Check if services are running
    running_services=$(docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE ps --services --filter "status=running" | wc -l)
    total_services=$(docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE ps --services | wc -l)
    
    if [[ $running_services -eq $total_services ]] && [[ $total_services -gt 0 ]]; then
        log_success "All $total_services services are running!"
        
        # Check individual service health
        log_info "Checking service health..."
        docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE ps
        
        # Test API endpoint
        log_info "Testing API endpoint..."
        if curl -f -s http://localhost/health > /dev/null; then
            log_success "API endpoint is responding!"
        else
            log_warning "API endpoint check failed - service might still be starting"
        fi
    else
        log_error "Only $running_services out of $total_services services are running!"
        docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE ps
        exit 1
    fi
}

show_help() {
    echo "AI News Aggregator - Production Deployment"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy      Full deployment (init + build + start)"
    echo "  build       Build Docker images only"
    echo "  start       Start services only"
    echo "  stop        Stop all services"
    echo "  restart     Restart services"
    echo "  status      Show service status"
    echo "  logs        Show service logs"
    echo "  health      Perform health checks"
    echo "  cleanup     Stop services and clean up resources"
    echo "  help        Show this help message"
    echo ""
    echo "Environment:"
    echo "  Uses $COMPOSE_FILE and $ENV_FILE"
}

# Main script logic
case "${1:-help}" in
    deploy)
        check_env_file
        init_environment
        build_images
        deploy
        log_info "Waiting for services to be ready..."
        sleep 30
        health_check
        ;;
    build)
        check_env_file
        build_images
        ;;
    start)
        check_env_file
        deploy
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        deploy
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    health)
        health_check
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac