#!/bin/bash
# ArchBuilder.AI Rollback Script
# Automated rollback for production environment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-production}"
BACKUP_VERSION="${2:-latest}"

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

# List available backups
list_backups() {
    log_info "Available backups:"
    if [ -d "$PROJECT_ROOT/backups" ]; then
        ls -la "$PROJECT_ROOT/backups" | grep "^d" | awk '{print $9}' | sort -r
    else
        log_warning "No backups directory found"
    fi
}

# Stop current services
stop_services() {
    log_info "Stopping current services..."
    
    cd "$PROJECT_ROOT"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f docker-compose.prod.yml down
    else
        docker-compose down
    fi
    
    log_success "Services stopped"
}

# Restore database
restore_database() {
    local backup_dir="$PROJECT_ROOT/backups/$BACKUP_VERSION"
    
    if [ ! -d "$backup_dir" ]; then
        log_error "Backup directory not found: $backup_dir"
        exit 1
    fi
    
    if [ ! -f "$backup_dir/database.sql" ]; then
        log_warning "Database backup not found, skipping database restore"
        return
    fi
    
    log_info "Restoring database from backup..."
    
    cd "$PROJECT_ROOT"
    
    # Start only PostgreSQL first
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f docker-compose.prod.yml up -d postgres
    else
        docker-compose up -d postgres
    fi
    
    # Wait for PostgreSQL to be ready
    sleep 30
    
    # Restore database
    if docker-compose exec -T postgres psql -U archbuilder -d archbuilder < "$backup_dir/database.sql"; then
        log_success "Database restored successfully"
    else
        log_error "Failed to restore database"
        exit 1
    fi
}

# Restore configuration
restore_configuration() {
    local backup_dir="$PROJECT_ROOT/backups/$BACKUP_VERSION"
    
    if [ ! -d "$backup_dir/configs" ]; then
        log_warning "Configuration backup not found, skipping configuration restore"
        return
    fi
    
    log_info "Restoring configuration from backup..."
    
    # Backup current config
    cp -r "$PROJECT_ROOT/configs" "$PROJECT_ROOT/configs.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Restore from backup
    cp -r "$backup_dir/configs" "$PROJECT_ROOT/"
    
    log_success "Configuration restored"
}

# Deploy previous version
deploy_previous_version() {
    log_info "Deploying previous version..."
    
    cd "$PROJECT_ROOT"
    
    # Use the backup version for deployment
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f docker-compose.prod.yml up -d
    else
        docker-compose up -d
    fi
    
    log_success "Previous version deployed"
}

# Verify rollback
verify_rollback() {
    log_info "Verifying rollback..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Rollback verification successful"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Rollback verification failed"
            exit 1
        fi
        
        log_info "Attempt $attempt/$max_attempts - waiting for services..."
        sleep 10
        ((attempt++))
    done
}

# Cleanup old containers
cleanup() {
    log_info "Cleaning up old containers and images..."
    
    # Remove old containers
    docker container prune -f
    
    # Remove unused images
    docker image prune -f
    
    log_success "Cleanup completed"
}

# Main rollback function
main() {
    log_info "Starting ArchBuilder.AI rollback..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Backup version: $BACKUP_VERSION"
    
    # List available backups
    list_backups
    
    # Confirm rollback
    read -p "Are you sure you want to rollback? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Rollback cancelled"
        exit 0
    fi
    
    # Execute rollback steps
    stop_services
    restore_database
    restore_configuration
    deploy_previous_version
    verify_rollback
    cleanup
    
    log_success "Rollback completed successfully!"
    log_info "Services are running with previous version"
}

# Run main function
main "$@"
