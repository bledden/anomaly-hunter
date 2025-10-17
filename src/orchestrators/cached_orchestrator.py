"""
Cached Streaming Orchestrator
Integrates semantic cache with collaborative orchestration
"""

import asyncio
from typing import Dict, Any, AsyncGenerator, Optional
from datetime import datetime

from src.orchestrators.collaborative_orchestrator import CollaborativeOrchestrator, CollaborationResult
from src.caching.semantic_cache import ContextAwareSemanticCache, CacheEntry


class CachedStreamingOrchestrator:
    """
    Orchestrator with semantic caching

    Flow:
    1. Check cache for similar task + context
    2. If hit: Stream cached result (with realistic pacing)
    3. If miss: Run real collaboration, then cache result
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        redis_url: str = "redis://localhost:6379/0",
        cache_enabled: bool = True
    ):
        """
        Initialize cached orchestrator

        Args:
            config: Orchestrator configuration
            redis_url: Redis connection URL
            cache_enabled: Enable/disable caching
        """
        self.orchestrator = CollaborativeOrchestrator(config, use_sequential=True)
        self.cache = ContextAwareSemanticCache(redis_url=redis_url)
        self.cache_enabled = cache_enabled

    async def collaborate(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CollaborationResult:
        """
        Execute collaborative task with caching

        Args:
            task: Task description
            context: User context for cache matching

        Returns:
            CollaborationResult
        """
        context = context or {}

        # Try cache first (if enabled)
        if self.cache_enabled:
            cached_entry = await self.cache.get(task, context)

            if cached_entry:
                print(f"[CACHE] Cache hit! (similarity > {self.cache.similarity_threshold})")
                print(f"   Cached: {self._format_time_ago(cached_entry.cached_at)}")
                print(f"   Context: {self._format_context(cached_entry.context)}\n")

                # Return cached result as CollaborationResult
                return CollaborationResult(
                    task=task,
                    agents_used=cached_entry.metadata.get("agents_used", []),
                    consensus_method="cached",
                    individual_outputs={},
                    final_output=cached_entry.result,
                    metrics={
                        "quality": cached_entry.metadata.get("quality", 0.9),
                        "cached": True,
                        "cache_age_hours": (datetime.now().timestamp() - cached_entry.cached_at) / 3600
                    },
                    conflicts_resolved=0,
                    consensus_rounds=0
                )

        # Cache miss - run real collaboration
        print("[REVW] Cache miss - starting collaborative session...\n")

        result = await self.orchestrator.collaborate(task)

        # Cache the result
        if self.cache_enabled and result.final_output:
            await self.cache.set(
                task,
                context,
                result.final_output,
                metadata={
                    "agents_used": result.agents_used,
                    "quality": result.metrics.get("quality", 0.0),
                    "duration": result.metrics.get("duration", 0.0)
                }
            )
            print("\n[CACHE] Result cached for future use")

        return result

    async def stream_collaborate(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream collaborative task with caching

        Yields streaming events for CLI/Web UI

        Args:
            task: Task description
            context: User context

        Yields:
            Event dictionaries with type, content, timestamp
        """
        context = context or {}

        # Try cache first
        if self.cache_enabled:
            cached_entry = await self.cache.get(task, context)

            if cached_entry:
                # Stream cached result with realistic pacing
                async for event in self._stream_cached_result(cached_entry):
                    yield event
                return

        # Cache miss - stream real collaboration
        yield {
            "type": "cache_miss",
            "message": "No cached solution found",
            "timestamp": datetime.now().isoformat()
        }

        # Run real collaboration and stream results
        result = await self.orchestrator.collaborate(task)

        # Stream the result
        yield {
            "type": "collaboration_complete",
            "result": result.final_output,
            "agents_used": result.agents_used,
            "metrics": result.metrics,
            "timestamp": datetime.now().isoformat()
        }

        # Cache for future
        if self.cache_enabled and result.final_output:
            await self.cache.set(
                task,
                context,
                result.final_output,
                metadata={
                    "agents_used": result.agents_used,
                    "quality": result.metrics.get("quality", 0.0)
                }
            )

            yield {
                "type": "cached",
                "message": "Result cached for future use",
                "timestamp": datetime.now().isoformat()
            }

    async def _stream_cached_result(
        self,
        cached_entry: CacheEntry
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a cached result with realistic pacing

        This makes cached results feel "live" rather than instant
        """
        # Announce cache hit
        yield {
            "type": "cache_hit",
            "message": f"Found similar solution (cached {self._format_time_ago(cached_entry.cached_at)})",
            "similarity": "> 92%",
            "context": cached_entry.context,
            "timestamp": datetime.now().isoformat()
        }

        await asyncio.sleep(0.3)

        # Stream result in chunks (simulating real-time generation)
        result_text = cached_entry.result
        chunk_size = 100  # Characters per chunk

        for i in range(0, len(result_text), chunk_size):
            chunk = result_text[i:i + chunk_size]

            yield {
                "type": "output_chunk",
                "content": chunk,
                "is_cached": True,
                "timestamp": datetime.now().isoformat()
            }

            # Realistic pacing (50-100ms per chunk)
            await asyncio.sleep(0.05 + (len(chunk) / 2000))

        # Final event
        yield {
            "type": "complete",
            "cached": True,
            "metadata": cached_entry.metadata,
            "timestamp": datetime.now().isoformat()
        }

    def _format_time_ago(self, timestamp: float) -> str:
        """Format timestamp as human-readable 'time ago'"""
        seconds_ago = datetime.now().timestamp() - timestamp

        if seconds_ago < 60:
            return "just now"
        elif seconds_ago < 3600:
            minutes = int(seconds_ago / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds_ago < 86400:
            hours = int(seconds_ago / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(seconds_ago / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for display"""
        parts = []

        if context.get("preferred_language"):
            parts.append(context["preferred_language"])

        if context.get("frameworks"):
            parts.append(", ".join(context["frameworks"]))

        if context.get("security_level"):
            parts.append(context["security_level"])

        return ", ".join(parts) if parts else "default"

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_stats()

    async def close(self):
        """Close connections"""
        await self.cache.close()


# Demo
async def demo_cached_orchestrator():
    """Demonstrate cached orchestrator"""
    orchestrator = CachedStreamingOrchestrator()

    print("=== Cached Orchestrator Demo ===\n")

    # Context for a Python startup
    python_context = {
        "preferred_language": "python",
        "frameworks": ["fastapi"],
        "security_level": "standard",
        "team_size": "small"
    }

    # First request (cache miss)
    print("First request: Build authentication API\n")
    result1 = await orchestrator.collaborate(
        "Build a user authentication API with JWT",
        python_context
    )
    print(f"Result: {result1.final_output[:100]}...")
    print(f"Cached: {result1.metrics.get('cached', False)}\n")

    # Second request (cache hit - same task, same context)
    print("\nSecond request: Same task, same context\n")
    result2 = await orchestrator.collaborate(
        "Build a user authentication API with JWT",
        python_context
    )
    print(f"Result: {result2.final_output[:100]}...")
    print(f"Cached: {result2.metrics.get('cached', False)}\n")

    # Third request (cache miss - different context)
    java_context = {
        "preferred_language": "java",
        "frameworks": ["spring"],
        "security_level": "enterprise",
        "team_size": "large"
    }

    print("\nThird request: Same task, different context\n")
    result3 = await orchestrator.collaborate(
        "Build a user authentication API with JWT",
        java_context
    )
    print(f"Result: {result3.final_output[:100]}...")
    print(f"Cached: {result3.metrics.get('cached', False)}\n")

    # Show cache stats
    print("\nCache Statistics:")
    stats = await orchestrator.get_cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(demo_cached_orchestrator())
