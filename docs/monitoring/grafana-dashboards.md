# Grafana Dashboards for ArchBuilder.AI
# Grafana dashboards - P45-T2

## Overview

This document describes the Grafana dashboard configurations for monitoring ArchBuilder.AI system performance, security, and business metrics.

## Dashboard Categories

### 1. System Performance Dashboard

**Purpose**: Monitor system performance metrics and resource utilization

**Key Metrics**:
- CPU Usage
- Memory Usage
- Disk I/O
- Network I/O
- Response Times
- Throughput

**Dashboard Configuration**:

```json
{
  "dashboard": {
    "title": "ArchBuilder.AI - System Performance",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(cpu_usage_total[5m])",
            "legendFormat": "CPU Usage %"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "memory_usage_bytes",
            "legendFormat": "Memory Usage"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### 2. AI Operations Dashboard

**Purpose**: Monitor AI model performance and usage

**Key Metrics**:
- AI Request Rate
- AI Response Time
- AI Error Rate
- Model Usage Distribution
- Token Usage
- Cost Tracking

**Dashboard Configuration**:

```json
{
  "dashboard": {
    "title": "ArchBuilder.AI - AI Operations",
    "panels": [
      {
        "title": "AI Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ai_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "AI Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(ai_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "AI Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ai_requests_failed_total[5m]) / rate(ai_requests_total[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      },
      {
        "title": "Model Usage Distribution",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (model) (ai_requests_total)",
            "legendFormat": "{{model}}"
          }
        ]
      }
    ]
  }
}
```

### 3. Security Dashboard

**Purpose**: Monitor security events and threats

**Key Metrics**:
- Failed Login Attempts
- Suspicious Activity
- File Upload Security
- API Abuse
- Rate Limiting

**Dashboard Configuration**:

```json
{
  "dashboard": {
    "title": "ArchBuilder.AI - Security",
    "panels": [
      {
        "title": "Failed Login Attempts",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(auth_failed_total[5m])",
            "legendFormat": "Failed Logins/sec"
          }
        ]
      },
      {
        "title": "Suspicious Activity",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(security_violations_total[5m])",
            "legendFormat": "Security Violations/sec"
          }
        ]
      },
      {
        "title": "File Upload Security",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(file_abuse_detected_total[5m])",
            "legendFormat": "Abuse Detected/sec"
          }
        ]
      }
    ]
  }
}
```

### 4. Business Metrics Dashboard

**Purpose**: Monitor business KPIs and user engagement

**Key Metrics**:
- Active Users
- Subscription Metrics
- Revenue Tracking
- Feature Usage
- User Satisfaction

**Dashboard Configuration**:

```json
{
  "dashboard": {
    "title": "ArchBuilder.AI - Business Metrics",
    "panels": [
      {
        "title": "Active Users",
        "type": "graph",
        "targets": [
          {
            "expr": "active_users_total",
            "legendFormat": "Active Users"
          }
        ]
      },
      {
        "title": "Subscription Metrics",
        "type": "graph",
        "targets": [
          {
            "expr": "subscriptions_total",
            "legendFormat": "Total Subscriptions"
          }
        ]
      },
      {
        "title": "Revenue Tracking",
        "type": "graph",
        "targets": [
          {
            "expr": "revenue_total",
            "legendFormat": "Revenue"
          }
        ]
      }
    ]
  }
}
```

### 5. RAG System Dashboard

**Purpose**: Monitor RAG (Retrieval-Augmented Generation) system performance

**Key Metrics**:
- Document Processing Rate
- Vector Search Performance
- Embedding Generation
- RAG Response Quality
- Knowledge Base Size

**Dashboard Configuration**:

```json
{
  "dashboard": {
    "title": "ArchBuilder.AI - RAG System",
    "panels": [
      {
        "title": "Document Processing Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(documents_processed_total[5m])",
            "legendFormat": "Documents/sec"
          }
        ]
      },
      {
        "title": "Vector Search Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(vector_search_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "RAG Response Quality",
        "type": "graph",
        "targets": [
          {
            "expr": "avg(rag_response_quality_score)",
            "legendFormat": "Quality Score"
          }
        ]
      }
    ]
  }
}
```

## Alert Rules

### Critical Alerts

```yaml
groups:
  - name: archbuilder.critical
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_failed_total[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}%"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      - alert: AIModelDown
        expr: up{job="ai-model"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "AI model is down"
          description: "AI model service is not responding"
```

### Warning Alerts

```yaml
groups:
  - name: archbuilder.warning
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}%"

      - alert: HighMemoryUsage
        expr: memory_usage_percent > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}%"

      - alert: DiskSpaceLow
        expr: disk_free_percent < 20
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space"
          description: "Disk space is {{ $value }}% free"
```

## Dashboard Setup Instructions

### 1. Install Grafana

```bash
# Using Docker
docker run -d --name grafana -p 3000:3000 grafana/grafana:latest

# Using Helm
helm install grafana grafana/grafana
```

### 2. Configure Data Sources

```yaml
# prometheus-datasource.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-datasource
data:
  datasource.yaml: |
    apiVersion: 1
    datasources:
      - name: Prometheus
        type: prometheus
        url: http://prometheus:9090
        access: proxy
        isDefault: true
```

### 3. Import Dashboards

```bash
# Import system performance dashboard
curl -X POST \
  http://admin:admin@localhost:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @system-performance-dashboard.json

# Import AI operations dashboard
curl -X POST \
  http://admin:admin@localhost:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @ai-operations-dashboard.json
```

### 4. Configure Alerting

```yaml
# alertmanager-config.yaml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@archbuilder.ai'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:5001/webhook'
```

## Custom Metrics

### Python Application Metrics

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Request metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# AI metrics
AI_REQUESTS = Counter('ai_requests_total', 'Total AI requests', ['model', 'status'])
AI_DURATION = Histogram('ai_request_duration_seconds', 'AI request duration')

# Business metrics
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')
SUBSCRIPTIONS = Gauge('subscriptions_total', 'Total subscriptions', ['tier'])
```

### C# Application Metrics

```csharp
using Prometheus;

// Request metrics
private static readonly Counter RequestCount = Metrics
    .CreateCounter("http_requests_total", "Total HTTP requests", new[] { "method", "endpoint", "status" });

private static readonly Histogram RequestDuration = Metrics
    .CreateHistogram("http_request_duration_seconds", "HTTP request duration");

// AI metrics
private static readonly Counter AIRequests = Metrics
    .CreateCounter("ai_requests_total", "Total AI requests", new[] { "model", "status" });
```

## Dashboard Maintenance

### Regular Tasks

1. **Review Dashboard Performance**
   - Check dashboard load times
   - Optimize queries
   - Remove unused panels

2. **Update Alert Thresholds**
   - Review alert effectiveness
   - Adjust thresholds based on historical data
   - Add new alerts for emerging issues

3. **Dashboard Versioning**
   - Export dashboard configurations
   - Version control dashboard changes
   - Document dashboard modifications

### Best Practices

1. **Dashboard Design**
   - Use consistent color schemes
   - Group related metrics
   - Provide context and explanations

2. **Performance Optimization**
   - Use appropriate time ranges
   - Limit data points per query
   - Cache frequently accessed data

3. **Security**
   - Restrict dashboard access
   - Use authentication
   - Audit dashboard usage

## Troubleshooting

### Common Issues

1. **Dashboard Not Loading**
   - Check data source connectivity
   - Verify query syntax
   - Check time range settings

2. **Missing Metrics**
   - Verify metric collection
   - Check Prometheus configuration
   - Review application instrumentation

3. **Performance Issues**
   - Optimize queries
   - Reduce time range
   - Use data sampling

### Support Resources

- Grafana Documentation: https://grafana.com/docs/
- Prometheus Documentation: https://prometheus.io/docs/
- ArchBuilder.AI Monitoring Guide: [Internal Documentation]
