#!/bin/bash
# ArchBuilder.AI Deployment Script
# Automated deployment for production environment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-production}"
VERSION="${2:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_error ".env file not found. Please copy env.example to .env and configure it."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build cloud server image
    docker build -t archbuilder/cloud-server:$VERSION -f src/cloud-server/Dockerfile src/cloud-server/
    
    log_success "Docker images built successfully"
}

# Deploy services
deploy_services() {
    log_info "Deploying services for environment: $ENVIRONMENT"
    
    cd "$PROJECT_ROOT"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f docker-compose.prod.yml up -d
    else
        docker-compose up -d
    fi
    
    log_success "Services deployed successfully"
}

# Wait for services to be healthy
wait_for_health() {
    log_info "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Cloud server is healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Services failed to become healthy within timeout"
            exit 1
        fi
        
        log_info "Attempt $attempt/$max_attempts - waiting for services..."
        sleep 10
        ((attempt++))
    done
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd "$PROJECT_ROOT"
    
    # Run migrations using the cloud server container
    docker-compose exec cloud-server python -m alembic upgrade head
    
    log_success "Database migrations completed"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Wait for Prometheus to be ready
    sleep 30
    
    # Check if Grafana is accessible
    if curl -f http://localhost:3000 &> /dev/null; then
        log_success "Grafana is accessible at http://localhost:3000"
        log_info "Default credentials: admin/admin"
    else
        log_warning "Grafana is not accessible"
    fi
    
    # Check if Prometheus is accessible
    if curl -f http://localhost:9090 &> /dev/null; then
        log_success "Prometheus is accessible at http://localhost:9090"
    else
        log_warning "Prometheus is not accessible"
    fi
}

# Create backup
create_backup() {
    log_info "Creating backup before deployment..."
    
    local backup_dir="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup database
    if docker-compose exec -T postgres pg_dump -U archbuilder archbuilder > "$backup_dir/database.sql"; then
        log_success "Database backup created: $backup_dir/database.sql"
    else
        log_warning "Failed to create database backup"
    fi
    
    # Backup configuration
    cp -r "$PROJECT_ROOT/configs" "$backup_dir/"
    log_success "Configuration backup created"
}

# Rollback function
rollback() {
    log_error "Deployment failed. Initiating rollback..."
    
    cd "$PROJECT_ROOT"
    
    # Stop current services
    docker-compose down
    
    # Restore from backup if available
    local latest_backup=$(ls -t "$PROJECT_ROOT/backups" | head -n1)
    if [ -n "$latest_backup" ]; then
        log_info "Restoring from backup: $latest_backup"
        # Add rollback logic here
    fi
    
    log_warning "Rollback completed. Please check the logs and fix issues before retrying."
    exit 1
}

# Main deployment function
main() {
    log_info "Starting ArchBuilder.AI deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    
    # Set up error handling
    trap rollback ERR
    
    # Execute deployment steps
    check_prerequisites
    create_backup
    build_images
    deploy_services
    wait_for_health
    run_migrations
    setup_monitoring
    
    log_success "Deployment completed successfully!"
    log_info "Services are running:"
    log_info "  - API Server: http://localhost:8000"
    log_info "  - Grafana: http://localhost:3000"
    log_info "  - Prometheus: http://localhost:9090"
    log_info "  - PostgreSQL: localhost:5432"
    log_info "  - Redis: localhost:6379"
}

# Run main function
main "$@"
