"""
Optional OpenTelemetry integration for tracing and metrics.
"""

import os
from contextlib import contextmanager

# Check if OpenTelemetry SDK is installed
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    
    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False


def setup_telemetry(service_name: str = "shiftiq") -> None:
    """
    Initialize OpenTelemetry tracer if enabled.
    
    Can be enabled by pointing MIGRATION_OTEL_ENDPOINT to a collector.
    """
    endpoint = os.environ.get("MIGRATION_OTEL_ENDPOINT")
    if not _OTEL_AVAILABLE or not endpoint:
        return
        
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    
    # Use OTLP over HTTP
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)


def get_tracer(name: str):
    """Get a named tracer, or None if disabled."""
    if not _OTEL_AVAILABLE or not os.environ.get("MIGRATION_OTEL_ENDPOINT"):
        return None
    return trace.get_tracer(name)


@contextmanager
def trace_migration(name: str, attributes: dict = None):
    """
    Context manager for tracing migration steps.
    
    Usage:
        with trace_migration("analyze_code", {"file": "app.py"}) as span:
            do_work()
    """
    tracer = get_tracer(__name__)
    if not tracer:
        yield None
        return
        
    with tracer.start_as_current_span(name, attributes=attributes or {}) as span:
        yield span
