"""
CUGA-Phoenix Integration Layer

Provides hooks to integrate Phoenix observability into CUGA's execution flow:
1. Trace agent workflows and decision-making
2. Monitor tool executions and API calls
3. Track performance metrics
4. Capture errors and debugging information
"""

from typing import Optional, Dict, Any
from loguru import logger

from cuga.backend.phoenix_integration.phoenix_tracer import PhoenixTracer, get_phoenix_tracer
from cuga.backend.cuga_graph.state.agent_state import AgentState
from cuga.config import settings


class CugaPhoenixIntegration:
    """Integration layer between CUGA and Phoenix observability."""

    def __init__(self):
        """Initialize the integration."""
        self.tracer: Optional[PhoenixTracer] = None
        self.enabled = False
        self.current_trace_context = None

        # Initialize if Phoenix is enabled in settings
        if hasattr(settings, 'phoenix') and settings.phoenix.enabled:
            self._initialize()

    def _initialize(self):
        """Initialize Phoenix tracer."""
        try:
            self.tracer = get_phoenix_tracer(
                project_name=settings.phoenix.project_name,
                phoenix_host=settings.phoenix.phoenix_host,
                phoenix_port=settings.phoenix.phoenix_port,
                enabled=settings.phoenix.enabled,
                auto_instrument_langchain=settings.phoenix.auto_instrument_langchain,
                launch_phoenix=settings.phoenix.launch_phoenix,
                phoenix_collector_endpoint=settings.phoenix.get('phoenix_collector_endpoint'),
            )

            self.enabled = self.tracer.enabled

            if self.enabled:
                logger.info("✅ CUGA-Phoenix integration initialized")
                stats = self.tracer.get_stats()
                if stats.get('ui_url'):
                    logger.info(f"   Phoenix UI: {stats['ui_url']}")
            else:
                logger.warning("⚠️  Phoenix integration failed to initialize")

        except Exception as e:
            logger.error(f"Failed to initialize Phoenix integration: {e}")
            self.enabled = False

    def start_agent_trace(self, task: str, state: Optional[AgentState] = None) -> Any:
        """
        Start tracing an agent execution.

        Args:
            task: The task being executed
            state: Agent state (optional)

        Returns:
            Trace context
        """
        if not self.enabled:
            return None

        try:
            metadata = {
                "task": task,
                "timestamp": str(state.timestamp) if state and hasattr(state, 'timestamp') else None,
                "mode": getattr(settings, 'cuga_mode', 'unknown'),
            }

            self.current_trace_context = self.tracer.start_trace(
                trace_name=f"cuga_agent_{task[:50]}", metadata=metadata
            )

            logger.debug(f"Started Phoenix trace for task: {task[:50]}...")
            return self.current_trace_context

        except Exception as e:
            logger.error(f"Failed to start agent trace: {e}")
            return None

    def log_tool_execution(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        success: bool = True,
        error: Optional[str] = None,
        execution_time: Optional[float] = None,
    ):
        """
        Log a tool execution to Phoenix.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input arguments
            tool_output: Tool output
            success: Whether execution was successful
            error: Error message if failed
            execution_time: Execution time in seconds
        """
        if not self.enabled:
            return

        try:
            metadata = {"execution_time": execution_time, "success": success}

            self.tracer.log_tool_execution(
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
                success=success,
                error=error,
                metadata=metadata,
            )

            logger.debug(f"Logged tool execution: {tool_name} (success: {success})")

        except Exception as e:
            logger.error(f"Failed to log tool execution: {e}")

    def log_agent_step(
        self,
        step_name: str,
        step_type: str,
        input_data: Any,
        output_data: Any,
        state: Optional[AgentState] = None,
    ):
        """
        Log an agent execution step.

        Args:
            step_name: Name of the step
            step_type: Type of step (e.g., 'planning', 'execution', 'reflection')
            input_data: Step input
            output_data: Step output
            state: Agent state (optional)
        """
        if not self.enabled:
            return

        try:
            metadata = {"step_type": step_type, "state_keys": list(state.__dict__.keys()) if state else []}

            self.tracer.log_agent_step(
                step_name=step_name,
                step_type=step_type,
                input_data=input_data,
                output_data=output_data,
                metadata=metadata,
            )

            logger.debug(f"Logged agent step: {step_name} ({step_type})")

        except Exception as e:
            logger.error(f"Failed to log agent step: {e}")

    def log_llm_call(
        self,
        model: str,
        prompt: str,
        response: str,
        tokens_used: Optional[int] = None,
        latency: Optional[float] = None,
    ):
        """
        Log an LLM call (for manual logging when auto-instrumentation isn't sufficient).

        Args:
            model: Model name
            prompt: Input prompt
            response: Model response
            tokens_used: Number of tokens used
            latency: Response latency in seconds
        """
        if not self.enabled:
            return

        try:
            metadata = {"tokens_used": tokens_used, "latency": latency}

            self.tracer.log_llm_call(model=model, prompt=prompt, response=response, metadata=metadata)

            logger.debug(f"Logged LLM call: {model}")

        except Exception as e:
            logger.error(f"Failed to log LLM call: {e}")

    def log_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Log an error to Phoenix.

        Args:
            error_type: Type of error
            error_message: Error message
            stack_trace: Stack trace if available
            context: Additional context
        """
        if not self.enabled:
            return

        try:
            metadata = context or {}

            self.tracer.log_error(
                error_type=error_type, error_message=error_message, stack_trace=stack_trace, metadata=metadata
            )

            logger.debug(f"Logged error: {error_type}")

        except Exception as e:
            logger.error(f"Failed to log error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get integration statistics.

        Returns:
            Dictionary with integration stats
        """
        if not self.tracer:
            return {"enabled": False, "tracer_available": False}

        stats = self.tracer.get_stats()
        stats["integration_enabled"] = self.enabled
        return stats

    def shutdown(self):
        """Shutdown Phoenix integration."""
        if self.tracer:
            self.tracer.shutdown()
            logger.info("✅ Phoenix integration shutdown complete")


# Singleton instance
_cuga_phoenix_instance: Optional[CugaPhoenixIntegration] = None


def get_cuga_phoenix_integration(force_reinit: bool = False) -> CugaPhoenixIntegration:
    """
    Get or create the CUGA-Phoenix integration singleton instance.

    Args:
        force_reinit: Force reinitialization even if instance exists

    Returns:
        CugaPhoenixIntegration instance
    """
    global _cuga_phoenix_instance

    if _cuga_phoenix_instance is None or force_reinit:
        if _cuga_phoenix_instance and force_reinit:
            _cuga_phoenix_instance.shutdown()

        _cuga_phoenix_instance = CugaPhoenixIntegration()

    return _cuga_phoenix_instance


# Made with Bob
