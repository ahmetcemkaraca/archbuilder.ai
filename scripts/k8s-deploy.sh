#!/bin/bash
# ArchBuilder.AI Kubernetes Deployment Script
# Automated deployment to Kubernetes cluster

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
NAMESPACE="${1:-archbuilder}"
ENVIRONMENT="${2:-production}"
VERSION="${3:-latest}"

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
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        log_error "Helm is not installed"
        exit 1
    fi
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Kubernetes cluster is not accessible"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_info "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace "$NAMESPACE"
        log_success "Namespace $NAMESPACE created"
    fi
}

# Install dependencies
install_dependencies() {
    log_info "Installing Helm dependencies..."
    
    cd "$PROJECT_ROOT/helm/archbuilder"
    
    # Add required repositories
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update
    
    # Install dependencies
    helm dependency update
    
    log_success "Dependencies installed"
}

# Deploy application
deploy_application() {
    log_info "Deploying ArchBuilder.AI to Kubernetes..."
    
    cd "$PROJECT_ROOT/helm/archbuilder"
    
    # Create values file for environment
    local values_file="values-${ENVIRONMENT}.yaml"
    if [ ! -f "$values_file" ]; then
        log_warning "Environment-specific values file not found: $values_file"
        log_info "Using default values.yaml"
        values_file="values.yaml"
    fi
    
    # Deploy with Helm
    helm upgrade --install archbuilder . \
        --namespace "$NAMESPACE" \
        --values "$values_file" \
        --set image.tag="$VERSION" \
        --set global.imageRegistry="" \
        --wait \
        --timeout=10m
    
    log_success "Application deployed successfully"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check if pods are running
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        local running_pods=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=archbuilder --field-selector=status.phase=Running --no-headers | wc -l)
        local total_pods=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=archbuilder --no-headers | wc -l)
        
        if [ "$running_pods" -eq "$total_pods" ] && [ "$total_pods" -gt 0 ]; then
            log_success "All pods are running"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Pods failed to start within timeout"
            kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=archbuilder
            exit 1
        fi
        
        log_info "Attempt $attempt/$max_attempts - waiting for pods to be ready..."
        sleep 10
        ((attempt++))
    done
    
    # Check service endpoints
    if kubectl get endpoints -n "$NAMESPACE" archbuilder &> /dev/null; then
        log_success "Service endpoints are ready"
    else
        log_warning "Service endpoints not ready"
    fi
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Check if Prometheus is running
    if kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=prometheus --field-selector=status.phase=Running --no-headers | wc -l | grep -q "0"; then
        log_warning "Prometheus is not running"
    else
        log_success "Prometheus is running"
    fi
    
    # Check if Grafana is running
    if kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=grafana --field-selector=status.phase=Running --no-headers | wc -l | grep -q "0"; then
        log_warning "Grafana is not running"
    else
        log_success "Grafana is running"
    fi
}

# Get service URLs
get_service_urls() {
    log_info "Getting service URLs..."
    
    # Get ingress URL
    local ingress_host=$(kubectl get ingress -n "$NAMESPACE" archbuilder -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "")
    if [ -n "$ingress_host" ]; then
        log_info "Application URL: https://$ingress_host"
    fi
    
    # Get port-forward commands
    log_info "Port-forward commands:"
    log_info "  kubectl port-forward -n $NAMESPACE svc/archbuilder 8000:8000"
    log_info "  kubectl port-forward -n $NAMESPACE svc/archbuilder-grafana 3000:3000"
    log_info "  kubectl port-forward -n $NAMESPACE svc/archbuilder-prometheus-server 9090:80"
}

# Cleanup function
cleanup() {
    log_error "Deployment failed. Cleaning up..."
    
    # Delete failed deployment
    helm uninstall archbuilder --namespace "$NAMESPACE" || true
    
    log_warning "Cleanup completed"
}

# Main deployment function
main() {
    log_info "Starting ArchBuilder.AI Kubernetes deployment..."
    log_info "Namespace: $NAMESPACE"
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    
    # Set up error handling
    trap cleanup ERR
    
    # Execute deployment steps
    check_prerequisites
    create_namespace
    install_dependencies
    deploy_application
    verify_deployment
    setup_monitoring
    get_service_urls
    
    log_success "Kubernetes deployment completed successfully!"
    log_info "Use 'kubectl get pods -n $NAMESPACE' to check pod status"
    log_info "Use 'kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=archbuilder' to view logs"
}

# Run main function
main "$@"
