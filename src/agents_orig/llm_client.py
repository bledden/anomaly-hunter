"""
LLM Client for real agent execution
Supports OpenAI, Anthropic, and Google models
With optional interactive fallback manager for manual mode
"""

import os
import asyncio
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
import aiohttp
import json
from dotenv import load_dotenv
import weave
import litellm

# Load environment variables
load_dotenv()

# Import fallback manager (optional - only used in manual mode)
try:
    from agents.fallback_manager import FallbackManager, FallbackContext
    FALLBACK_AVAILABLE = True
except ImportError:
    FALLBACK_AVAILABLE = False


@dataclass
class LLMResponse:
    """Response from an LLM"""
    content: str
    model: str
    tokens_used: int
    latency: float
    error: Optional[str] = None


class LLMClient:
    """Unified client for multiple LLM providers using LiteLLM and OpenRouter"""

    def __init__(self, config: Dict[str, Any], manual_mode: bool = False):
        self.config = config
        self.manual_mode = manual_mode
        self.fallback_manager = None

        # Configure LiteLLM for OpenRouter
        litellm.api_key = os.getenv("OPENROUTER_API_KEY")
        litellm.api_base = "https://openrouter.ai/api/v1"

        # Initialize fallback manager ONLY if manual mode is enabled
        if manual_mode and FALLBACK_AVAILABLE:
            self.fallback_manager = FallbackManager(config_path="config/config.yaml", config_dict=config)
            if os.getenv("DEMO_MODE"):
                print("[INFO] Fallback manager enabled (manual mode)")

    @weave.op()
    async def execute_llm(
        self,
        agent_id: str,
        task: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        personality: str = "",
        expertise: list = None
    ) -> LLMResponse:
        """Execute task with specified LLM"""

        # Build the prompt
        prompt = self._build_prompt(agent_id, task, personality, expertise)

        # Track timing
        import time
        start_time = time.time()

        try:
            # Use LiteLLM to call OpenRouter - prefix model with "openrouter/"
            openrouter_model = f"openrouter/{model}"
            response = await litellm.acompletion(
                model=openrouter_model,  # e.g., "openrouter/openai/gpt-4", "openrouter/anthropic/claude-sonnet-4.5"
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            llm_response = LLMResponse(
                content=response.choices[0].message.content,
                model=model,
                tokens_used=response.usage.total_tokens,  # REAL tokens from OpenRouter
                latency=time.time() - start_time
            )

            # Log execution for demo
            if os.getenv("DEMO_MODE"):
                print(f"[LLM] {agent_id} using {model}: {llm_response.content[:100]}...")

            return llm_response

        except Exception as e:
            error_msg = f"LLM execution failed: {str(e)}"
            if os.getenv("DEMO_MODE"):
                print(f"[ERROR] {agent_id}: {error_msg}")

            # If manual mode and fallback manager available, offer to retry with different model
            if self.manual_mode and self.fallback_manager:
                # Classify error type
                error_type = self._classify_error(e)

                # Create fallback context
                context = FallbackContext(
                    agent_type=agent_id,
                    task_description=task[:100],
                    failed_model=model,
                    error_type=error_type,
                    error_message=error_msg,
                    attempt_number=1,  # Could track this better
                    session_cost=0.0,  # Could track this
                    estimated_cost=0.0
                )

                # Ask user for fallback
                next_model = self.fallback_manager.handle_model_failure(context)

                if next_model and next_model != "__SKIP__":
                    # Retry with the selected model
                    if os.getenv("DEMO_MODE"):
                        print(f"[RETRY] {agent_id} with model: {next_model}")

                    # Recursive call with new model
                    return await self.execute_llm(
                        agent_id=agent_id,
                        task=task,
                        model=next_model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        personality=personality,
                        expertise=expertise
                    )

            # Return fallback response if no retry or user aborted
            return LLMResponse(
                content=f"[{agent_id}] encountered an error but suggests: {task[:50]}...",
                model=model,
                tokens_used=0,
                latency=time.time() - start_time,
                error=error_msg
            )

    def _classify_error(self, exception: Exception) -> str:
        """Classify error type for fallback manager"""
        error_str = str(exception).lower()

        if "rate" in error_str or "429" in error_str or "too many requests" in error_str:
            return "rate_limit"
        elif "timeout" in error_str or "timed out" in error_str:
            return "timeout"
        elif "invalid" in error_str or "not found" in error_str or "400" in error_str:
            return "invalid_model"
        else:
            return "api_error"

    def _build_prompt(self, agent_id: str, task: str, personality: str, expertise: list) -> str:
        """Build prompt for LLM"""

        expertise_str = ", ".join(expertise) if expertise else "general tasks"

        prompt = f"""You are {agent_id}, an AI agent with the following characteristics:

Personality: {personality}
Expertise: {expertise_str}

Your task is: {task}

Please provide a detailed response that:
1. Leverages your specific expertise
2. Provides concrete, actionable insights
3. Considers potential challenges and solutions
4. Maintains your personality and perspective

Response:"""

        return prompt

class MultiAgentLLMOrchestrator:
    """Orchestrator for managing multiple LLM agents"""

    def __init__(self, config: Dict[str, Any], manual_mode: bool = False, strategy_selector=None):
        self.config = config
        self.manual_mode = manual_mode
        self.llm_client = LLMClient(config, manual_mode=manual_mode)
        self.agent_configs = config.get("agents", {})
        self.strategy_selector = strategy_selector  # Optional strategy selector for dynamic model selection

        # Prompt user for fallback strategy BEFORE starting (if manual mode)
        if manual_mode and self.llm_client.fallback_manager:
            self.llm_client.fallback_manager.prompt_initial_strategy()

    @weave.op()
    async def execute_agent_task(self, agent_id: str, task: str) -> str:
        """Execute a task with a specific agent using their configured LLM"""

        # Get agent configuration
        agent_config = self.agent_configs.get(agent_id, {})

        # Select model: use StrategySelector if available, otherwise fallback to default_model
        if self.strategy_selector:
            # Use strategy selector for dynamic model selection
            from agents.strategy_selector import ModelSelectionContext
            context = ModelSelectionContext(
                task_type=agent_id,  # Use agent_id as task type
                task_complexity=0.7,  # Default complexity, could be estimated
                remaining_budget=100.0,  # Could track this
                sensitive_data=False
            )
            model, selection_info = self.strategy_selector.select_model(agent_id, context)
            if os.getenv("DEMO_MODE"):
                print(f"[LLM] {agent_id} using {model} (strategy: {selection_info['strategy_used']})")
        else:
            # Fallback to config default_model (backwards compatible)
            model = agent_config.get("default_model", "qwen/qwen3-coder-plus")

        # Execute with LLM
        response = await self.llm_client.execute_llm(
            agent_id=agent_id,
            task=task,
            model=model,
            temperature=agent_config.get("temperature", 0.7),
            max_tokens=agent_config.get("max_tokens", 2000),
            personality=agent_config.get("personality", ""),
            expertise=agent_config.get("expertise", [])
        )

        if response.error:
            # Log error but return content anyway
            if os.getenv("DEMO_MODE"):
                print(f"[WARN] {agent_id} error: {response.error}")

        return response.content

    async def execute_parallel_agents(self, agents: list, task: str) -> Dict[str, str]:
        """Execute task with multiple agents in parallel"""

        tasks = [
            self.execute_agent_task(agent_id, task)
            for agent_id in agents
        ]

        results = await asyncio.gather(*tasks)

        return {
            agent_id: result
            for agent_id, result in zip(agents, results)
        }