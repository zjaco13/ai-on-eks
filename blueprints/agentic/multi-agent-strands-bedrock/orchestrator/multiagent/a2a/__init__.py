"""Agent-to-Agent (A2A) communication protocol implementation for Strands Agents.

This module provides classes and utilities for enabling Strands Agents to communicate
with other agents using the Agent-to-Agent (A2A) protocol.

Docs: https://google-a2a.github.io/A2A/latest/

Classes:
    A2AAgent: A wrapper that adapts a Strands Agent to be A2A-compatible.
"""

from .agent import A2AAgent

__all__ = ["A2AAgent"]
