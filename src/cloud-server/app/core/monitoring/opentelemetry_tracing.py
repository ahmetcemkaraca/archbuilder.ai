"""
OpenTelemetry Tracing for ArchBuilder.AI
OpenTelemetry tracing - P46-T1
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import structlog
from contextlib import asynccontextmanager
from functools import wraps

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage import get_all_baggage, set_baggage

logger = structlog.get_logger(__name__)


@dataclass
class TraceConfig:
    """OpenTelemetry configuration"""
    service_name: str = "archbuilder-ai"
    service_version: str = "1.0.0"
    environment: str = "production"
    jaeger_endpoint: str = "http://localhost:14268/api/traces"
    otlp_endpoint: str = "http://localhost:4317"
    sampling_rate: float = 1.0
    enable_auto_instrumentation: bool = True


class ArchBuilderTracer:
    """OpenTelemetry tracer for ArchBuilder.AI"""
    
    def __init__(self, config: TraceConfig):
        self.config = config
        self.tracer = None
        self._setup_tracer()
    
    def _setup_tracer(self):
        """Setup OpenTelemetry tracer"""
        # Create resource
        resource = Resource.create({
            "service.name": self.config.service_name,
            "service.version": self.config.service_version,
            "deployment.environment": self.config.environment,
        })
        
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        
        # Create exporters
        jaeger_exporter = JaegerExporter(
            agent_host_name="localhost",
            agent_port=14268,
        )
        
        otlp_exporter = OTLPSpanExporter(
            endpoint=self.config.otlp_endpoint,
        )
        
        # Add span processors
        tracer_provider.add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )
        tracer_provider.add_span_processor(
            BatchSpanProcessor(otlp_exporter)
        )
        
        # Get tracer
        self.tracer = trace.get_tracer(__name__)
        
        logger.info("OpenTelemetry tracer configured", service_name=self.config.service_name)
    
    def get_tracer(self):
        """Get the configured tracer"""
        return self.tracer
    
    def trace_function(self, operation_name: str = None, attributes: Dict[str, Any] = None):
        """Decorator to trace function execution"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                span_name = operation_name or f"{func.__module__}.{func.__name__}"
                
                with self.tracer.start_as_current_span(span_name) as span:
                    # Add attributes
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                    
                    # Add function arguments as attributes
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    try:
                        start_time = time.time()
                        result = await func(*args, **kwargs)
                        end_time = time.time()
                        
                        # Add timing information
                        span.set_attribute("duration_ms", (end_time - start_time) * 1000)
                        span.set_status(Status(StatusCode.OK))
                        
                        return result
                        
                    except Exception as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.set_attribute("error", True)
                        span.set_attribute("error.message", str(e))
                        span.set_attribute("error.type", type(e).__name__)
                        raise
                    
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                span_name = operation_name or f"{func.__module__}.{func.__name__}"
                
                with self.tracer.start_as_current_span(span_name) as span:
                    # Add attributes
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                    
                    # Add function arguments as attributes
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    try:
                        start_time = time.time()
                        result = func(*args, **kwargs)
                        end_time = time.time()
                        
                        # Add timing information
                        span.set_attribute("duration_ms", (end_time - start_time) * 1000)
                        span.set_status(Status(StatusCode.OK))
                        
                        return result
                        
                    except Exception as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.set_attribute("error", True)
                        span.set_attribute("error.message", str(e))
                        span.set_attribute("error.type", type(e).__name__)
                        raise
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    @asynccontextmanager
    async def trace_async_operation(self, operation_name: str, attributes: Dict[str, Any] = None):
        """Context manager for tracing async operations"""
        with self.tracer.start_as_current_span(operation_name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                span.set_attribute("error.type", type(e).__name__)
                raise
    
    def trace_ai_operation(self, model: str, operation: str, user_id: str = None):
        """Trace AI operations with specific attributes"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                span_name = f"ai.{operation}"
                
                with self.tracer.start_as_current_span(span_name) as span:
                    # AI-specific attributes
                    span.set_attribute("ai.model", model)
                    span.set_attribute("ai.operation", operation)
                    span.set_attribute("ai.user_id", user_id or "anonymous")
                    
                    # Add request context
                    if "prompt" in kwargs:
                        span.set_attribute("ai.prompt_length", len(str(kwargs["prompt"])))
                    
                    if "correlation_id" in kwargs:
                        span.set_attribute("correlation.id", kwargs["correlation_id"])
                    
                    try:
                        start_time = time.time()
                        result = await func(*args, **kwargs)
                        end_time = time.time()
                        
                        # Add AI-specific metrics
                        span.set_attribute("ai.duration_ms", (end_time - start_time) * 1000)
                        span.set_attribute("ai.success", True)
                        
                        # Add response context
                        if isinstance(result, dict):
                            if "confidence" in result:
                                span.set_attribute("ai.confidence", result["confidence"])
                            if "tokens_used" in result:
                                span.set_attribute("ai.tokens_used", result["tokens_used"])
                        
                        span.set_status(Status(StatusCode.OK))
                        return result
                        
                    except Exception as e:
                        span.set_attribute("ai.success", False)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.set_attribute("error", True)
                        span.set_attribute("error.message", str(e))
                        raise
            
            return wrapper
        return decorator
    
    def trace_database_operation(self, operation: str, table: str = None):
        """Trace database operations"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                span_name = f"db.{operation}"
                
                with self.tracer.start_as_current_span(span_name) as span:
                    # Database-specific attributes
                    span.set_attribute("db.operation", operation)
                    if table:
                        span.set_attribute("db.table", table)
                    
                    # Add query context
                    if "query" in kwargs:
                        span.set_attribute("db.query", str(kwargs["query"])[:1000])  # Truncate long queries
                    
                    try:
                        start_time = time.time()
                        result = await func(*args, **kwargs)
                        end_time = time.time()
                        
                        # Add database metrics
                        span.set_attribute("db.duration_ms", (end_time - start_time) * 1000)
                        span.set_attribute("db.success", True)
                        
                        # Add result context
                        if isinstance(result, (list, tuple)):
                            span.set_attribute("db.rows_affected", len(result))
                        
                        span.set_status(Status(StatusCode.OK))
                        return result
                        
                    except Exception as e:
                        span.set_attribute("db.success", False)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.set_attribute("error", True)
                        span.set_attribute("error.message", str(e))
                        raise
            
            return wrapper
        return decorator
    
    def trace_file_operation(self, operation: str, file_type: str = None):
        """Trace file operations"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                span_name = f"file.{operation}"
                
                with self.tracer.start_as_current_span(span_name) as span:
                    # File-specific attributes
                    span.set_attribute("file.operation", operation)
                    if file_type:
                        span.set_attribute("file.type", file_type)
                    
                    # Add file context
                    if "file_path" in kwargs:
                        span.set_attribute("file.path", str(kwargs["file_path"]))
                    
                    if "file_size" in kwargs:
                        span.set_attribute("file.size_bytes", kwargs["file_size"])
                    
                    try:
                        start_time = time.time()
                        result = await func(*args, **kwargs)
                        end_time = time.time()
                        
                        # Add file metrics
                        span.set_attribute("file.duration_ms", (end_time - start_time) * 1000)
                        span.set_attribute("file.success", True)
                        
                        span.set_status(Status(StatusCode.OK))
                        return result
                        
                    except Exception as e:
                        span.set_attribute("file.success", False)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.set_attribute("error", True)
                        span.set_attribute("error.message", str(e))
                        raise
            
            return wrapper
        return decorator


class TraceContextManager:
    """Manages trace context across service boundaries"""
    
    def __init__(self, tracer: ArchBuilderTracer):
        self.tracer = tracer
        self.propagator = TraceContextTextMapPropagator()
    
    def extract_trace_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Extract trace context from headers"""
        return self.propagator.extract(headers)
    
    def inject_trace_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject trace context into headers"""
        return self.propagator.inject(headers)
    
    def set_baggage(self, key: str, value: str):
        """Set baggage data for trace context"""
        set_baggage(key, value)
    
    def get_baggage(self, key: str) -> Optional[str]:
        """Get baggage data from trace context"""
        baggage = get_all_baggage()
        return baggage.get(key)
    
    def get_all_baggage(self) -> Dict[str, str]:
        """Get all baggage data"""
        return get_all_baggage()


class TraceMetrics:
    """Collects metrics from trace data"""
    
    def __init__(self, tracer: ArchBuilderTracer):
        self.tracer = tracer
        self.metrics = {
            "total_spans": 0,
            "error_spans": 0,
            "ai_operations": 0,
            "db_operations": 0,
            "file_operations": 0,
            "avg_duration_ms": 0,
            "error_rate": 0
        }
    
    def update_metrics(self, span_data: Dict[str, Any]):
        """Update metrics from span data"""
        self.metrics["total_spans"] += 1
        
        if span_data.get("error"):
            self.metrics["error_spans"] += 1
        
        if span_data.get("ai.operation"):
            self.metrics["ai_operations"] += 1
        
        if span_data.get("db.operation"):
            self.metrics["db_operations"] += 1
        
        if span_data.get("file.operation"):
            self.metrics["file_operations"] += 1
        
        # Update error rate
        self.metrics["error_rate"] = (
            self.metrics["error_spans"] / self.metrics["total_spans"]
            if self.metrics["total_spans"] > 0 else 0
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.copy()


# Global tracer instance
_trace_config = TraceConfig()
_tracer = ArchBuilderTracer(_trace_config)
_trace_context_manager = TraceContextManager(_tracer)
_trace_metrics = TraceMetrics(_tracer)


def trace_function(operation_name: str = None, attributes: Dict[str, Any] = None):
    """Global function tracer decorator"""
    return _tracer.trace_function(operation_name, attributes)


def trace_ai_operation(model: str, operation: str, user_id: str = None):
    """Global AI operation tracer decorator"""
    return _tracer.trace_ai_operation(model, operation, user_id)


def trace_database_operation(operation: str, table: str = None):
    """Global database operation tracer decorator"""
    return _tracer.trace_database_operation(operation, table)


def trace_file_operation(operation: str, file_type: str = None):
    """Global file operation tracer decorator"""
    return _tracer.trace_file_operation(operation, file_type)


async def trace_async_operation(operation_name: str, attributes: Dict[str, Any] = None):
    """Global async operation tracer context manager"""
    return _tracer.trace_async_operation(operation_name, attributes)


def get_trace_context_manager() -> TraceContextManager:
    """Get trace context manager"""
    return _trace_context_manager


def get_trace_metrics() -> Dict[str, Any]:
    """Get trace metrics"""
    return _trace_metrics.get_metrics()


def setup_auto_instrumentation(app=None):
    """Setup automatic instrumentation"""
    if _trace_config.enable_auto_instrumentation:
        # Instrument FastAPI
        if app:
            FastAPIInstrumentor.instrument_app(app)
        
        # Instrument HTTP clients
        HTTPXClientInstrumentor().instrument()
        RequestsInstrumentor().instrument()
        
        # Instrument database
        SQLAlchemyInstrumentor().instrument()
        
        # Instrument Redis
        RedisInstrumentor().instrument()
        
        logger.info("OpenTelemetry auto-instrumentation enabled")
