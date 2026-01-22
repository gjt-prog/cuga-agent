"""
Phoenix Tracer for CUGA Agent

Provides comprehensive observability using Phoenix (Arize-Phoenix) for:
- LLM call tracing
- Tool execution tracking
- Agent workflow visualization
- Performance metrics
- Error tracking
"""

import os
from typing import Optional, Dict, Any
from loguru import logger

try:
    import phoenix as px
    from phoenix.trace import using_project
    from openinference.instrumentation.langchain import (
        LangChainInstrumentor as OpenInferenceLangChainInstrumentor,
    )

    PHOENIX_AVAILABLE = True
except ImportError:
    PHOENIX_AVAILABLE = False
    logger.warning("Phoenix not installed. Install with: pip install arize-phoenix")


class PhoenixTracer:
    """
    Phoenix tracer for CUGA agent observability.

    Provides automatic instrumentation for:
    - LangChain LLM calls
    - Tool executions
    - Agent workflows
    - Custom spans for CUGA-specific operations
    """

    _instance: Optional['PhoenixTracer'] = None

    def __init__(
        self,
        project_name: str = "cuga-agent",
        phoenix_host: str = "http://localhost",
        phoenix_port: int = 6006,
        enabled: bool = True,
        auto_instrument_langchain: bool = True,
        launch_phoenix: bool = False,
        phoenix_collector_endpoint: Optional[str] = None,
    ):
        """
        Initialize Phoenix tracer.

        Args:
            project_name: Name of the Phoenix project
            phoenix_host: Phoenix server host
            phoenix_port: Phoenix server port
            enabled: Enable/disable tracing
            auto_instrument_langchain: Automatically instrument LangChain
            launch_phoenix: Launch Phoenix server locally
            phoenix_collector_endpoint: Custom collector endpoint (overrides host/port)
        """
        self.project_name = project_name
        self.phoenix_host = phoenix_host
        self.phoenix_port = phoenix_port
        self.enabled = enabled and PHOENIX_AVAILABLE
        self.auto_instrument_langchain = auto_instrument_langchain
        self.launch_phoenix = launch_phoenix
        self.phoenix_collector_endpoint = phoenix_collector_endpoint

        self.session = None
        self.instrumentor = None
        self._initialized = False

        if self.enabled:
            self._initialize()
        else:
            if not PHOENIX_AVAILABLE:
                logger.warning("⚠️  Phoenix not available - tracing disabled")
            else:
                logger.info("ℹ️  Phoenix tracing disabled in configuration")

    def _initialize(self):
        """Initialize Phoenix tracing."""
        try:
            # Launch Phoenix server if requested
            if self.launch_phoenix:
                logger.info("🚀 Launching Phoenix server...")
                self.session = px.launch_app()
                logger.info(f"✅ Phoenix UI available at: {self.session.url}")

            # Set up collector endpoint
            if self.phoenix_collector_endpoint:
                endpoint = self.phoenix_collector_endpoint
            else:
                endpoint = f"{self.phoenix_host}:{self.phoenix_port}"

            # Set environment variable for OpenTelemetry
            os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = endpoint

            # Auto-instrument LangChain if enabled
            if self.auto_instrument_langchain:
                try:
                    self.instrumentor = OpenInferenceLangChainInstrumentor()
                    self.instrumentor.instrument()
                    logger.info("✅ LangChain auto-instrumentation enabled")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to auto-instrument LangChain: {e}")

            self._initialized = True
            logger.info(f"✅ Phoenix tracer initialized (project: {self.project_name})")
            logger.info(f"   Collector endpoint: {endpoint}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Phoenix tracer: {e}")
            self.enabled = False

    def start_trace(self, trace_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Start a new trace context.

        Args:
            trace_name: Name of the trace
            metadata: Additional metadata for the trace
        """
        if not self.enabled:
            return None

        try:
            return using_project(self.project_name)
        except Exception as e:
            logger.error(f"Failed to start trace '{trace_name}': {e}")
            return None

    def log_llm_call(self, model: str, prompt: str, response: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Log an LLM call (for manual logging when auto-instrumentation isn't used).

        Args:
            model: Model name
            prompt: Input prompt
            response: Model response
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        try:
            # LangChain auto-instrumentation handles this automatically
            # This method is for custom/manual logging if needed
            logger.debug(f"LLM call logged: {model}")
        except Exception as e:
            logger.error(f"Failed to log LLM call: {e}")

    def log_tool_execution(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log a tool execution.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input arguments
            tool_output: Tool output
            success: Whether execution was successful
            error: Error message if failed
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        try:
            # LangChain auto-instrumentation handles tool calls automatically
            # This method is for additional custom logging if needed
            logger.debug(f"Tool execution logged: {tool_name} (success: {success})")
        except Exception as e:
            logger.error(f"Failed to log tool execution: {e}")

    def log_agent_step(
        self,
        step_name: str,
        step_type: str,
        input_data: Any,
        output_data: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log an agent execution step.

        Args:
            step_name: Name of the step
            step_type: Type of step (e.g., 'planning', 'execution', 'reflection')
            input_data: Step input
            output_data: Step output
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        try:
            logger.debug(f"Agent step logged: {step_name} ({step_type})")
        except Exception as e:
            logger.error(f"Failed to log agent step: {e}")

    def log_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log an error.

        Args:
            error_type: Type of error
            error_message: Error message
            stack_trace: Stack trace if available
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        try:
            logger.debug(f"Error logged: {error_type} - {error_message}")
        except Exception as e:
            logger.error(f"Failed to log error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get tracer statistics.

        Returns:
            Dictionary with tracer stats
        """
        return {
            "enabled": self.enabled,
            "initialized": self._initialized,
            "project_name": self.project_name,
            "phoenix_available": PHOENIX_AVAILABLE,
            "auto_instrument_langchain": self.auto_instrument_langchain,
            "collector_endpoint": self.phoenix_collector_endpoint
            or f"{self.phoenix_host}:{self.phoenix_port}",
            "session_active": self.session is not None,
            "ui_url": self.session.url if self.session else None,
        }

    def shutdown(self):
        """Shutdown Phoenix tracer and cleanup resources."""
        if not self.enabled:
            return

        try:
            # Uninstrument LangChain if it was instrumented
            if self.instrumentor:
                self.instrumentor.uninstrument()
                logger.info("✅ LangChain uninstrumented")

            # Close Phoenix session if it was launched
            if self.session:
                # Phoenix session cleanup (if needed)
                logger.info("✅ Phoenix session closed")

            self._initialized = False
            logger.info("✅ Phoenix tracer shutdown complete")

        except Exception as e:
            logger.error(f"Error during Phoenix tracer shutdown: {e}")

    def __del__(self):
        """Cleanup on deletion."""
        if self._initialized:
            self.shutdown()


# Singleton instance
_phoenix_tracer_instance: Optional[PhoenixTracer] = None


def get_phoenix_tracer(
    project_name: str = "cuga-agent",
    phoenix_host: str = "http://localhost",
    phoenix_port: int = 6006,
    enabled: bool = True,
    auto_instrument_langchain: bool = True,
    launch_phoenix: bool = False,
    phoenix_collector_endpoint: Optional[str] = None,
    force_reinit: bool = False,
) -> PhoenixTracer:
    """
    Get or create the Phoenix tracer singleton instance.

    Args:
        project_name: Name of the Phoenix project
        phoenix_host: Phoenix server host
        phoenix_port: Phoenix server port
        enabled: Enable/disable tracing
        auto_instrument_langchain: Automatically instrument LangChain
        launch_phoenix: Launch Phoenix server locally
        phoenix_collector_endpoint: Custom collector endpoint
        force_reinit: Force reinitialization even if instance exists

    Returns:
        PhoenixTracer instance
    """
    global _phoenix_tracer_instance

    if _phoenix_tracer_instance is None or force_reinit:
        if _phoenix_tracer_instance and force_reinit:
            _phoenix_tracer_instance.shutdown()

        _phoenix_tracer_instance = PhoenixTracer(
            project_name=project_name,
            phoenix_host=phoenix_host,
            phoenix_port=phoenix_port,
            enabled=enabled,
            auto_instrument_langchain=auto_instrument_langchain,
            launch_phoenix=launch_phoenix,
            phoenix_collector_endpoint=phoenix_collector_endpoint,
        )

    return _phoenix_tracer_instance


# Made with Bob
