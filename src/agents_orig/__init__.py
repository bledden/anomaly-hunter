"""
Facilitair Agents Module

This module contains all agent implementations and utilities:
- llm_client: LLM API client with OpenRouter integration
- hallucination_detector: Pattern-based hallucination detection
"""

from .llm_client import LLMClient, MultiAgentLLMOrchestrator
from .hallucination_detector import HallucinationDetector

__all__ = [
    'LLMClient',
    'MultiAgentLLMOrchestrator',
    'HallucinationDetector',
]
