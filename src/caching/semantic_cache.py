"""
Context-Aware Semantic Cache
Caches collaboration results based on task similarity AND context
"""

import asyncio
import hashlib
import json
import time
from typing import Optional, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import redis.asyncio as redis
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Cached collaboration result"""
    task: str
    context: Dict[str, Any]
    result: str
    embedding: bytes
    metadata: Dict[str, Any]
    cached_at: float


class ContextAwareSemanticCache:
    """
    Semantic cache with context awareness

    Key Features:
    - Same query, different context = different cache entry
    - Cosine similarity matching with high threshold (0.92)
    - 7-day TTL for entries
    - Efficient embedding computation
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.92
    ):
        """
        Initialize semantic cache

        Args:
            redis_url: Redis connection URL
            model_name: SentenceTransformer model for embeddings
            similarity_threshold: Minimum cosine similarity for cache hit (0.0-1.0)
        """
        self.model = SentenceTransformer(model_name)
        self.redis_url = redis_url
        self.redis_client = None
        self.similarity_threshold = similarity_threshold

        # Cache stats
        self.hits = 0
        self.misses = 0

    async def connect(self):
        """Connect to Redis"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(self.redis_url)

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

    def _canonicalize_context(self, context: Dict[str, Any]) -> str:
        """
        Canonicalize context for consistent cache keys

        Context includes:
        - User preferences (language, framework)
        - Organization requirements (security level, compliance)
        - Historical choices (past tech stack)
        """
        canonical = {
            "language": context.get("preferred_language", "any"),
            "frameworks": sorted(context.get("frameworks", [])),
            "security_level": context.get("security_level", "standard"),
            "compliance": sorted(context.get("compliance", [])),
            "team_size": context.get("team_size", "small"),
            "existing_stack": sorted(context.get("existing_stack", [])),
        }

        return json.dumps(canonical, sort_keys=True)

    def _create_embedding(self, task: str, context: Dict[str, Any]) -> np.ndarray:
        """
        Create embedding for task + context

        Format: "TASK |CONTEXT| {canonical_context}"
        This ensures similar tasks with different contexts get different embeddings
        """
        context_str = self._canonicalize_context(context)
        combined = f"{task} |CONTEXT| {context_str}"

        embedding = self.model.encode(combined)
        return embedding

    def _calculate_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        return np.dot(emb1, emb2) / (
            np.linalg.norm(emb1) * np.linalg.norm(emb2)
        )

    async def get(
        self,
        task: str,
        context: Dict[str, Any]
    ) -> Optional[CacheEntry]:
        """
        Check cache for similar task with similar context

        Returns:
            CacheEntry if found with similarity > threshold, None otherwise
        """
        await self.connect()

        # Create query embedding
        query_embedding = self._create_embedding(task, context)

        # Get all cached items
        # In production, use a vector database (Pinecone, Weaviate, etc.)
        # For now, we scan all keys (fine for <10k entries)
        keys = await self.redis_client.keys("cache:*")

        best_match = None
        best_similarity = 0.0

        for key in keys:
            cached_data_str = await self.redis_client.get(key)
            if not cached_data_str:
                continue

            cached_data = json.loads(cached_data_str)

            # Reconstruct embedding from hex string
            cached_embedding = np.frombuffer(
                bytes.fromhex(cached_data["embedding"]),
                dtype=np.float32
            )

            # Calculate similarity
            similarity = self._calculate_similarity(query_embedding, cached_embedding)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = cached_data

        # Check if best match exceeds threshold
        if best_similarity > self.similarity_threshold:
            self.hits += 1
            return CacheEntry(
                task=best_match["task"],
                context=best_match["context"],
                result=best_match["result"],
                embedding=bytes.fromhex(best_match["embedding"]),
                metadata=best_match["metadata"],
                cached_at=best_match["cached_at"]
            )

        self.misses += 1
        return None

    async def set(
        self,
        task: str,
        context: Dict[str, Any],
        result: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Cache result with context embedding

        Args:
            task: Original task description
            context: Context dictionary
            result: Collaboration result to cache
            metadata: Optional metadata (agents used, duration, etc.)
        """
        await self.connect()

        # Create embedding
        embedding = self._create_embedding(task, context)

        # Create cache key (hash of embedding)
        cache_key = f"cache:{hashlib.sha256(embedding.tobytes()).hexdigest()}"

        # Prepare cache entry
        cache_entry = {
            "task": task,
            "context": context,
            "result": result,
            "embedding": embedding.tobytes().hex(),
            "metadata": metadata or {},
            "cached_at": time.time()
        }

        # Store in Redis with 7-day TTL
        await self.redis_client.setex(
            cache_key,
            60 * 60 * 24 * 7,  # 7 days
            json.dumps(cache_entry)
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0.0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate": f"{hit_rate:.1f}%"
        }

    async def clear(self):
        """Clear all cache entries"""
        await self.connect()
        keys = await self.redis_client.keys("cache:*")
        if keys:
            await self.redis_client.delete(*keys)


# Demo/Test
async def demo_semantic_cache():
    """Demonstrate semantic cache functionality"""
    cache = ContextAwareSemanticCache()

    print("=== Semantic Cache Demo ===\n")

    # Scenario 1: Same task, same context (should hit cache)
    print("Scenario 1: Exact match")
    context1 = {
        "preferred_language": "python",
        "frameworks": ["fastapi"],
        "security_level": "standard"
    }

    # First request (cache miss)
    result1 = await cache.get("Build a REST API", context1)
    print(f"  First request: {result1}")  # None

    # Cache the result
    await cache.set(
        "Build a REST API",
        context1,
        "Here's a FastAPI implementation...",
        metadata={"agents_used": ["architect", "coder", "reviewer"]}
    )

    # Second request (cache hit)
    result2 = await cache.get("Build a REST API", context1)
    print(f"  Second request: {result2.result if result2 else None}")  # Hit!

    print()

    # Scenario 2: Similar task, different context (should miss)
    print("Scenario 2: Different context")
    context2 = {
        "preferred_language": "java",
        "frameworks": ["spring"],
        "security_level": "enterprise"
    }

    result3 = await cache.get("Build a REST API", context2)
    print(f"  Result: {result3}")  # None (different context)

    print()

    # Scenario 3: Slightly different wording, same context (might hit)
    print("Scenario 3: Similar wording")
    result4 = await cache.get("Create a RESTful API", context1)
    print(f"  Result: {result4.result if result4 else None}")  # Might hit!

    print()

    # Stats
    print("Cache Statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    await cache.close()


if __name__ == "__main__":
    asyncio.run(demo_semantic_cache())
