"""
Kaizen Integration Module for CUGA Agent

This module integrates Kaizen's self-improving capabilities into CUGA,
enabling the agent to learn from past executions and retrieve relevant
guidelines for new tasks.
"""

from .kaizen_adapter import KaizenAdapter
from .trajectory_capture import TrajectoryCapture

__all__ = ['KaizenAdapter', 'TrajectoryCapture']

# Made with Bob
