"""
demo_guided_learning — Example script showing the DeepTutor guided-learning
agent integrated into a CugaSupervisor multi-agent setup.

Usage
-----
1. Start DeepTutor in a separate terminal::

       cd /path/to/DeepTutor
       deeptutor serve          # default port 8001

2. Run this script::

       python -m cuga.backend.tools_env.demo_guided_learning

   or import and call ``main()`` from your own orchestration code.

The supervisor will have two sub-agents:

- **general** — a vanilla CugaAgent with no special tools (handles everyday
  tasks).
- **tutor** — a CugaAgent equipped with the ``consult_deep_tutor`` tool,
  specialising in guided learning and pedagogical explanations.

When the user's request is educational in nature, the supervisor delegates
to the tutor agent which in turn queries the DeepTutor backend.
"""

from __future__ import annotations

import asyncio

from langchain_core.tools import tool

from cuga import CugaAgent, CugaSupervisor
from cuga.backend.tools_env.deep_tutor_tool import consult_deep_tutor


# ---------------------------------------------------------------------------
# Optional: A trivial "general" tool so the general agent isn't empty.
# ---------------------------------------------------------------------------
@tool
def echo(text: str) -> str:
    """Echo the input text back — a no-op placeholder tool."""
    return text


# ---------------------------------------------------------------------------
# Build the supervisor
# ---------------------------------------------------------------------------
def build_guided_learning_supervisor() -> CugaSupervisor:
    """Construct and return a ``CugaSupervisor`` with general + tutor agents."""

    general_agent = CugaAgent(tools=[echo])
    general_agent.description = (
        "A general-purpose assistant for everyday tasks such as "
        "summarisation, look-ups, and simple Q&A."
    )

    tutor_agent = CugaAgent(tools=[consult_deep_tutor])
    tutor_agent.description = (
        "A specialised agent for guided learning, explanations, "
        "step-by-step problem solving, and generating quizzes. "
        "Delegate to this agent when the user needs to learn, "
        "understand concepts, or solve complex problems methodically."
    )

    supervisor = CugaSupervisor(
        agents={
            "general": general_agent,
            "tutor": tutor_agent,
        },
    )
    return supervisor


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
async def main() -> None:
    supervisor = build_guided_learning_supervisor()

    query = "Can you act as my tutor and explain how Fourier transforms work?"
    print(f"\n🎓 Sending query to supervisor:\n   {query}\n")

    result = await supervisor.invoke(query)
    print(f"\n📘 Response:\n{result.answer}\n")


if __name__ == "__main__":
    asyncio.run(main())
