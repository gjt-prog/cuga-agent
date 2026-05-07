"""
DeepTutor Tool — LangChain tool wrapper for the DeepTutor tutoring service.

Provides a ``consult_deep_tutor`` tool that communicates with a running
DeepTutor backend (``deeptutor serve``) over its WebSocket chat API.

The tool is designed to be handed to a dedicated ``CugaAgent`` inside a
``CugaSupervisor`` so that complex educational, problem-solving, and
explanation tasks can be delegated to DeepTutor's multi-agent pipeline.

Environment variables
---------------------
``DEEP_TUTOR_WS_URL``  — WebSocket URL of the DeepTutor chat endpoint.
                         Default: ``ws://localhost:8001/api/v1/chat``

``DEEP_TUTOR_HTTP_URL`` — HTTP base URL used for REST fallback or health checks.
                          Default: ``http://localhost:8001``
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Optional

import websockets  # type: ignore[import-untyped]
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_WS_URL = "ws://localhost:8001/api/v1/chat"
DEFAULT_HTTP_URL = "http://localhost:8001"

_DEEP_TUTOR_WS_URL: str = os.environ.get("DEEP_TUTOR_WS_URL", DEFAULT_WS_URL)
_DEEP_TUTOR_HTTP_URL: str = os.environ.get("DEEP_TUTOR_HTTP_URL", DEFAULT_HTTP_URL)

# Maximum seconds to wait for a complete response from DeepTutor.
_TIMEOUT_SECONDS: int = int(os.environ.get("DEEP_TUTOR_TIMEOUT", "120"))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
async def _query_deep_tutor_ws(
    message: str,
    *,
    session_id: Optional[str] = None,
    capability: str = "chat",
    enable_rag: bool = False,
    kb_name: str = "",
    ws_url: str | None = None,
    timeout: int | None = None,
) -> str:
    """Send a query to the DeepTutor WebSocket chat endpoint and return the
    aggregated response text.

    The protocol mirrors ``deeptutor/api/routers/chat.py``:

    - Client sends a JSON message with ``message``, ``session_id``, etc.
    - Server streams ``{"type": "stream", "content": "..."}`` chunks.
    - Server finishes with ``{"type": "result", "content": "..."}`` or
      ``{"type": "sources", ...}`` followed by ``result``.
    - On error: ``{"type": "error", "message": "..."}``.
    """
    url = ws_url or _DEEP_TUTOR_WS_URL
    t = timeout or _TIMEOUT_SECONDS

    payload = {
        "message": message,
        "session_id": session_id,
        "capability": capability,
        "enable_rag": enable_rag,
        "kb_name": kb_name,
        "enable_web_search": False,
    }

    full_response = ""
    sources_text = ""

    try:
        async with websockets.connect(url, open_timeout=10) as ws:
            await ws.send(json.dumps(payload))

            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=t)
                except asyncio.TimeoutError:
                    logger.warning(
                        "DeepTutor response timed out after %d s", t
                    )
                    break

                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type", "")

                if msg_type == "stream":
                    full_response += data.get("content", "")

                elif msg_type == "result":
                    # The result event carries the complete response.
                    full_response = data.get("content", full_response)
                    break

                elif msg_type == "sources":
                    rag_sources = data.get("rag", [])
                    web_sources = data.get("web", [])
                    parts: list[str] = []
                    for src in rag_sources:
                        parts.append(
                            f"- [RAG] {src.get('title', src.get('filename', 'unknown'))}"
                        )
                    for src in web_sources:
                        parts.append(
                            f"- [Web] {src.get('title', src.get('url', 'unknown'))}"
                        )
                    if parts:
                        sources_text = "\n\nSources:\n" + "\n".join(parts)

                elif msg_type == "error":
                    error_msg = data.get("message", "Unknown DeepTutor error")
                    logger.error("DeepTutor returned error: %s", error_msg)
                    return f"DeepTutor error: {error_msg}"

                elif msg_type == "session":
                    # Session ID acknowledgement — ignore.
                    continue

                elif msg_type == "status":
                    # Status updates (e.g. "Generating response...") — ignore.
                    continue

    except (OSError, websockets.exceptions.WebSocketException) as exc:
        logger.error("Failed to connect to DeepTutor at %s: %s", url, exc)
        return (
            f"Failed to reach DeepTutor at {url}. "
            f"Ensure `deeptutor serve` is running. Error: {exc}"
        )

    return (full_response + sources_text).strip() or "No response from DeepTutor."


# ---------------------------------------------------------------------------
# Public LangChain tool
# ---------------------------------------------------------------------------
@tool
async def consult_deep_tutor(
    query: str,
    session_id: Optional[str] = None,
) -> str:
    """Consult the DeepTutor intelligent tutoring system for guided learning.

    Use this tool when the user needs:
    - Step-by-step explanations of concepts or problems
    - Guided walkthroughs of complex topics
    - Pedagogical, Socratic-style tutoring
    - Deep problem solving with citations

    Args:
        query: The question or topic to send to DeepTutor.
        session_id: Optional session ID to continue a previous DeepTutor
                     conversation. Pass None to start a new session.

    Returns:
        The tutoring response from DeepTutor, potentially including source
        citations.
    """
    logger.info("consult_deep_tutor called — query: %s", query[:120])
    return await _query_deep_tutor_ws(
        message=query,
        session_id=session_id,
    )
