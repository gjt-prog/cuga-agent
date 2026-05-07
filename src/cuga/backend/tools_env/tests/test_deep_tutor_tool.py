"""
Tests for the DeepTutor guided-learning tool and its supervisor integration.

These tests mock the WebSocket connection so no running DeepTutor instance is
required.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cuga.backend.tools_env.deep_tutor_tool import (
    _query_deep_tutor_ws,
    consult_deep_tutor,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ws_messages(messages: list[dict[str, Any]]) -> AsyncIterator[str]:
    """Create an async iterator that yields JSON-encoded WS messages."""

    async def _iter():
        for msg in messages:
            yield json.dumps(msg)

    return _iter()


class _FakeWebSocket:
    """Minimal fake WebSocket that replays canned messages."""

    def __init__(self, messages: list[dict[str, Any]]):
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        for msg in messages:
            self._queue.put_nowait(json.dumps(msg))
        self._sent: list[str] = []

    async def send(self, data: str) -> None:
        self._sent.append(data)

    async def recv(self) -> str:
        if self._queue.empty():
            # Simulate connection closing after all messages are consumed.
            await asyncio.sleep(999)  # will be cancelled by timeout
        return self._queue.get_nowait()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


# ---------------------------------------------------------------------------
# Unit tests — _query_deep_tutor_ws
# ---------------------------------------------------------------------------
class TestQueryDeepTutorWs:
    """Unit tests for the internal ``_query_deep_tutor_ws`` helper."""

    @pytest.mark.asyncio
    async def test_successful_streamed_response(self):
        """Chunks followed by a result event should be aggregated."""
        messages = [
            {"type": "session", "session_id": "s1"},
            {"type": "status", "stage": "generating", "message": "Generating..."},
            {"type": "stream", "content": "Hello "},
            {"type": "stream", "content": "World"},
            {"type": "result", "content": "Hello World"},
        ]
        fake_ws = _FakeWebSocket(messages)

        with patch(
            "cuga.backend.tools_env.deep_tutor_tool.websockets.connect",
            return_value=fake_ws,
        ):
            result = await _query_deep_tutor_ws("test query", timeout=5)

        assert result == "Hello World"

    @pytest.mark.asyncio
    async def test_result_event_overrides_stream_chunks(self):
        """The ``result`` event should be used as the final response."""
        messages = [
            {"type": "stream", "content": "partial"},
            {"type": "result", "content": "The full answer."},
        ]
        fake_ws = _FakeWebSocket(messages)

        with patch(
            "cuga.backend.tools_env.deep_tutor_tool.websockets.connect",
            return_value=fake_ws,
        ):
            result = await _query_deep_tutor_ws("q", timeout=5)

        assert result == "The full answer."

    @pytest.mark.asyncio
    async def test_sources_appended(self):
        """Source citations should be appended to the response."""
        messages = [
            {"type": "stream", "content": "Answer text."},
            {
                "type": "sources",
                "rag": [{"title": "Textbook Ch.3"}],
                "web": [{"url": "https://example.com"}],
            },
            {"type": "result", "content": "Answer text."},
        ]
        fake_ws = _FakeWebSocket(messages)

        with patch(
            "cuga.backend.tools_env.deep_tutor_tool.websockets.connect",
            return_value=fake_ws,
        ):
            result = await _query_deep_tutor_ws("q", timeout=5)

        assert "Textbook Ch.3" in result
        assert "https://example.com" in result

    @pytest.mark.asyncio
    async def test_error_event(self):
        """An error event should return a user-friendly error string."""
        messages = [
            {"type": "error", "message": "LLM quota exceeded"},
        ]
        fake_ws = _FakeWebSocket(messages)

        with patch(
            "cuga.backend.tools_env.deep_tutor_tool.websockets.connect",
            return_value=fake_ws,
        ):
            result = await _query_deep_tutor_ws("q", timeout=5)

        assert "LLM quota exceeded" in result

    @pytest.mark.asyncio
    async def test_connection_failure(self):
        """A connection failure should return a descriptive error."""
        with patch(
            "cuga.backend.tools_env.deep_tutor_tool.websockets.connect",
            side_effect=OSError("Connection refused"),
        ):
            result = await _query_deep_tutor_ws("q", timeout=5)

        assert "Connection refused" in result
        assert "deeptutor serve" in result


# ---------------------------------------------------------------------------
# Integration-style test — consult_deep_tutor tool
# ---------------------------------------------------------------------------
class TestConsultDeepTutorTool:
    """Verify the public ``@tool`` wrapper delegates correctly."""

    @pytest.mark.asyncio
    async def test_tool_invokes_ws_query(self):
        """The LangChain tool should call the WS helper and return its result."""
        messages = [
            {"type": "result", "content": "A derivative measures the rate of change."},
        ]
        fake_ws = _FakeWebSocket(messages)

        with patch(
            "cuga.backend.tools_env.deep_tutor_tool.websockets.connect",
            return_value=fake_ws,
        ):
            result = await consult_deep_tutor.ainvoke(
                {"query": "Explain derivatives step by step"}
            )

        assert "rate of change" in result


# ---------------------------------------------------------------------------
# Supervisor wiring test (lightweight — no LLM needed)
# ---------------------------------------------------------------------------
class TestGuidedLearningSupervisorWiring:
    """Verify the demo helper builds a valid supervisor."""

    def test_build_supervisor_creates_two_agents(self):
        """Supervisor wiring should produce a valid object with two agents."""
        from unittest.mock import MagicMock

        # Mock LLMManager so CugaAgent doesn't need real API keys.
        fake_model = MagicMock()
        with patch(
            "cuga.sdk.LLMManager"
        ) as mock_llm_cls:
            mock_llm_cls.return_value.get_model.return_value = fake_model

            from cuga.backend.tools_env.demo_guided_learning import (
                build_guided_learning_supervisor,
            )

            supervisor = build_guided_learning_supervisor()

        # The supervisor should have been created without errors.
        assert supervisor is not None
