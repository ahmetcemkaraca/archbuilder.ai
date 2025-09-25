#!/bin/bash
# ArchBuilder.AI Blue-Green Deployment Script
# Zero-downtime deployment strategy

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
NAMESPACE="${1:-archbuilder}"
VERSION="${2:-latest}"
DEPLOYMENT_STRATEGY="${3:-blue-green}"  # blue-green or canary

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

# Get current active deployment
get_current_deployment() {
    local current=$(kubectl get service -n "$NAMESPACE" archbuilder -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "blue")
    echo "$current"
}

# Get inactive deployment
get_inactive_deployment() {
    local current=$(get_current_deployment)
    if [ "$current" = "blue" ]; then
        echo "green"
    else
        echo "blue"
    fi
}

# Deploy new version to inactive environment
deploy_to_inactive() {
    local target_env=$(get_inactive_deployment)
    log_info "Deploying version $VERSION to $target_env environment..."
    
    cd "$PROJECT_ROOT/helm/archbuilder"
    
    # Deploy to inactive environment
    helm upgrade --install "archbuilder-$target_env" . \
        --namespace "$NAMESPACE" \
        --values "values-$target_env.yaml" \
        --set image.tag="$VERSION" \
        --set service.name="archbuilder-$target_env" \
        --set ingress.hosts[0].host="$target_env-api.archbuilder.app" \
        --wait \
        --timeout=10m
    
    log_success "Deployed to $target_env environment"
}

# Run health checks on new deployment
run_health_checks() {
    local target_env=$(get_inactive_deployment)
    local service_name="archbuilder-$target_env"
    
    log_info "Running health checks on $target_env environment..."
    
    # Port forward to new service
    kubectl port-forward -n "$NAMESPACE" "svc/$service_name" 8080:8000 &
    local port_forward_pid=$!
    
    # Wait for port forward to be ready
    sleep 10
    
    # Run health checks
    local max_attempts=30
    local attempt=1
    local health_checks_passed=0
    
    while [ $attempt -le $max_attempts ]; do
        # Basic health check
        if curl -f http://localhost:8080/health &> /dev/null; then
            ((health_checks_passed++))
        fi
        
        # API endpoint check
        if curl -f http://localhost:8080/v1/users &> /dev/null; then
            ((health_checks_passed++))
        fi
        
        # Database connectivity check
        if curl -f http://localhost:8080/v1/health/database &> /dev/null; then
            ((health_checks_passed++))
        fi
        
        if [ $health_checks_passed -ge 2 ]; then
            log_success "Health checks passed for $target_env environment"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Health checks failed for $target_env environment"
            kill $port_forward_pid 2>/dev/null || true
            return 1
        fi
        
        log_info "Attempt $attempt/$max_attempts - running health checks..."
        sleep 10
        ((attempt++))
    done
    
    # Clean up port forward
    kill $port_forward_pid 2>/dev/null || true
    
    return 0
}

# Run smoke tests
run_smoke_tests() {
    local target_env=$(get_inactive_deployment)
    local service_name="archbuilder-$target_env"
    
    log_info "Running smoke tests on $target_env environment..."
    
    # Port forward to new service
    kubectl port-forward -n "$NAMESPACE" "svc/$service_name" 8080:8000 &
    local port_forward_pid=$!
    
    # Wait for port forward to be ready
    sleep 10
    
    # Run smoke tests
    local smoke_tests_passed=0
    local total_tests=5
    
    # Test 1: Health endpoint
    if curl -f http://localhost:8080/health &> /dev/null; then
        log_success "✓ Health endpoint test passed"
        ((smoke_tests_passed++))
    else
        log_warning "✗ Health endpoint test failed"
    fi
    
    # Test 2: API endpoints
    if curl -f http://localhost:8080/v1/users &> /dev/null; then
        log_success "✓ Users API test passed"
        ((smoke_tests_passed++))
    else
        log_warning "✗ Users API test failed"
    fi
    
    # Test 3: Projects API
    if curl -f http://localhost:8080/v1/projects &> /dev/null; then
        log_success "✓ Projects API test passed"
        ((smoke_tests_passed++))
    else
        log_warning "✗ Projects API test failed"
    fi
    
    # Test 4: AI Commands API
    if curl -f http://localhost:8080/v1/ai/commands &> /dev/null; then
        log_success "✓ AI Commands API test passed"
        ((smoke_tests_passed++))
    else
        log_warning "✗ AI Commands API test failed"
    fi
    
    # Test 5: WebSocket endpoint
    if curl -f http://localhost:8080/v1/ws/status &> /dev/null; then
        log_success "✓ WebSocket endpoint test passed"
        ((smoke_tests_passed++))
    else
        log_warning "✗ WebSocket endpoint test failed"
    fi
    
    # Clean up port forward
    kill $port_forward_pid 2>/dev/null || true
    
    log_info "Smoke tests completed: $smoke_tests_passed/$total_tests passed"
    
    if [ $smoke_tests_passed -ge 3 ]; then
        log_success "Smoke tests passed"
        return 0
    else
        log_error "Smoke tests failed"
        return 1
    fi
}

# Switch traffic to new deployment
switch_traffic() {
    local target_env=$(get_inactive_deployment)
    log_info "Switching traffic to $target_env environment..."
    
    # Update service selector to point to new deployment
    kubectl patch service -n "$NAMESPACE" archbuilder -p "{\"spec\":{\"selector\":{\"version\":\"$target_env\"}}}"
    
    # Update ingress to point to new service
    kubectl patch ingress -n "$NAMESPACE" archbuilder -p "{\"spec\":{\"rules\":[{\"host\":\"api.archbuilder.app\",\"http\":{\"paths\":[{\"path\":\"/\",\"backend\":{\"service\":{\"name\":\"archbuilder-$target_env\",\"port\":{\"number\":8000}}}}]}}]}}"
    
    log_success "Traffic switched to $target_env environment"
}

# Run canary deployment
run_canary_deployment() {
    log_info "Running canary deployment strategy..."
    
    local canary_percentages=(10 25 50 75 100)
    
    for percentage in "${canary_percentages[@]}"; do
        log_info "Deploying canary at $percentage% traffic..."
        
        # Update Istio VirtualService for canary traffic splitting
        kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: archbuilder-canary
  namespace: $NAMESPACE
spec:
  hosts:
  - api.archbuilder.app
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: archbuilder-green
        port:
          number: 8000
  - route:
    - destination:
        host: archbuilder-blue
        port:
          number: 8000
      weight: $((100 - percentage))
    - destination:
        host: archbuilder-green
        port:
          number: 8000
      weight: $percentage
EOF
        
        # Wait for traffic to stabilize
        sleep 60
        
        # Run health checks
        if ! run_health_checks; then
            log_error "Canary deployment failed at $percentage%"
            return 1
        fi
        
        # Run smoke tests
        if ! run_smoke_tests; then
            log_error "Canary smoke tests failed at $percentage%"
            return 1
        fi
        
        log_success "Canary deployment successful at $percentage%"
    done
    
    log_success "Canary deployment completed successfully"
}

# Cleanup old deployment
cleanup_old_deployment() {
    local old_env=$(get_inactive_deployment)
    log_info "Cleaning up old $old_env deployment..."
    
    # Scale down old deployment
    kubectl scale deployment -n "$NAMESPACE" "archbuilder-$old_env" --replicas=0
    
    # Wait for pods to terminate
    kubectl wait --for=delete pod -n "$NAMESPACE" -l app.kubernetes.io/name=archbuilder,version=$old_env --timeout=300s
    
    log_success "Old $old_env deployment cleaned up"
}

# Rollback deployment
rollback_deployment() {
    local current_env=$(get_current_deployment)
    local target_env=$(get_inactive_deployment)
    
    log_error "Rolling back deployment..."
    
    # Switch traffic back to previous environment
    kubectl patch service -n "$NAMESPACE" archbuilder -p "{\"spec\":{\"selector\":{\"version\":\"$target_env\"}}}"
    
    # Update ingress back to previous service
    kubectl patch ingress -n "$NAMESPACE" archbuilder -p "{\"spec\":{\"rules\":[{\"host\":\"api.archbuilder.app\",\"http\":{\"paths\":[{\"path\":\"/\",\"backend\":{\"service\":{\"name\":\"archbuilder-$target_env\",\"port\":{\"number\":8000}}}}]}}]}}"
    
    # Scale down failed deployment
    kubectl scale deployment -n "$NAMESPACE" "archbuilder-$current_env" --replicas=0
    
    log_success "Rollback completed"
}

# Main deployment function
main() {
    log_info "Starting ArchBuilder.AI $DEPLOYMENT_STRATEGY deployment..."
    log_info "Namespace: $NAMESPACE"
    log_info "Version: $VERSION"
    log_info "Strategy: $DEPLOYMENT_STRATEGY"
    
    # Set up error handling
    trap rollback_deployment ERR
    
    # Get current deployment state
    local current_env=$(get_current_deployment)
    local target_env=$(get_inactive_deployment)
    
    log_info "Current active environment: $current_env"
    log_info "Target environment: $target_env"
    
    # Deploy to inactive environment
    deploy_to_inactive
    
    # Run health checks
    if ! run_health_checks; then
        log_error "Health checks failed"
        exit 1
    fi
    
    # Run smoke tests
    if ! run_smoke_tests; then
        log_error "Smoke tests failed"
        exit 1
    fi
    
    # Deploy based on strategy
    if [ "$DEPLOYMENT_STRATEGY" = "canary" ]; then
        run_canary_deployment
    else
        # Blue-green deployment
        switch_traffic
        
        # Wait for traffic to stabilize
        sleep 30
        
        # Verify new deployment is working
        if ! run_health_checks; then
            log_error "Post-switch health checks failed"
            exit 1
        fi
    fi
    
    # Cleanup old deployment
    cleanup_old_deployment
    
    log_success "$DEPLOYMENT_STRATEGY deployment completed successfully!"
    log_info "Active environment: $target_env"
    log_info "Application URL: https://api.archbuilder.app"
}

# Run main function
main "$@"
