"""
Prometheus Metrics Collection for ArchBuilder.AI

Provides:
- Custom metrics collection
- Performance monitoring
- Business metrics tracking
- System health metrics
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

from prometheus_client import Counter, Histogram, Gauge, Summary, Info, CollectorRegistry, generate_latest
import structlog

logger = structlog.get_logger(__name__)


class MetricType(str, Enum):
    """Metric type categories"""
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"
    SUMMARY = "summary"
    INFO = "info"


class ArchBuilderMetrics:
    """Prometheus metrics collector for ArchBuilder.AI"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize all metrics"""
        
        # Request metrics
        self.http_requests_total = Counter(
            'archbuilder_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.http_request_duration_seconds = Histogram(
            'archbuilder_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # AI inference metrics
        self.ai_requests_total = Counter(
            'archbuilder_ai_requests_total',
            'Total AI inference requests',
            ['model', 'provider', 'status'],
            registry=self.registry
        )
        
        self.ai_request_duration_seconds = Histogram(
            'archbuilder_ai_request_duration_seconds',
            'AI inference duration in seconds',
            ['model', 'provider'],
            registry=self.registry
        )
        
        self.ai_tokens_used_total = Counter(
            'archbuilder_ai_tokens_used_total',
            'Total AI tokens used',
            ['model', 'provider', 'token_type'],
            registry=self.registry
        )
        
        self.ai_confidence_score = Histogram(
            'archbuilder_ai_confidence_score',
            'AI response confidence scores',
            ['model', 'provider'],
            registry=self.registry
        )
        
        # Document processing metrics
        self.document_uploads_total = Counter(
            'archbuilder_document_uploads_total',
            'Total document uploads',
            ['file_type', 'status'],
            registry=self.registry
        )
        
        self.document_processing_duration_seconds = Histogram(
            'archbuilder_document_processing_duration_seconds',
            'Document processing duration in seconds',
            ['file_type', 'processing_type'],
            registry=self.registry
        )
        
        self.document_size_bytes = Histogram(
            'archbuilder_document_size_bytes',
            'Document file sizes in bytes',
            ['file_type'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_operations_total = Counter(
            'archbuilder_cache_operations_total',
            'Total cache operations',
            ['operation', 'status'],
            registry=self.registry
        )
        
        self.cache_hit_ratio = Gauge(
            'archbuilder_cache_hit_ratio',
            'Cache hit ratio',
            registry=self.registry
        )
        
        self.cache_size_bytes = Gauge(
            'archbuilder_cache_size_bytes',
            'Cache size in bytes',
            registry=self.registry
        )
        
        # Database metrics
        self.database_connections_active = Gauge(
            'archbuilder_database_connections_active',
            'Active database connections',
            registry=self.registry
        )
        
        self.database_connections_idle = Gauge(
            'archbuilder_database_connections_idle',
            'Idle database connections',
            registry=self.registry
        )
        
        self.database_query_duration_seconds = Histogram(
            'archbuilder_database_query_duration_seconds',
            'Database query duration in seconds',
            ['query_type'],
            registry=self.registry
        )
        
        self.database_queries_total = Counter(
            'archbuilder_database_queries_total',
            'Total database queries',
            ['query_type', 'status'],
            registry=self.registry
        )
        
        # Task queue metrics
        self.celery_tasks_total = Counter(
            'archbuilder_celery_tasks_total',
            'Total Celery tasks',
            ['task_name', 'status'],
            registry=self.registry
        )
        
        self.celery_task_duration_seconds = Histogram(
            'archbuilder_celery_task_duration_seconds',
            'Celery task duration in seconds',
            ['task_name'],
            registry=self.registry
        )
        
        self.celery_queue_length = Gauge(
            'archbuilder_celery_queue_length',
            'Celery queue length',
            ['queue_name'],
            registry=self.registry
        )
        
        # Business metrics
        self.user_sessions_active = Gauge(
            'archbuilder_user_sessions_active',
            'Active user sessions',
            registry=self.registry
        )
        
        self.projects_created_total = Counter(
            'archbuilder_projects_created_total',
            'Total projects created',
            ['user_tier'],
            registry=self.registry
        )
        
        self.layouts_generated_total = Counter(
            'archbuilder_layouts_generated_total',
            'Total layouts generated',
            ['building_type', 'complexity'],
            registry=self.registry
        )
        
        self.validations_performed_total = Counter(
            'archbuilder_validations_performed_total',
            'Total validations performed',
            ['validation_type', 'status'],
            registry=self.registry
        )
        
        # Security metrics
        self.security_events_total = Counter(
            'archbuilder_security_events_total',
            'Total security events',
            ['event_type', 'severity'],
            registry=self.registry
        )
        
        self.authentication_attempts_total = Counter(
            'archbuilder_authentication_attempts_total',
            'Total authentication attempts',
            ['status'],
            registry=self.registry
        )
        
        self.rate_limit_hits_total = Counter(
            'archbuilder_rate_limit_hits_total',
            'Total rate limit hits',
            ['endpoint', 'user_tier'],
            registry=self.registry
        )
        
        # System metrics
        self.system_memory_usage_bytes = Gauge(
            'archbuilder_system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )
        
        self.system_cpu_usage_percent = Gauge(
            'archbuilder_system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.application_info = Info(
            'archbuilder_application_info',
            'Application information',
            registry=self.registry
        )
        
        # Set application info
        self.application_info.info({
            'version': '1.0.0',
            'environment': 'production',
            'build_date': datetime.utcnow().isoformat()
        })
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_ai_request(self, model: str, provider: str, status: str, duration: float, 
                         tokens_used: int = 0, confidence: float = 0.0):
        """Record AI inference metrics"""
        self.ai_requests_total.labels(
            model=model,
            provider=provider,
            status=status
        ).inc()
        
        self.ai_request_duration_seconds.labels(
            model=model,
            provider=provider
        ).observe(duration)
        
        if tokens_used > 0:
            self.ai_tokens_used_total.labels(
                model=model,
                provider=provider,
                token_type='total'
            ).inc(tokens_used)
        
        if confidence > 0:
            self.ai_confidence_score.labels(
                model=model,
                provider=provider
            ).observe(confidence)
    
    def record_document_upload(self, file_type: str, status: str, file_size: int, duration: float):
        """Record document upload metrics"""
        self.document_uploads_total.labels(
            file_type=file_type,
            status=status
        ).inc()
        
        self.document_size_bytes.labels(
            file_type=file_type
        ).observe(file_size)
        
        self.document_processing_duration_seconds.labels(
            file_type=file_type,
            processing_type='upload'
        ).observe(duration)
    
    def record_cache_operation(self, operation: str, status: str):
        """Record cache operation metrics"""
        self.cache_operations_total.labels(
            operation=operation,
            status=status
        ).inc()
    
    def update_cache_metrics(self, hit_ratio: float, size_bytes: int):
        """Update cache metrics"""
        self.cache_hit_ratio.set(hit_ratio)
        self.cache_size_bytes.set(size_bytes)
    
    def record_database_query(self, query_type: str, status: str, duration: float):
        """Record database query metrics"""
        self.database_queries_total.labels(
            query_type=query_type,
            status=status
        ).inc()
        
        self.database_query_duration_seconds.labels(
            query_type=query_type
        ).observe(duration)
    
    def update_database_connections(self, active: int, idle: int):
        """Update database connection metrics"""
        self.database_connections_active.set(active)
        self.database_connections_idle.set(idle)
    
    def record_celery_task(self, task_name: str, status: str, duration: float):
        """Record Celery task metrics"""
        self.celery_tasks_total.labels(
            task_name=task_name,
            status=status
        ).inc()
        
        self.celery_task_duration_seconds.labels(
            task_name=task_name
        ).observe(duration)
    
    def update_celery_queue_length(self, queue_name: str, length: int):
        """Update Celery queue length"""
        self.celery_queue_length.labels(queue_name=queue_name).set(length)
    
    def record_business_metric(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Record business metric"""
        labels = labels or {}
        
        if metric_name == 'user_sessions_active':
            self.user_sessions_active.set(value)
        elif metric_name == 'projects_created':
            self.projects_created_total.labels(**labels).inc(value)
        elif metric_name == 'layouts_generated':
            self.layouts_generated_total.labels(**labels).inc(value)
        elif metric_name == 'validations_performed':
            self.validations_performed_total.labels(**labels).inc(value)
    
    def record_security_event(self, event_type: str, severity: str):
        """Record security event"""
        self.security_events_total.labels(
            event_type=event_type,
            severity=severity
        ).inc()
    
    def record_authentication_attempt(self, status: str):
        """Record authentication attempt"""
        self.authentication_attempts_total.labels(status=status).inc()
    
    def record_rate_limit_hit(self, endpoint: str, user_tier: str):
        """Record rate limit hit"""
        self.rate_limit_hits_total.labels(
            endpoint=endpoint,
            user_tier=user_tier
        ).inc()
    
    def update_system_metrics(self, memory_usage: int, cpu_usage: float):
        """Update system metrics"""
        self.system_memory_usage_bytes.set(memory_usage)
        self.system_cpu_usage_percent.set(cpu_usage)
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        return generate_latest(self.registry)


class MetricsCollector:
    """Metrics collection service for ArchBuilder.AI"""
    
    def __init__(self):
        self.metrics = ArchBuilderMetrics()
        self._start_time = time.time()
    
    async def collect_system_metrics(self):
        """Collect system metrics"""
        try:
            import psutil
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.used
            
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            self.metrics.update_system_metrics(memory_usage, cpu_usage)
            
        except ImportError:
            logger.warning("psutil not available, skipping system metrics")
        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))
    
    async def collect_cache_metrics(self):
        """Collect cache metrics"""
        try:
            from app.core.cache import get_cache_service
            
            cache_service = await get_cache_service()
            stats = await cache_service.cache_manager.get_stats()
            
            if stats:
                # Calculate hit ratio
                hits = stats.get('keyspace_hits', 0)
                misses = stats.get('keyspace_misses', 0)
                total = hits + misses
                hit_ratio = hits / total if total > 0 else 0.0
                
                # Cache size
                cache_size = stats.get('used_memory', 0)
                
                self.metrics.update_cache_metrics(hit_ratio, cache_size)
                
        except Exception as e:
            logger.error("Failed to collect cache metrics", error=str(e))
    
    async def collect_database_metrics(self):
        """Collect database metrics"""
        try:
            from app.core.connection_pool import get_pool_manager
            
            pool_manager = get_pool_manager()
            pool_metrics = pool_manager.get_pool_metrics()
            
            if pool_metrics:
                self.metrics.update_database_connections(
                    pool_metrics.checked_out,
                    pool_metrics.checked_in
                )
                
        except Exception as e:
            logger.error("Failed to collect database metrics", error=str(e))
    
    async def collect_celery_metrics(self):
        """Collect Celery metrics"""
        try:
            from app.core.celery_app import get_task_queue_manager
            
            task_manager = get_task_queue_manager()
            queue_stats = await task_manager.get_queue_stats()
            
            if queue_stats:
                for queue_name, queue_data in queue_stats.get('queues', {}).items():
                    total_tasks = (
                        queue_data.get('active', 0) + 
                        queue_data.get('scheduled', 0) + 
                        queue_data.get('reserved', 0)
                    )
                    self.metrics.update_celery_queue_length(queue_name, total_tasks)
                    
        except Exception as e:
            logger.error("Failed to collect Celery metrics", error=str(e))
    
    async def collect_all_metrics(self):
        """Collect all metrics"""
        await asyncio.gather(
            self.collect_system_metrics(),
            self.collect_cache_metrics(),
            self.collect_database_metrics(),
            self.collect_celery_metrics(),
            return_exceptions=True
        )
    
    def get_metrics_output(self) -> str:
        """Get metrics output"""
        return self.metrics.get_metrics()


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def initialize_metrics() -> MetricsCollector:
    """Initialize global metrics collector"""
    global _metrics_collector
    
    _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
    if _metrics_collector is None:
        raise RuntimeError("Metrics collector not initialized")
    return _metrics_collector
