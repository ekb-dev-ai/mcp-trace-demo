import os


def configure_telemetry(
        service_name: str,
        instrument_crewai: bool = False,
        stdio_safe: bool = False
 ) -> None:
    """
    Configure tracing for MCP
    """

    import logfire

    token = os.getenv("LOGFIRE_TOKEN", "").strip()
    if not token:
        os.environ.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf")
        os.environ.setdefault("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://localhost:4318/v1/traces")
        os.environ.setdefault("OTEL_METRICS_EXPORTER", "none")
    
    logfire.configure(
        service_name=service_name,
        send_to_logfire=bool(token),
        token=token or None,
        console=False if stdio_safe else None,
    )
    logfire.instrument_mcp()

    if instrument_crewai:
        _instrument_crewai_and_llm(logfire)


def _instrument_crewai_and_llm(logfire_module) -> None:

    tracer_provider = logfire_module.DEFAULT_LOGFIRE_INSTANCE.config.get_tracer_provider()
    from opentelemetry.instrumentation.crewai import CrewAIInstrumentor

    CrewAIInstrumentor().instrument(tracer_provider=tracer_provider)
    logfire_module.instrument_litellm()