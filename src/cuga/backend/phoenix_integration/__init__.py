"""
Phoenix Arize Observability Integration for CUGA

This module provides comprehensive observability for CUGA agent executions
using Phoenix (Arize-Phoenix), an open-source LLM observability platform.

Features:
- Automatic tracing of LLM calls
- Tool execution tracking
- Agent workflow visualization
- Performance metrics and analytics
- Error tracking and debugging
"""

from cuga.backend.phoenix_integration.phoenix_tracer import PhoenixTracer, get_phoenix_tracer

__all__ = ["PhoenixTracer", "get_phoenix_tracer"]

# Made with Bob
