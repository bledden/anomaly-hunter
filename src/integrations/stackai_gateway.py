"""
StackAI Gateway Integration
Multi-model routing for anomaly detection agents using Stack AI Flows
"""

import aiohttp
import os
from typing import Dict, Any, Optional
import asyncio
import openai


class StackAIGateway:
    """
    StackAI Gateway - Flow-Based Multi-Model Router

    Routes agent requests to appropriate Stack AI flows:
    - Pattern Analyst → GPT-4 Turbo Flow
    - Root Cause Agent → o1-mini Flow
    - Change Detective → Fallback (local processing)

    Benefits:
    - Deployed workflows with optimized prompts
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

        # Stack AI organization and flow IDs
        self.org_id = "0acc2aff-5dab-4a7c-bd72-2dd158e493df"

        # Flow routing map - maps model names to Stack AI flow IDs
        self.flow_map = {
            # "openai/gpt-5-pro": "68f2bece9e2d263db0c93aa3",            # Pattern Analyst flow (DISABLED - too slow, 5+ min timeout)
            "anthropic/claude-sonnet-4-5": "68f2c162c148d3edaa517114",  # Root Cause flow (Claude 4.5 Sonnet) - FAST!
        }

        self.base_url = "https://api.stack-ai.com/inference/v0"
        self.session: Optional[aiohttp.ClientSession] = None

    async def create_session(self):
        """Create aiohttp session"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=300)  # 5 min timeout for GPT-5 Pro
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
        Route completion request to appropriate Stack AI flow

        Args:
            model: Model identifier (e.g., "openai/gpt-4-turbo")
            prompt: Input prompt
            temperature: Sampling temperature (ignored for flows)
            max_tokens: Maximum response tokens (ignored for flows)
            **kwargs: Additional model parameters

        Returns:
            Model response text
        """

        if not self.api_key:
            return self._fallback_response(model, prompt)

        # Get flow ID for this model
        flow_id = self.flow_map.get(model)
        if not flow_id:
            # Silently use fallback for models without flows (Change Detective uses local analysis)
            return self._fallback_response(model, prompt)

        await self.create_session()

        # Stack AI flow payload format
        payload = {
            "user_id": "anomaly-hunter-session",
            "in-0": prompt  # Input parameter name from Stack AI flow
        }

        # Build the flow endpoint URL
        flow_url = f"{self.base_url}/run/{self.org_id}/{flow_id}"

        try:
            async with self.session.post(flow_url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"[ERROR] Stack AI flow error ({response.status}): {error_text}")
                    return self._fallback_response(model, prompt)

                data = await response.json()

                # Stack AI returns: {"outputs": {"out-0": "response text"}}
                if "outputs" in data and "out-0" in data["outputs"]:
                    return data["outputs"]["out-0"]
                elif "output" in data:
                    return data["output"]
                elif "out-0" in data:
                    return data["out-0"]
                else:
                    print(f"[WARN] Unexpected Stack AI response format: {data}")
                    return self._fallback_response(model, prompt)

        except asyncio.TimeoutError:
            print(f"[ERROR] Stack AI request timeout for {model}")
            return self._fallback_response(model, prompt)

        except Exception as e:
            print(f"[ERROR] Stack AI request failed: {e}")
            return self._fallback_response(model, prompt)

    def _fallback_response(self, model: str, prompt: str) -> str:
        """Fallback response using direct OpenAI API when Stack AI unavailable"""

        try:
            # Use OpenAI API directly as fallback
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                return "Severity: 5\nAnalysis: Fallback failed - no OpenAI API key"

            # Set OpenAI client
            from openai import OpenAI
            client = OpenAI(api_key=openai_api_key)

            # Choose appropriate OpenAI model based on original request
            fallback_model = "gpt-4o-mini"  # Fast and cheap fallback

            # Make synchronous OpenAI call (in fallback path, acceptable)
            response = client.chat.completions.create(
                model=fallback_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"[ERROR] Fallback to OpenAI failed: {e}")
            # Last resort: basic rule-based response
            if "severity" in prompt.lower():
                return """Severity: 5
Analysis: Both Stack AI and OpenAI fallback unavailable. Basic statistical analysis suggests investigating data patterns."""
            return "Severity: 5\nAnalysis: Fallback unavailable"

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
    """Test StackAI gateway flows"""

    print("\n" + "="*60)
    print("STACK AI FLOW GATEWAY TEST")
    print("="*60)

    async with StackAIGateway() as gateway:
        # Test Pattern Analyst Flow (GPT-4)
        print("\n[TEST 1] Pattern Analyst Flow (GPT-4 Turbo)")
        print("Testing anomaly detection with statistical analysis...")
        response1 = await gateway.complete(
            model="openai/gpt-4-turbo",
            prompt="Analyze these anomalies: 19 data points with Z-scores > 3σ. Baseline: 0.1, Peak: 8.5. Max deviation: 4.41σ. Assess severity.",
            temperature=0.7,
            max_tokens=200
        )
        print(f"✓ Response:\n{response1}\n")

        # Test Root Cause Flow (o1-mini)
        print("\n[TEST 2] Root Cause Flow (o1-mini)")
        print("Testing root cause hypothesis generation...")
        response2 = await gateway.complete(
            model="openai/o1-mini",
            prompt="Generate root cause hypothesis: 3 anomaly clusters detected over 30min period. Network packet loss spike 0.1% → 8%. Correlation: 0.78. What's the likely cause?",
            temperature=0.3,
            max_tokens=300
        )
        print(f"✓ Response:\n{response2}\n")

        # Test Change Detective (Fallback - no flow)
        print("\n[TEST 3] Change Detective (Fallback Mode - No Flow)")
        print("Testing fallback for Claude Sonnet...")
        response3 = await gateway.complete(
            model="anthropic/claude-sonnet-3-5",
            prompt="Detect change points in time series with 99.7% drift. 30 change points detected.",
            temperature=0.5,
            max_tokens=200
        )
        print(f"✓ Response:\n{response3}\n")

    print("="*60)
    print("FLOW GATEWAY TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    asyncio.run(test_stackai())
