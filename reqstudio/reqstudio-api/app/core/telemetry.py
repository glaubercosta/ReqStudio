"""OpenTelemetry setup e structured JSON logging.

Configura:
  - Tracing básico com OTLP exporter (desabilitado por default em dev)
  - Structured JSON logging via Python logging + extra fields
  - FastAPI instrumentation automática
"""

import json
import logging
import sys
from datetime import datetime, timezone

from app.core.config import settings


class StructuredJsonFormatter(logging.Formatter):
    """Formata logs como JSON estruturado para ingestão em observability tools."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Campos extras adicionados via logger.info(..., extra={...})
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "taskName",
            }:
                log_entry[key] = value

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str, ensure_ascii=False)


def setup_logging() -> None:
    """Configura o sistema de logging com formatter JSON estruturado."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Reduzir verbosidade de bibliotecas externas
    for noisy_logger in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def setup_telemetry() -> None:
    """Configura OpenTelemetry tracing básico.

    Em dev (DEBUG=True): apenas logging, sem exportador externo.
    Em produção: configure OTEL_EXPORTER_OTLP_ENDPOINT para envio ao coletor.
    """
    setup_logging()

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )

        resource = Resource.create({"service.name": "reqstudio-api"})
        provider = TracerProvider(resource=resource)

        if settings.DEBUG:
            # Dev: exibe spans no console (opcional — pode ser removido)
            provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )

        trace.set_tracer_provider(provider)

        # Instrumentação automática FastAPI
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor().instrument()

        logging.getLogger(__name__).info(
            "OpenTelemetry configured",
            extra={"debug": settings.DEBUG},
        )

    except ImportError:
        logging.getLogger(__name__).warning(
            "OpenTelemetry packages not installed — tracing disabled. "
            "Add opentelemetry-sdk and opentelemetry-instrumentation-fastapi to requirements.txt"
        )
