#!/bin/bash
# ArchBuilder.AI Data Recovery Script
# Comprehensive data recovery from backups

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_FILE="${1:-}"
ENCRYPTION_KEY="${2:-}"
RECOVERY_TYPE="${3:-full}"  # full, database, configs, or selective

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
    
    local backup_dir="$PROJECT_ROOT/backups"
    if [ -d "$backup_dir" ]; then
        find "$backup_dir" -name "*.tar.gz.enc" -o -name "*.tar.gz" | sort -r | head -10
    else
        log_warning "No backups directory found"
    fi
}

# Decrypt backup
decrypt_backup() {
    local backup_file="$1"
    local encryption_key="$2"
    local temp_dir="/tmp/archbuilder-recovery-$(date +%s)"
    
    log_info "Decrypting backup: $backup_file"
    
    # Create temporary directory
    mkdir -p "$temp_dir"
    
    # Decrypt backup
    if [[ "$backup_file" == *.enc ]]; then
        if [ -z "$encryption_key" ]; then
            log_error "Encryption key required for encrypted backup"
            return 1
        fi
        
        echo "$encryption_key" | openssl enc -aes-256-cbc -d -in "$backup_file" | tar -xzf - -C "$temp_dir"
    else
        tar -xzf "$backup_file" -C "$temp_dir"
    fi
    
    echo "$temp_dir"
}

# Restore database
restore_database() {
    local recovery_dir="$1"
    local db_backup_file=$(find "$recovery_dir" -name "*.sql.gz" | head -1)
    
    if [ -z "$db_backup_file" ]; then
        log_warning "No database backup found"
        return 0
    fi
    
    log_info "Restoring database from: $db_backup_file"
    
    # Check if running in Kubernetes
    if kubectl get pods -n archbuilder -l app=postgresql &> /dev/null; then
        # Kubernetes environment
        gunzip -c "$db_backup_file" | kubectl exec -i -n archbuilder deployment/postgresql -- psql -U archbuilder -d archbuilder
    else
        # Docker environment
        gunzip -c "$db_backup_file" | docker-compose exec -T postgres psql -U archbuilder -d archbuilder
    fi
    
    log_success "Database restored successfully"
}

# Restore configurations
restore_configurations() {
    local recovery_dir="$1"
    local config_dir="$recovery_dir/configs"
    
    if [ ! -d "$config_dir" ]; then
        log_warning "No configuration backup found"
        return 0
    fi
    
    log_info "Restoring configuration files..."
    
    # Backup current configurations
    local current_config_backup="$PROJECT_ROOT/configs.backup.$(date +%Y%m%d_%H%M%S)"
    if [ -d "$PROJECT_ROOT/configs" ]; then
        cp -r "$PROJECT_ROOT/configs" "$current_config_backup"
        log_info "Current configurations backed up to: $current_config_backup"
    fi
    
    # Restore configurations
    cp -r "$config_dir"/* "$PROJECT_ROOT/"
    
    log_success "Configurations restored successfully"
}

# Restore logs
restore_logs() {
    local recovery_dir="$1"
    local logs_dir="$recovery_dir/logs"
    
    if [ ! -d "$logs_dir" ]; then
        log_warning "No logs backup found"
        return 0
    fi
    
    log_info "Restoring application logs..."
    
    # Create logs directory
    mkdir -p "$PROJECT_ROOT/logs"
    
    # Restore logs
    cp -r "$logs_dir"/* "$PROJECT_ROOT/logs/"
    
    log_success "Logs restored successfully"
}

# Restore volumes
restore_volumes() {
    local recovery_dir="$1"
    local volumes_dir="$recovery_dir/volumes"
    
    if [ ! -d "$volumes_dir" ]; then
        log_warning "No volumes backup found"
        return 0
    fi
    
    log_info "Restoring persistent volumes..."
    
    # Restore Docker volumes
    if command -v docker &> /dev/null; then
        for volume_file in "$volumes_dir"/*.tar.gz; do
            if [ -f "$volume_file" ]; then
                local volume_name=$(basename "$volume_file" .tar.gz)
                log_info "Restoring Docker volume: $volume_name"
                
                # Create volume if it doesn't exist
                docker volume create "$volume_name" 2>/dev/null || true
                
                # Restore volume
                docker run --rm -v "$volume_name":/target -v "$volumes_dir":/backup alpine tar -xzf "/backup/$(basename "$volume_file")" -C /target
            fi
        done
    fi
    
    # Restore Kubernetes volumes
    if command -v kubectl &> /dev/null; then
        for pvc_file in "$volumes_dir"/*.tar.gz; do
            if [ -f "$pvc_file" ]; then
                local pvc_name=$(basename "$pvc_file" .tar.gz)
                log_info "Restoring Kubernetes PVC: $pvc_name"
                
                # Create a temporary pod to restore the PVC
                kubectl run restore-pod --image=alpine --rm -i --restart=Never -n archbuilder --overrides='
                {
                    "spec": {
                        "containers": [{
                            "name": "restore-pod",
                            "image": "alpine",
                            "command": ["sh", "-c", "tar -xzf /backup/pvc.tar.gz -C /data"],
                            "volumeMounts": [{
                                "name": "data",
                                "mountPath": "/data"
                            }]
                        }],
                        "volumes": [{
                            "name": "data",
                            "persistentVolumeClaim": {
                                "claimName": "'$pvc_name'"
                            }
                        }]
                    }
                }' -- tar -xzf /backup/pvc.tar.gz -C /data
            fi
        done
    fi
    
    log_success "Volumes restored successfully"
}

# Restore secrets
restore_secrets() {
    local recovery_dir="$1"
    local secrets_dir="$recovery_dir/secrets"
    
    if [ ! -d "$secrets_dir" ]; then
        log_warning "No secrets backup found"
        return 0
    fi
    
    log_info "Restoring secrets..."
    
    # Restore Kubernetes secrets
    if command -v kubectl &> /dev/null && [ -f "$secrets_dir/k8s-secrets.yaml" ]; then
        kubectl apply -f "$secrets_dir/k8s-secrets.yaml"
        log_success "Kubernetes secrets restored"
    fi
    
    # Restore environment variables
    if [ -f "$secrets_dir/env-vars.txt" ]; then
        log_info "Environment variables backup found: $secrets_dir/env-vars.txt"
        log_warning "Please manually restore environment variables from the backup"
    fi
    
    log_success "Secrets restored successfully"
}

# Verify recovery
verify_recovery() {
    log_info "Verifying recovery..."
    
    # Check if services are running
    if command -v kubectl &> /dev/null; then
        if kubectl get pods -n archbuilder -l app.kubernetes.io/name=archbuilder --field-selector=status.phase=Running | grep -q archbuilder; then
            log_success "✓ Kubernetes pods are running"
        else
            log_warning "✗ Kubernetes pods are not running"
        fi
    fi
    
    if command -v docker &> /dev/null; then
        if docker-compose ps | grep -q "Up"; then
            log_success "✓ Docker containers are running"
        else
            log_warning "✗ Docker containers are not running"
        fi
    fi
    
    # Check database connectivity
    if command -v kubectl &> /dev/null; then
        if kubectl exec -n archbuilder deployment/postgresql -- pg_isready -U archbuilder -d archbuilder &> /dev/null; then
            log_success "✓ Database is accessible"
        else
            log_warning "✗ Database is not accessible"
        fi
    fi
    
    log_success "Recovery verification completed"
}

# Cleanup temporary files
cleanup() {
    local temp_dir="$1"
    
    log_info "Cleaning up temporary files..."
    rm -rf "$temp_dir"
    log_success "Cleanup completed"
}

# Main recovery function
main() {
    log_info "Starting ArchBuilder.AI data recovery procedures..."
    log_info "Recovery Type: $RECOVERY_TYPE"
    
    # Check if backup file is provided
    if [ -z "$BACKUP_FILE" ]; then
        log_error "Backup file not specified"
        log_info "Usage: $0 <backup_file> [encryption_key] [recovery_type]"
        list_backups
        exit 1
    fi
    
    # Check if backup file exists
    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup file not found: $BACKUP_FILE"
        list_backups
        exit 1
    fi
    
    # Decrypt backup
    local recovery_dir=$(decrypt_backup "$BACKUP_FILE" "$ENCRYPTION_KEY")
    
    # Perform recovery based on type
    case "$RECOVERY_TYPE" in
        "full")
            restore_database "$recovery_dir"
            restore_configurations "$recovery_dir"
            restore_logs "$recovery_dir"
            restore_volumes "$recovery_dir"
            restore_secrets "$recovery_dir"
            ;;
        "database")
            restore_database "$recovery_dir"
            ;;
        "configs")
            restore_configurations "$recovery_dir"
            ;;
        "selective")
            log_info "Selective recovery - choose components to restore:"
            read -p "Restore database? (y/N): " restore_db
            read -p "Restore configurations? (y/N): " restore_configs
            read -p "Restore logs? (y/N): " restore_logs
            read -p "Restore volumes? (y/N): " restore_volumes
            read -p "Restore secrets? (y/N): " restore_secrets
            
            if [[ "$restore_db" =~ ^[Yy]$ ]]; then
                restore_database "$recovery_dir"
            fi
            if [[ "$restore_configs" =~ ^[Yy]$ ]]; then
                restore_configurations "$recovery_dir"
            fi
            if [[ "$restore_logs" =~ ^[Yy]$ ]]; then
                restore_logs "$recovery_dir"
            fi
            if [[ "$restore_volumes" =~ ^[Yy]$ ]]; then
                restore_volumes "$recovery_dir"
            fi
            if [[ "$restore_secrets" =~ ^[Yy]$ ]]; then
                restore_secrets "$recovery_dir"
            fi
            ;;
        *)
            log_error "Invalid recovery type: $RECOVERY_TYPE"
            log_info "Valid types: full, database, configs, selective"
            exit 1
            ;;
    esac
    
    # Verify recovery
    verify_recovery
    
    # Cleanup
    cleanup "$recovery_dir"
    
    log_success "Data recovery procedures completed successfully!"
    log_info "Please restart services to ensure all components are working correctly"
}

# Run main function
main "$@"
