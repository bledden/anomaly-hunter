"""
Dynamic Web Search Router
Detects if a task needs external information and routes to appropriate model/tool.
"""

import weave
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re


class SearchStrategy(Enum):
    """Web search strategies based on user preference"""
    CHEAPEST = "cheapest"  # Lowest cost (Tavily API)
    FASTEST = "fastest"  # Lowest latency (Perplexity Sonar)
    HIGHEST_QUALITY = "highest_quality"  # Best results (Perplexity R1)
    BALANCED = "balanced"  # Balance of cost/quality (Gemini 2.5)


@dataclass
class SearchCapability:
    """Model or tool with web search capability"""
    name: str
    provider: str  # "perplexity", "tavily", "google"
    cost_per_search: float  # USD
    avg_latency_ms: float
    quality_score: float  # 0-1 based on benchmarks
    model_id: Optional[str] = None  # If it's a model
    is_tool: bool = False  # True for Tavily API


# Available web search options
SEARCH_CAPABILITIES = {
    "tavily_api": SearchCapability(
        name="Tavily Search API",
        provider="tavily",
        cost_per_search=0.001,  # $0.001 per search
        avg_latency_ms=500,
        quality_score=0.85,
        is_tool=True
    ),
    "perplexity_r1": SearchCapability(
        name="Perplexity R1",
        provider="perplexity",
        cost_per_search=0.015,  # ~$0.015 per query (estimate)
        avg_latency_ms=2000,
        quality_score=0.95,
        model_id="perplexity/r1"
    ),
    "perplexity_sonar": SearchCapability(
        name="Perplexity Sonar Online",
        provider="perplexity",
        cost_per_search=0.005,  # ~$0.005 per query
        avg_latency_ms=1200,
        quality_score=0.88,
        model_id="perplexity/llama-3.1-sonar-large-128k-online"
    ),
    "gemini_2.5_pro": SearchCapability(
        name="Gemini 2.5 Pro (w/ search)",
        provider="google",
        cost_per_search=0.010,  # ~$0.010 per query
        avg_latency_ms=1800,
        quality_score=0.90,
        model_id="google/gemini-2.5-pro-exp"
    )
}


class WebSearchRouter:
    """Routes tasks to appropriate web search model/tool based on user preference"""

    # Patterns indicating need for external information
    EXTERNAL_INFO_INDICATORS = [
        # Time-sensitive
        r"latest|current|recent|2024|2025|new|updated|modern",
        r"best practices? \d{4}",

        # Version-specific
        r"version \d+\.?\d*",
        r"v\d+\.?\d*",
        r"\d+\.x",

        # Framework/library specific
        r"next\.?js \d+",
        r"react \d+",
        r"python \d\.\d+",
        r"node\.?js \d+",

        # Security
        r"CVE-\d{4}-\d+",
        r"vulnerability|exploit|patch|security update",

        # Documentation/API
        r"api documentation|api reference",
        r"how to use .+ api",
        r"integration guide",

        # Comparison/Research
        r"compare .+ with",
        r"which .+ is better",
        r"benchmark .+ vs",
        r"performance comparison",

        # Troubleshooting
        r"fix .+ error",
        r"resolve .+ issue",
        r"why .+ not working",

        # Current state
        r"current .+ implementation",
        r"production-ready",
        r"industry standard",
    ]

    def __init__(self, default_strategy: SearchStrategy = SearchStrategy.BALANCED):
        self.default_strategy = default_strategy
        self.search_count = 0
        self.total_cost = 0.0

    @weave.op()
    def detect_needs_web_search(self, task: str) -> Tuple[bool, List[str], float]:
        """
        Detect if task needs web search.

        Returns:
            (needs_search, matched_patterns, confidence)
        """
        task_lower = task.lower()

        matched_patterns = []
        for pattern in self.EXTERNAL_INFO_INDICATORS:
            if re.search(pattern, task_lower):
                matched_patterns.append(pattern)

        # Confidence based on number of matches
        confidence = min(len(matched_patterns) * 0.25, 1.0)
        needs_search = confidence > 0.5

        return needs_search, matched_patterns, confidence

    @weave.op()
    def select_search_method(
        self,
        strategy: Optional[SearchStrategy] = None,
        budget_usd: Optional[float] = None
    ) -> SearchCapability:
        """
        Select optimal web search method based on strategy.

        Args:
            strategy: User preference (cheapest, fastest, highest_quality, balanced)
            budget_usd: Maximum budget per search (optional constraint)

        Returns:
            SearchCapability with selected method
        """
        strategy = strategy or self.default_strategy

        # Filter by budget if specified
        options = SEARCH_CAPABILITIES.values()
        if budget_usd:
            options = [o for o in options if o.cost_per_search <= budget_usd]

        if not options:
            raise ValueError(f"No search options within budget ${budget_usd}")

        # Select based on strategy
        if strategy == SearchStrategy.CHEAPEST:
            selected = min(options, key=lambda x: x.cost_per_search)

        elif strategy == SearchStrategy.FASTEST:
            selected = min(options, key=lambda x: x.avg_latency_ms)

        elif strategy == SearchStrategy.HIGHEST_QUALITY:
            selected = max(options, key=lambda x: x.quality_score)

        elif strategy == SearchStrategy.BALANCED:
            # Balanced: normalize and combine metrics
            # Lower cost = better, lower latency = better, higher quality = better
            scored = []
            for opt in options:
                # Normalize to 0-1 (invert for cost/latency)
                cost_score = 1 - (opt.cost_per_search / max(o.cost_per_search for o in options))
                latency_score = 1 - (opt.avg_latency_ms / max(o.avg_latency_ms for o in options))
                quality_score = opt.quality_score

                # Weighted average: quality 50%, cost 30%, latency 20%
                combined = (quality_score * 0.5 + cost_score * 0.3 + latency_score * 0.2)
                scored.append((opt, combined))

            selected = max(scored, key=lambda x: x[1])[0]

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        self.search_count += 1
        self.total_cost += selected.cost_per_search

        return selected

    @weave.op()
    async def route_task(
        self,
        task: str,
        strategy: Optional[SearchStrategy] = None,
        budget_usd: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Route task to appropriate handler.

        Returns:
            {
                "needs_search": bool,
                "confidence": float,
                "matched_patterns": List[str],
                "search_method": SearchCapability (if needs search),
                "reasoning": str
            }
        """
        needs_search, patterns, confidence = self.detect_needs_web_search(task)

        result = {
            "needs_search": needs_search,
            "confidence": confidence,
            "matched_patterns": patterns,
            "task": task
        }

        if needs_search:
            search_method = self.select_search_method(strategy, budget_usd)
            result["search_method"] = search_method
            result["reasoning"] = (
                f"Task matches {len(patterns)} external info indicators. "
                f"Routing to {search_method.name} "
                f"(${search_method.cost_per_search:.4f}, "
                f"{search_method.avg_latency_ms}ms, "
                f"quality={search_method.quality_score:.2f})"
            )
        else:
            result["reasoning"] = (
                f"Task appears self-contained (confidence={confidence:.2f}). "
                f"No external information needed - routing to standard model."
            )

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            "total_searches": self.search_count,
            "total_cost_usd": self.total_cost,
            "avg_cost_per_search": self.total_cost / max(self.search_count, 1)
        }


# Example usage
async def demo():
    """Demonstrate web search routing"""
    import asyncio

    router = WebSearchRouter(default_strategy=SearchStrategy.BALANCED)

    test_tasks = [
        # Self-contained (no search needed)
        "Implement binary search on a sorted array",
        "Write a function to reverse a linked list",

        # Needs search
        "Create a Next.js 14 server action using useFormStatus",
        "Fix CVE-2021-44228 log4j vulnerability",
        "Compare React 18 vs React 19 performance",
        "How to use TanStack Query v5 with Vite 5",
        "What are the latest best practices for FastAPI 2024?",
    ]

    print("=" * 80)
    print("WEB SEARCH ROUTING DEMO")
    print("=" * 80)

    for task in test_tasks:
        print(f"\nDocumenter Task: {task}")
        result = await router.route_task(task, strategy=SearchStrategy.BALANCED)

        if result["needs_search"]:
            method = result["search_method"]
            print(f"   [OK] NEEDS SEARCH (confidence: {result['confidence']:.2f})")
            print(f"   → Routing to: {method.name}")
            print(f"   → Cost: ${method.cost_per_search:.4f}")
            print(f"   → Latency: {method.avg_latency_ms}ms")
            print(f"   → Quality: {method.quality_score:.2f}")
            print(f"   → Matched: {', '.join(result['matched_patterns'][:3])}")
        else:
            print(f"   [FAIL] NO SEARCH NEEDED (confidence: {result['confidence']:.2f})")
            print(f"   → Using standard model")

    print("\n" + "=" * 80)
    print("ROUTING STATISTICS")
    print("=" * 80)
    stats = router.get_stats()
    print(f"Total searches: {stats['total_searches']}")
    print(f"Total cost: ${stats['total_cost_usd']:.4f}")
    print(f"Avg cost/search: ${stats['avg_cost_per_search']:.4f}")


if __name__ == "__main__":
    import asyncio
    weave.init("facilitair/web-search-router-demo")
    asyncio.run(demo())
