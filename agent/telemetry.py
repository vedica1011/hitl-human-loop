"""OpenTelemetry → Langfuse wiring."""
from __future__ import annotations

import base64
import logging
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

log = logging.getLogger(__name__)


def setup_langfuse(service_name: str = "hitl-memory-assistant") -> None:
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = os.environ.get("LANGFUSE_SECRET_KEY")
    if not (pk and sk):
        log.info("Langfuse keys not set - skipping OTel wiring.")
        return

    host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
    auth = base64.b64encode(f"{pk}:{sk}".encode()).decode()
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{host}/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {auth}"

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    log.info("Langfuse OTel exporter active -> %s", host)
