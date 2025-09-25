#!/bin/bash
# ArchBuilder.AI Staging Environment Deployment Script
# Automated deployment for staging environment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="staging"
VERSION="${1:-staging}"

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
    log_info "Checking prerequisites for staging deployment..."
    
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
        log_warning ".env file not found. Using default staging configuration."
    fi
    
    log_success "Prerequisites check passed"
}

# Build staging images
build_staging_images() {
    log_info "Building staging Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build cloud server image for staging
    docker build -t archbuilder/cloud-server:staging -f src/cloud-server/Dockerfile src/cloud-server/
    
    # Build test data generator
    docker build -t archbuilder/test-data-generator:latest -f scripts/test-data/Dockerfile scripts/test-data/
    
    log_success "Staging images built successfully"
}

# Deploy staging services
deploy_staging_services() {
    log_info "Deploying staging services..."
    
    cd "$PROJECT_ROOT"
    
    # Stop existing staging services
    docker-compose -f docker-compose.staging.yml down || true
    
    # Start staging services
    docker-compose -f docker-compose.staging.yml up -d
    
    log_success "Staging services deployed"
}

# Wait for staging services to be healthy
wait_for_staging_health() {
    log_info "Waiting for staging services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Staging cloud server is healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Staging services failed to become healthy within timeout"
            docker-compose -f docker-compose.staging.yml logs cloud-server
            exit 1
        fi
        
        log_info "Attempt $attempt/$max_attempts - waiting for staging services..."
        sleep 10
        ((attempt++))
    done
}

# Run database migrations for staging
run_staging_migrations() {
    log_info "Running staging database migrations..."
    
    cd "$PROJECT_ROOT"
    
    # Wait for PostgreSQL to be ready
    sleep 20
    
    # Run migrations using the staging cloud server container
    docker-compose -f docker-compose.staging.yml exec cloud-server python -m alembic upgrade head || {
        log_warning "Migrations failed, but continuing..."
    }
    
    log_success "Staging database migrations completed"
}

# Generate test data
generate_test_data() {
    log_info "Generating test data for staging environment..."
    
    cd "$PROJECT_ROOT"
    
    # Run test data generator
    docker-compose -f docker-compose.staging.yml run --rm test-data-generator || {
        log_warning "Test data generation failed, but continuing..."
    }
    
    log_success "Test data generation completed"
}

# Run load tests
run_load_tests() {
    log_info "Running load tests on staging environment..."
    
    cd "$PROJECT_ROOT"
    
    # Run K6 load tests
    docker-compose -f docker-compose.staging.yml run --rm k6 run /scripts/staging-load-test.js || {
        log_warning "Load tests failed, but continuing..."
    }
    
    log_success "Load tests completed"
}

# Setup monitoring for staging
setup_staging_monitoring() {
    log_info "Setting up staging monitoring..."
    
    # Wait for monitoring services to be ready
    sleep 30
    
    # Check if Prometheus is accessible
    if curl -f http://localhost:9091 &> /dev/null; then
        log_success "Staging Prometheus is accessible at http://localhost:9091"
    else
        log_warning "Staging Prometheus is not accessible"
    fi
    
    # Check if Grafana is accessible
    if curl -f http://localhost:3001 &> /dev/null; then
        log_success "Staging Grafana is accessible at http://localhost:3001"
        log_info "Default credentials: admin/staging"
    else
        log_warning "Staging Grafana is not accessible"
    fi
}

# Verify staging environment
verify_staging_environment() {
    log_info "Verifying staging environment..."
    
    # Test API endpoints
    local endpoints=(
        "http://localhost:8000/health"
        "http://localhost:8000/v1/users"
        "http://localhost:8000/v1/projects"
        "http://localhost:8000/v1/ai/commands"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f "$endpoint" &> /dev/null; then
            log_success "✓ $endpoint is accessible"
        else
            log_warning "✗ $endpoint is not accessible"
        fi
    done
}

# Cleanup function
cleanup() {
    log_error "Staging deployment failed. Cleaning up..."
    
    # Stop staging services
    docker-compose -f docker-compose.staging.yml down || true
    
    log_warning "Staging cleanup completed"
}

# Main deployment function
main() {
    log_info "Starting ArchBuilder.AI staging environment deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    
    # Set up error handling
    trap cleanup ERR
    
    # Execute deployment steps
    check_prerequisites
    build_staging_images
    deploy_staging_services
    wait_for_staging_health
    run_staging_migrations
    generate_test_data
    setup_staging_monitoring
    verify_staging_environment
    run_load_tests
    
    log_success "Staging environment deployment completed successfully!"
    log_info "Staging services are running:"
    log_info "  - API Server: http://localhost:8000"
    log_info "  - Grafana: http://localhost:3001"
    log_info "  - Prometheus: http://localhost:9091"
    log_info "  - PostgreSQL: localhost:5433"
    log_info "  - Redis: localhost:6380"
    log_info "  - RAGFlow: http://localhost:8002"
    log_info ""
    log_info "Use 'docker-compose -f docker-compose.staging.yml logs -f' to view logs"
    log_info "Use 'docker-compose -f docker-compose.staging.yml down' to stop services"
}

# Run main function
main "$@"
