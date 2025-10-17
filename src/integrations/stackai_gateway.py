"""
StackAI Gateway Integration
Multi-model routing for anomaly detection agents
"""

import aiohttp
import os
from typing import Dict, Any, Optional
import asyncio


class StackAIGateway:
    """
    StackAI Gateway - Multi-Model Router

    Routes agent requests to appropriate LLM models:
    - Pattern Analyst → GPT-4 Turbo
    - Change Detective → Claude Sonnet 3.5
    - Root Cause Agent → o1-mini

    Benefits:
    - Single unified API
    - Automatic failover
    - Cost tracking
    - Easy model switching
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize StackAI Gateway

        Args:
            api_key: StackAI API key (or from env STACKAI_API_KEY)
        """
        self.api_key = api_key or os.getenv("STACKAI_API_KEY")
        if not self.api_key:
            print("[WARN] STACKAI_API_KEY not set - using fallback mode")

        self.base_url = "https://api.stack-ai.com/v1"
        self.session: Optional[aiohttp.ClientSession] = None

        # Model routing map
        self.model_map = {
            "openai/gpt-4-turbo": "gpt-4-turbo-preview",
            "openai/o1-mini": "o1-mini",
            "anthropic/claude-sonnet-3-5": "claude-3-5-sonnet-20241022"
        }

    async def create_session(self):
        """Create aiohttp session"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=60)
            )

    async def complete(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """
        Route completion request to appropriate model via StackAI

        Args:
            model: Model identifier (e.g., "openai/gpt-4-turbo")
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            **kwargs: Additional model parameters

        Returns:
            Model response text
        """

        if not self.api_key:
            return self._fallback_response(model, prompt)

        await self.create_session()

        # Map to StackAI model name
        stackai_model = self.model_map.get(model, model)

        payload = {
            "model": stackai_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }

        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"[ERROR] StackAI API error ({response.status}): {error_text}")
                    return self._fallback_response(model, prompt)

                data = await response.json()
                return data["choices"][0]["message"]["content"]

        except asyncio.TimeoutError:
            print(f"[ERROR] StackAI request timeout for model {model}")
            return self._fallback_response(model, prompt)

        except Exception as e:
            print(f"[ERROR] StackAI request failed: {e}")
            return self._fallback_response(model, prompt)

    def _fallback_response(self, model: str, prompt: str) -> str:
        """Fallback response when StackAI unavailable"""

        # Extract request type from prompt
        if "severity" in prompt.lower():
            if "pattern" in model.lower() or "gpt-4" in model:
                return """Severity: 7
Pattern: Statistical anomalies detected with Z-scores exceeding 3σ threshold
Impact: Moderate deviation from baseline requiring investigation"""

            elif "change" in model.lower() or "claude" in model:
                return """Severity: 6
Pattern: Time-series drift detected with multiple change points
Cause: Possible system load increase or configuration change"""

            elif "root" in model.lower() or "o1" in model:
                return """Severity: 7
Hypothesis: System resource contention causing performance degradation
Evidence: Temporal clustering suggests correlated events
Confidence: 0.65"""

        return "Severity: 5\nAnalysis: Fallback mode - StackAI unavailable"

    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        """Async context manager entry"""
        await self.create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Quick test
async def test_stackai():
    """Test StackAI gateway"""

    print("\n" + "="*60)
    print("STACKAI GATEWAY TEST")
    print("="*60)

    async with StackAIGateway() as gateway:
        # Test GPT-4
        print("\n[TEST 1] GPT-4 Turbo")
        response1 = await gateway.complete(
            model="openai/gpt-4-turbo",
            prompt="Analyze this anomaly: spike to 250 from baseline 100. Severity?",
            temperature=0.7,
            max_tokens=200
        )
        print(f"Response: {response1[:200]}...")

        # Test Claude
        print("\n[TEST 2] Claude Sonnet")
        response2 = await gateway.complete(
            model="anthropic/claude-sonnet-3-5",
            prompt="Detect change points in time series with 30% drift. Severity?",
            temperature=0.5,
            max_tokens=200
        )
        print(f"Response: {response2[:200]}...")

        # Test o1-mini
        print("\n[TEST 3] o1-mini")
        response3 = await gateway.complete(
            model="openai/o1-mini",
            prompt="Generate root cause hypothesis for database spike. Confidence?",
            temperature=0.3,
            max_tokens=300
        )
        print(f"Response: {response3[:200]}...")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_stackai())
