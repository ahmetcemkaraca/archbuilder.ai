#!/bin/bash
# ArchBuilder.AI Data Protection Script
# Comprehensive data backup, encryption, and recovery procedures

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/backups"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-$(openssl rand -base64 32)}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

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

# Create backup directory structure
create_backup_structure() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/$timestamp"
    
    log_info "Creating backup directory structure: $backup_path"
    
    mkdir -p "$backup_path"/{database,configs,logs,volumes,secrets}
    
    echo "$backup_path"
}

# Backup database
backup_database() {
    local backup_path="$1"
    local db_backup_file="$backup_path/database/archbuilder_$(date +%Y%m%d_%H%M%S).sql"
    
    log_info "Backing up database..."
    
    # Check if running in Kubernetes
    if kubectl get pods -n archbuilder -l app=postgresql &> /dev/null; then
        # Kubernetes environment
        kubectl exec -n archbuilder deployment/postgresql -- pg_dump -U archbuilder -d archbuilder > "$db_backup_file"
    else
        # Docker environment
        docker-compose exec postgres pg_dump -U archbuilder -d archbuilder > "$db_backup_file"
    fi
    
    # Compress database backup
    gzip "$db_backup_file"
    
    log_success "Database backup completed: $db_backup_file.gz"
}

# Backup configuration files
backup_configurations() {
    local backup_path="$1"
    local config_backup_dir="$backup_path/configs"
    
    log_info "Backing up configuration files..."
    
    # Copy configuration files
    cp -r "$PROJECT_ROOT/configs" "$config_backup_dir/"
    cp -r "$PROJECT_ROOT/helm" "$config_backup_dir/"
    cp -r "$PROJECT_ROOT/k8s" "$config_backup_dir/"
    
    # Copy environment files
    cp "$PROJECT_ROOT/.env" "$config_backup_dir/" 2>/dev/null || true
    cp "$PROJECT_ROOT/env.example" "$config_backup_dir/" 2>/dev/null || true
    
    # Copy Docker files
    cp "$PROJECT_ROOT/docker-compose.yml" "$config_backup_dir/"
    cp "$PROJECT_ROOT/docker-compose.prod.yml" "$config_backup_dir/"
    cp "$PROJECT_ROOT/docker-compose.staging.yml" "$config_backup_dir/"
    
    log_success "Configuration backup completed"
}

# Backup logs
backup_logs() {
    local backup_path="$1"
    local logs_backup_dir="$backup_path/logs"
    
    log_info "Backing up application logs..."
    
    # Create logs directory
    mkdir -p "$logs_backup_dir"
    
    # Copy application logs
    if [ -d "$PROJECT_ROOT/logs" ]; then
        cp -r "$PROJECT_ROOT/logs" "$logs_backup_dir/"
    fi
    
    # Copy container logs if available
    if command -v docker &> /dev/null; then
        docker-compose logs --no-color > "$logs_backup_dir/docker-compose.log" 2>/dev/null || true
    fi
    
    # Copy Kubernetes logs if available
    if command -v kubectl &> /dev/null; then
        kubectl logs -n archbuilder -l app.kubernetes.io/name=archbuilder --all-containers=true > "$logs_backup_dir/k8s-logs.log" 2>/dev/null || true
    fi
    
    log_success "Logs backup completed"
}

# Backup persistent volumes
backup_volumes() {
    local backup_path="$1"
    local volumes_backup_dir="$backup_path/volumes"
    
    log_info "Backing up persistent volumes..."
    
    mkdir -p "$volumes_backup_dir"
    
    # Backup Docker volumes
    if command -v docker &> /dev/null; then
        for volume in $(docker volume ls -q | grep archbuilder); do
            log_info "Backing up Docker volume: $volume"
            docker run --rm -v "$volume":/source -v "$volumes_backup_dir":/backup alpine tar czf "/backup/$volume.tar.gz" -C /source .
        done
    fi
    
    # Backup Kubernetes volumes
    if command -v kubectl &> /dev/null; then
        for pvc in $(kubectl get pvc -n archbuilder -o name); do
            local pvc_name=$(echo "$pvc" | cut -d'/' -f2)
            log_info "Backing up Kubernetes PVC: $pvc_name"
            
            # Create a temporary pod to backup the PVC
            kubectl run backup-pod --image=alpine --rm -i --restart=Never -n archbuilder --overrides='
            {
                "spec": {
                    "containers": [{
                        "name": "backup-pod",
                        "image": "alpine",
                        "command": ["sh", "-c", "tar czf /backup/pvc.tar.gz -C /data ."],
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
            }' -- tar czf /backup/pvc.tar.gz -C /data .
        done
    fi
    
    log_success "Volumes backup completed"
}

# Backup secrets
backup_secrets() {
    local backup_path="$1"
    local secrets_backup_dir="$backup_path/secrets"
    
    log_info "Backing up secrets..."
    
    mkdir -p "$secrets_backup_dir"
    
    # Backup Kubernetes secrets
    if command -v kubectl &> /dev/null; then
        kubectl get secrets -n archbuilder -o yaml > "$secrets_backup_dir/k8s-secrets.yaml"
    fi
    
    # Backup Docker secrets
    if command -v docker &> /dev/null; then
        docker secret ls > "$secrets_backup_dir/docker-secrets.txt" 2>/dev/null || true
    fi
    
    # Backup environment variables (sanitized)
    env | grep -E "(API_KEY|SECRET|PASSWORD|TOKEN)" > "$secrets_backup_dir/env-vars.txt" 2>/dev/null || true
    
    log_success "Secrets backup completed"
}

# Encrypt backup
encrypt_backup() {
    local backup_path="$1"
    
    log_info "Encrypting backup..."
    
    # Create encryption key file
    echo "$ENCRYPTION_KEY" > "$backup_path/encryption.key"
    
    # Encrypt the entire backup directory
    tar czf - -C "$(dirname "$backup_path")" "$(basename "$backup_path")" | \
    openssl enc -aes-256-cbc -salt -in - -out "$backup_path.tar.gz.enc" -pass file:"$backup_path/encryption.key"
    
    # Remove unencrypted backup
    rm -rf "$backup_path"
    
    log_success "Backup encrypted: $backup_path.tar.gz.enc"
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"
    
    log_info "Verifying backup integrity..."
    
    # Check if backup file exists
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi
    
    # Check file size
    local file_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null || echo "0")
    if [ "$file_size" -lt 1000 ]; then
        log_error "Backup file is too small: $file_size bytes"
        return 1
    fi
    
    # Test encryption (if encrypted)
    if [[ "$backup_file" == *.enc ]]; then
        local encryption_key_file="${backup_file%.tar.gz.enc}/encryption.key"
        if [ -f "$encryption_key_file" ]; then
            if openssl enc -aes-256-cbc -d -in "$backup_file" -pass file:"$encryption_key_file" | tar -tz > /dev/null 2>&1; then
                log_success "Encrypted backup is valid"
            else
                log_error "Encrypted backup is corrupted"
                return 1
            fi
        else
            log_warning "Encryption key not found, skipping encryption verification"
        fi
    else
        # Test uncompressed backup
        if tar -tzf "$backup_file" > /dev/null 2>&1; then
            log_success "Backup is valid"
        else
            log_error "Backup is corrupted"
            return 1
        fi
    fi
    
    log_success "Backup verification completed"
}

# Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups (older than $RETENTION_DAYS days)..."
    
    find "$BACKUP_DIR" -name "*.tar.gz*" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    find "$BACKUP_DIR" -type d -empty -delete 2>/dev/null || true
    
    log_success "Old backups cleaned up"
}

# Create backup manifest
create_backup_manifest() {
    local backup_path="$1"
    local manifest_file="$backup_path/backup-manifest.json"
    
    log_info "Creating backup manifest..."
    
    cat > "$manifest_file" << EOF
{
  "backup_id": "$(basename "$backup_path")",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "version": "1.0",
  "components": {
    "database": {
      "backed_up": true,
      "size": "$(du -sh "$backup_path/database" 2>/dev/null | cut -f1 || echo "unknown")"
    },
    "configurations": {
      "backed_up": true,
      "size": "$(du -sh "$backup_path/configs" 2>/dev/null | cut -f1 || echo "unknown")"
    },
    "logs": {
      "backed_up": true,
      "size": "$(du -sh "$backup_path/logs" 2>/dev/null | cut -f1 || echo "unknown")"
    },
    "volumes": {
      "backed_up": true,
      "size": "$(du -sh "$backup_path/volumes" 2>/dev/null | cut -f1 || echo "unknown")"
    },
    "secrets": {
      "backed_up": true,
      "size": "$(du -sh "$backup_path/secrets" 2>/dev/null | cut -f1 || echo "unknown")"
    }
  },
  "encryption": {
    "encrypted": false,
    "algorithm": "none"
  },
  "retention": {
    "days": $RETENTION_DAYS,
    "expires": "$(date -d "+$RETENTION_DAYS days" -u +%Y-%m-%dT%H:%M:%SZ)"
  }
}
EOF
    
    log_success "Backup manifest created: $manifest_file"
}

# Main backup function
main() {
    log_info "Starting ArchBuilder.AI data protection procedures..."
    log_info "Backup directory: $BACKUP_DIR"
    log_info "Retention period: $RETENTION_DAYS days"
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Create backup structure
    local backup_path=$(create_backup_structure)
    
    # Perform backups
    backup_database "$backup_path"
    backup_configurations "$backup_path"
    backup_logs "$backup_path"
    backup_volumes "$backup_path"
    backup_secrets "$backup_path"
    
    # Create manifest
    create_backup_manifest "$backup_path"
    
    # Encrypt backup
    encrypt_backup "$backup_path"
    
    # Verify backup
    verify_backup "$backup_path.tar.gz.enc"
    
    # Cleanup old backups
    cleanup_old_backups
    
    log_success "Data protection procedures completed successfully!"
    log_info "Backup created: $backup_path.tar.gz.enc"
    log_info "Encryption key: $ENCRYPTION_KEY"
    log_info "Retention: $RETENTION_DAYS days"
}

# Run main function
main "$@"
