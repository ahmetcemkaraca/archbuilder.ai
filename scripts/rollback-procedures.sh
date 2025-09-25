#!/bin/bash
# ArchBuilder.AI Rollback Procedures
# Comprehensive rollback strategies for different scenarios

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
NAMESPACE="${1:-archbuilder}"
ROLLBACK_TYPE="${2:-quick}"  # quick, full, data, or emergency
BACKUP_VERSION="${3:-latest}"

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

# Get current deployment status
get_deployment_status() {
    log_info "Checking current deployment status..."
    
    # Get current active deployment
    local current_env=$(kubectl get service -n "$NAMESPACE" archbuilder -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "blue")
    local target_env=$(if [ "$current_env" = "blue" ]; then echo "green"; else echo "blue"; fi)
    
    echo "CURRENT_ENV=$current_env"
    echo "TARGET_ENV=$target_env"
}

# Quick rollback (traffic switch only)
quick_rollback() {
    log_info "Performing quick rollback (traffic switch only)..."
    
    local current_env=$(kubectl get service -n "$NAMESPACE" archbuilder -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "blue")
    local target_env=$(if [ "$current_env" = "blue" ]; then echo "green"; else echo "blue"; fi)
    
    log_info "Switching traffic from $current_env to $target_env..."
    
    # Switch service selector
    kubectl patch service -n "$NAMESPACE" archbuilder -p "{\"spec\":{\"selector\":{\"version\":\"$target_env\"}}}"
    
    # Switch ingress
    kubectl patch ingress -n "$NAMESPACE" archbuilder -p "{\"spec\":{\"rules\":[{\"host\":\"api.archbuilder.app\",\"http\":{\"paths\":[{\"path\":\"/\",\"backend\":{\"service\":{\"name\":\"archbuilder-$target_env\",\"port\":{\"number\":8000}}}}]}}]}}"
    
    # Wait for traffic to switch
    sleep 30
    
    # Verify rollback
    if curl -f https://api.archbuilder.app/health &> /dev/null; then
        log_success "Quick rollback completed successfully"
    else
        log_error "Quick rollback verification failed"
        return 1
    fi
}

# Full rollback (deployment + traffic)
full_rollback() {
    log_info "Performing full rollback..."
    
    local current_env=$(kubectl get service -n "$NAMESPACE" archbuilder -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "blue")
    local target_env=$(if [ "$current_env" = "blue" ]; then echo "green"; else echo "blue"; fi)
    
    # Switch traffic first
    quick_rollback
    
    # Scale down failed deployment
    log_info "Scaling down failed $current_env deployment..."
    kubectl scale deployment -n "$NAMESPACE" "archbuilder-$current_env" --replicas=0
    
    # Wait for pods to terminate
    kubectl wait --for=delete pod -n "$NAMESPACE" -l app.kubernetes.io/name=archbuilder,version=$current_env --timeout=300s
    
    log_success "Full rollback completed"
}

# Data rollback (database + application)
data_rollback() {
    log_info "Performing data rollback..."
    
    # Check if backup exists
    local backup_dir="$PROJECT_ROOT/backups/$BACKUP_VERSION"
    if [ ! -d "$backup_dir" ]; then
        log_error "Backup directory not found: $backup_dir"
        return 1
    fi
    
    # Stop application services
    log_info "Stopping application services..."
    kubectl scale deployment -n "$NAMESPACE" archbuilder-blue --replicas=0
    kubectl scale deployment -n "$NAMESPACE" archbuilder-green --replicas=0
    
    # Restore database
    if [ -f "$backup_dir/database.sql" ]; then
        log_info "Restoring database from backup..."
        
        # Port forward to PostgreSQL
        kubectl port-forward -n "$NAMESPACE" svc/postgresql 5432:5432 &
        local port_forward_pid=$!
        sleep 10
        
        # Restore database
        if kubectl exec -n "$NAMESPACE" -it deployment/postgresql -- psql -U archbuilder -d archbuilder < "$backup_dir/database.sql"; then
            log_success "Database restored successfully"
        else
            log_error "Database restore failed"
            kill $port_forward_pid 2>/dev/null || true
            return 1
        fi
        
        kill $port_forward_pid 2>/dev/null || true
    else
        log_warning "Database backup not found, skipping database restore"
    fi
    
    # Restore configuration
    if [ -d "$backup_dir/configs" ]; then
        log_info "Restoring configuration from backup..."
        cp -r "$backup_dir/configs" "$PROJECT_ROOT/"
        log_success "Configuration restored"
    fi
    
    # Restart application services
    log_info "Restarting application services..."
    kubectl scale deployment -n "$NAMESPACE" archbuilder-blue --replicas=2
    kubectl scale deployment -n "$NAMESPACE" archbuilder-green --replicas=2
    
    # Wait for services to be ready
    kubectl wait --for=condition=available deployment -n "$NAMESPACE" archbuilder-blue --timeout=300s
    kubectl wait --for=condition=available deployment -n "$NAMESPACE" archbuilder-green --timeout=300s
    
    log_success "Data rollback completed"
}

# Emergency rollback (immediate traffic cut)
emergency_rollback() {
    log_info "Performing emergency rollback..."
    
    # Immediately switch to blue environment (assumed stable)
    log_info "Switching to blue environment immediately..."
    kubectl patch service -n "$NAMESPACE" archbuilder -p "{\"spec\":{\"selector\":{\"version\":\"blue\"}}}"
    kubectl patch ingress -n "$NAMESPACE" archbuilder -p "{\"spec\":{\"rules\":[{\"host\":\"api.archbuilder.app\",\"http\":{\"paths\":[{\"path\":\"/\",\"backend\":{\"service\":{\"name\":\"archbuilder-blue\",\"port\":{\"number\":8000}}}}]}}]}}"
    
    # Scale down green environment
    kubectl scale deployment -n "$NAMESPACE" archbuilder-green --replicas=0
    
    # Verify blue environment is working
    sleep 30
    if curl -f https://api.archbuilder.app/health &> /dev/null; then
        log_success "Emergency rollback completed - blue environment is active"
    else
        log_error "Emergency rollback failed - blue environment is not responding"
        return 1
    fi
}

# Rollback verification
verify_rollback() {
    log_info "Verifying rollback..."
    
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        # Test health endpoint
        if curl -f https://api.archbuilder.app/health &> /dev/null; then
            log_success "✓ Health endpoint is responding"
        else
            log_warning "✗ Health endpoint is not responding"
        fi
        
        # Test API endpoints
        if curl -f https://api.archbuilder.app/v1/users &> /dev/null; then
            log_success "✓ API endpoints are responding"
        else
            log_warning "✗ API endpoints are not responding"
        fi
        
        # Test database connectivity
        if curl -f https://api.archbuilder.app/v1/health/database &> /dev/null; then
            log_success "✓ Database connectivity is working"
        else
            log_warning "✗ Database connectivity is not working"
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Rollback verification failed after $max_attempts attempts"
            return 1
        fi
        
        log_info "Attempt $attempt/$max_attempts - verifying rollback..."
        sleep 10
        ((attempt++))
    done
    
    log_success "Rollback verification completed successfully"
}

# Create rollback report
create_rollback_report() {
    local report_file="$PROJECT_ROOT/rollback-report-$(date +%Y%m%d_%H%M%S).txt"
    
    log_info "Creating rollback report: $report_file"
    
    cat > "$report_file" << EOF
ArchBuilder.AI Rollback Report
=============================
Date: $(date)
Rollback Type: $ROLLBACK_TYPE
Namespace: $NAMESPACE
Backup Version: $BACKUP_VERSION

Current Deployment Status:
$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=archbuilder)

Service Status:
$(kubectl get services -n "$NAMESPACE" archbuilder)

Ingress Status:
$(kubectl get ingress -n "$NAMESPACE" archbuilder)

Deployment History:
$(kubectl rollout history deployment -n "$NAMESPACE" archbuilder-blue)
$(kubectl rollout history deployment -n "$NAMESPACE" archbuilder-green)

Recent Events:
$(kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -20)

Rollback Actions Taken:
- Traffic switched to stable environment
- Failed deployment scaled down
- Health checks performed
- Verification completed

Next Steps:
1. Monitor application health
2. Investigate root cause of failure
3. Plan next deployment
4. Update documentation
EOF
    
    log_success "Rollback report created: $report_file"
}

# Main rollback function
main() {
    log_info "Starting ArchBuilder.AI rollback procedures..."
    log_info "Rollback Type: $ROLLBACK_TYPE"
    log_info "Namespace: $NAMESPACE"
    log_info "Backup Version: $BACKUP_VERSION"
    
    # Get current status
    get_deployment_status
    
    # Perform rollback based on type
    case "$ROLLBACK_TYPE" in
        "quick")
            quick_rollback
            ;;
        "full")
            full_rollback
            ;;
        "data")
            data_rollback
            ;;
        "emergency")
            emergency_rollback
            ;;
        *)
            log_error "Invalid rollback type: $ROLLBACK_TYPE"
            log_info "Valid types: quick, full, data, emergency"
            exit 1
            ;;
    esac
    
    # Verify rollback
    verify_rollback
    
    # Create report
    create_rollback_report
    
    log_success "Rollback procedures completed successfully!"
    log_info "Application is now running on stable environment"
    log_info "Monitor the application and investigate the root cause"
}

# Run main function
main "$@"
