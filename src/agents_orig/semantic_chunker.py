"""
Semantic Chunking for Intelligent Task Decomposition
Breaks complex requests into semantically coherent chunks for optimal processing
"""

import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import weave


@dataclass
class SemanticChunk:
    """A semantically coherent piece of a larger task"""
    id: str
    content: str
    chunk_type: str  # code, explanation, test, config, etc.
    language: str
    dependencies: List[str]  # IDs of chunks this depends on
    optimal_model: str
    estimated_tokens: int
    priority: int


class IntelligentSemanticChunker:
    """
    Breaks down complex requests into optimal chunks for processing
    This is WHERE the real intelligence happens
    """

    def __init__(self):
        self.chunk_patterns = self._init_patterns()

    def _init_patterns(self):
        """Initialize patterns for different chunk types"""
        return {
            "implementation": {
                "pattern": r"(?:implement|create|build|write|develop)\s+(.+?)(?:\.|$|\n)",
                "chunk_type": "code"
            },
            "testing": {
                "pattern": r"(?:test|verify|validate|check)\s+(.+?)(?:\.|$|\n)",
                "chunk_type": "test"
            },
            "documentation": {
                "pattern": r"(?:document|explain|describe|comment)\s+(.+?)(?:\.|$|\n)",
                "chunk_type": "docs"
            },
            "configuration": {
                "pattern": r"(?:configure|setup|deploy|install)\s+(.+?)(?:\.|$|\n)",
                "chunk_type": "config"
            },
            "optimization": {
                "pattern": r"(?:optimize|improve|refactor|enhance)\s+(.+?)(?:\.|$|\n)",
                "chunk_type": "optimization"
            }
        }

    @weave.op()
    def chunk_request(self, request: str) -> List[SemanticChunk]:
        """
        Intelligently chunk a complex request into semantic pieces

        Example:
        "Build a REST API with user authentication, add tests,
         document the endpoints, and deploy to AWS"

        Becomes:
        1. Chunk: "Build REST API" → Claude-3.5 (good at FastAPI)
        2. Chunk: "User authentication" → GPT-4 (security expertise)
        3. Chunk: "Add tests" → DeepSeek (testing patterns)
        4. Chunk: "Document endpoints" → Claude-Haiku (fast docs)
        5. Chunk: "Deploy to AWS" → GPT-4 (AWS knowledge)
        """

        chunks = []
        chunk_id = 0

        # Split by natural boundaries
        segments = self._split_by_boundaries(request)

        for segment in segments:
            # Analyze segment semantics
            chunk_type = self._identify_chunk_type(segment)
            language = self._detect_language(segment)

            # Determine optimal processing
            optimal_model = self._select_optimal_model_for_chunk(
                chunk_type, language, segment
            )

            # Create chunk
            chunk = SemanticChunk(
                id=f"chunk_{chunk_id}",
                content=segment,
                chunk_type=chunk_type,
                language=language,
                dependencies=self._identify_dependencies(segment, chunks),
                optimal_model=optimal_model,
                estimated_tokens=len(segment.split()) * 1.3,
                priority=self._calculate_priority(chunk_type, segment)
            )

            chunks.append(chunk)
            chunk_id += 1

        # Reorder by dependencies and priority
        chunks = self._optimize_chunk_order(chunks)

        weave.log({
            "semantic_chunking": {
                "original_request_length": len(request),
                "num_chunks": len(chunks),
                "chunk_types": [c.chunk_type for c in chunks],
                "models_selected": [c.optimal_model for c in chunks]
            }
        })

        return chunks

    def _split_by_boundaries(self, text: str) -> List[str]:
        """Split text by natural semantic boundaries"""

        # First, try to split by explicit markers
        if " and " in text.lower():
            segments = re.split(r'\s+and\s+', text, flags=re.IGNORECASE)
        elif "," in text:
            segments = [s.strip() for s in text.split(",")]
        elif "." in text:
            segments = [s.strip() for s in text.split(".") if s.strip()]
        else:
            # Fall back to newlines or treat as single segment
            segments = [s.strip() for s in text.split("\n") if s.strip()]
            if not segments:
                segments = [text]

        # Further split long segments
        refined_segments = []
        for segment in segments:
            if len(segment.split()) > 50:
                # Long segment, try to split further
                sub_segments = self._split_long_segment(segment)
                refined_segments.extend(sub_segments)
            else:
                refined_segments.append(segment)

        return refined_segments

    def _split_long_segment(self, segment: str) -> List[str]:
        """Split a long segment into smaller semantic chunks"""

        # Look for code blocks
        code_blocks = re.findall(r'```[\s\S]*?```', segment)
        if code_blocks:
            parts = []
            remaining = segment
            for block in code_blocks:
                before, after = remaining.split(block, 1)
                if before.strip():
                    parts.append(before.strip())
                parts.append(block)
                remaining = after
            if remaining.strip():
                parts.append(remaining.strip())
            return parts

        # Look for function/class definitions
        if "def " in segment or "class " in segment:
            lines = segment.split("\n")
            chunks = []
            current_chunk = []

            for line in lines:
                if line.strip().startswith(("def ", "class ")):
                    if current_chunk:
                        chunks.append("\n".join(current_chunk))
                    current_chunk = [line]
                else:
                    current_chunk.append(line)

            if current_chunk:
                chunks.append("\n".join(current_chunk))

            return chunks if chunks else [segment]

        # Default: split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', segment)
        if len(sentences) > 3:
            # Group sentences into chunks of ~3
            chunks = []
            for i in range(0, len(sentences), 3):
                chunk = " ".join(sentences[i:i+3])
                chunks.append(chunk)
            return chunks

        return [segment]

    def _identify_chunk_type(self, segment: str) -> str:
        """Identify the semantic type of a chunk"""

        segment_lower = segment.lower()

        # Check for code blocks
        if "```" in segment or "def " in segment or "class " in segment:
            return "code"

        # Check patterns
        for pattern_name, pattern_info in self.chunk_patterns.items():
            if re.search(pattern_info["pattern"], segment_lower):
                return pattern_info["chunk_type"]

        # Check for specific keywords
        if any(word in segment_lower for word in ["api", "endpoint", "route", "controller"]):
            return "code"
        elif any(word in segment_lower for word in ["test", "assert", "expect", "mock"]):
            return "test"
        elif any(word in segment_lower for word in ["document", "readme", "comment"]):
            return "docs"
        elif any(word in segment_lower for word in ["deploy", "docker", "kubernetes", "aws"]):
            return "config"

        return "general"

    def _detect_language(self, segment: str) -> str:
        """Detect programming language in segment"""

        # Look for explicit language markers
        if "```python" in segment or "import " in segment or "def " in segment:
            return "python"
        elif "```javascript" in segment or "const " in segment or "=>" in segment:
            return "javascript"
        elif "```typescript" in segment or ": string" in segment or ": number" in segment:
            return "typescript"
        elif "```rust" in segment or "fn " in segment or "mut " in segment:
            return "rust"
        elif "```go" in segment or "func " in segment or "package " in segment:
            return "go"
        elif "```java" in segment or "public class" in segment:
            return "java"
        elif "```sql" in segment or "SELECT " in segment.upper():
            return "sql"

        # Look for framework clues
        segment_lower = segment.lower()
        if "react" in segment_lower or "jsx" in segment_lower:
            return "javascript"
        elif "fastapi" in segment_lower or "django" in segment_lower:
            return "python"

        return "general"

    def _select_optimal_model_for_chunk(
        self,
        chunk_type: str,
        language: str,
        content: str
    ) -> str:
        """Select the best model for a specific chunk"""

        # Model selection based on chunk characteristics
        model_matrix = {
            ("code", "python"): "claude-3.5-sonnet-20241022",
            ("code", "javascript"): "gpt-4-turbo-2025-01",
            ("code", "typescript"): "gpt-4-turbo-2025-01",
            ("code", "rust"): "qwen-2.5-coder",
            ("code", "go"): "deepseek-coder-v2",
            ("code", "cpp"): "deepseek-coder-v2",

            ("test", "python"): "claude-3.5-sonnet-20241022",
            ("test", "javascript"): "gpt-4-turbo-2025-01",

            ("docs", "general"): "claude-3-haiku-20240307",  # Fast for docs
            ("docs", "python"): "claude-3-haiku-20240307",

            ("config", "general"): "gpt-4-turbo-2025-01",  # Best for DevOps
            ("optimization", "general"): "deepseek-coder-v2",

            ("general", "general"): "gpt-4-turbo-2025-01"
        }

        # Look up optimal model
        key = (chunk_type, language)
        if key in model_matrix:
            return model_matrix[key]

        # Fallback to type-only matching
        type_key = (chunk_type, "general")
        if type_key in model_matrix:
            return model_matrix[type_key]

        return "gpt-4-turbo-2025-01"  # Default

    def _identify_dependencies(
        self,
        segment: str,
        existing_chunks: List[SemanticChunk]
    ) -> List[str]:
        """Identify which chunks this segment depends on"""

        dependencies = []

        # Look for references to previous chunks
        for chunk in existing_chunks:
            # Check if this segment references something from a previous chunk
            if chunk.chunk_type == "code":
                # Look for function/class names from code chunks
                if "test" in segment.lower() and "test" not in chunk.content:
                    # Tests depend on code
                    dependencies.append(chunk.id)
                elif "document" in segment.lower() and chunk.chunk_type == "code":
                    # Docs depend on code
                    dependencies.append(chunk.id)

        return dependencies

    def _calculate_priority(self, chunk_type: str, segment: str) -> int:
        """Calculate processing priority for a chunk"""

        # Priority order (lower number = higher priority)
        priority_map = {
            "code": 1,  # Code first
            "config": 2,  # Configuration second
            "test": 3,  # Tests after code
            "docs": 4,  # Documentation last
            "optimization": 2,  # Optimization early
            "general": 5
        }

        base_priority = priority_map.get(chunk_type, 5)

        # Adjust based on keywords
        if any(word in segment.lower() for word in ["critical", "urgent", "important"]):
            base_priority -= 1

        return max(1, base_priority)

    def _optimize_chunk_order(self, chunks: List[SemanticChunk]) -> List[SemanticChunk]:
        """Reorder chunks based on dependencies and priority"""

        # Simple topological sort based on dependencies
        ordered = []
        remaining = chunks.copy()

        while remaining:
            # Find chunks with no unmet dependencies
            ready = []
            for chunk in remaining:
                if all(dep in [c.id for c in ordered] for dep in chunk.dependencies):
                    ready.append(chunk)

            if not ready:
                # Circular dependency or error, just add remaining
                ordered.extend(remaining)
                break

            # Sort ready chunks by priority
            ready.sort(key=lambda x: x.priority)

            # Add highest priority ready chunk
            next_chunk = ready[0]
            ordered.append(next_chunk)
            remaining.remove(next_chunk)

        return ordered


class ChunkedOrchestrator:
    """
    Orchestrator that processes semantically chunked requests
    """

    def __init__(self):
        self.chunker = IntelligentSemanticChunker()

    @weave.op()
    async def process_chunked_request(self, request: str) -> Dict[str, Any]:
        """Process a request using semantic chunking"""

        # Chunk the request
        chunks = self.chunker.chunk_request(request)

        # Process each chunk with its optimal model
        results = []
        for chunk in chunks:
            result = await self._process_chunk(chunk)
            results.append(result)

        # Combine results
        combined = self._combine_chunk_results(results)

        return {
            "chunks_processed": len(chunks),
            "models_used": list(set(c.optimal_model for c in chunks)),
            "result": combined
        }

    async def _process_chunk(self, chunk: SemanticChunk) -> Dict[str, Any]:
        """Process a single chunk with its optimal model"""

        # This would call the actual model
        # For now, return mock result
        return {
            "chunk_id": chunk.id,
            "model": chunk.optimal_model,
            "output": f"Processed {chunk.chunk_type} with {chunk.optimal_model}"
        }

    def _combine_chunk_results(self, results: List[Dict]) -> str:
        """Combine results from all chunks"""

        combined = []
        for result in results:
            combined.append(result["output"])

        return "\n".join(combined)


def demonstrate_semantic_chunking():
    """Show how semantic chunking improves processing"""

    print("\n" + "="*80)
    print("SEMANTIC CHUNKING DEMONSTRATION")
    print("="*80)

    chunker = IntelligentSemanticChunker()

    # Complex request
    request = """
    Build a FastAPI REST API for user management with JWT authentication,
    add comprehensive unit tests with pytest,
    document all endpoints with OpenAPI,
    optimize database queries for performance,
    and create Docker deployment configuration
    """

    chunks = chunker.chunk_request(request)

    print(f"\nDocumenter Original Request ({len(request)} chars):")
    print(request)

    print(f"\n[CUT] Semantic Chunks ({len(chunks)} chunks):\n")

    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}:")
        print(f"  Type: {chunk.chunk_type}")
        print(f"  Content: {chunk.content[:60]}...")
        print(f"  Optimal Model: {chunk.optimal_model}")
        print(f"  Language: {chunk.language}")
        print(f"  Priority: {chunk.priority}")
        print()

    print("[GOAL] BENEFITS:")
    print("  1. Each chunk processed by the BEST model for that task")
    print("  2. Parallel processing possible for independent chunks")
    print("  3. Better context window usage (smaller, focused chunks)")
    print("  4. Dependency-aware ordering")
    print("  5. Cost optimization (use cheaper models where appropriate)")


if __name__ == "__main__":
    demonstrate_semantic_chunking()