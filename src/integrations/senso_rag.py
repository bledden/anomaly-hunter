"""
Senso RAG Knowledge Base Integration
Retrieve historical anomaly patterns and context
"""

import os
import requests
from typing import Optional, Dict, Any
import sentry_sdk


class SensoRAG:
    """
    Senso Knowledge Base - RAG for Historical Anomalies

    Retrieves similar historical anomaly patterns
    to provide context for current investigation
    """

    def __init__(self):
        """Initialize Senso client"""

        self.api_key = os.getenv("SENSO_API_KEY")
        self.org_id = os.getenv("SENSO_ORG_ID")

        self.enabled = False

        if not self.api_key or not self.org_id:
            print("[WARN] Senso credentials missing - RAG disabled")
            return

        self.base_url = "https://sdk.senso.ai/api/v1"  # Correct Senso SDK endpoint
        self.enabled = True
        print("[SENSO] ✅ RAG knowledge base initialized")
        print(f"[SENSO]   └─ API endpoint: {self.base_url}")

    @sentry_sdk.trace
    def retrieve_context(self, anomaly_description: str, top_k: int = 3) -> Optional[str]:
        """
        Retrieve historical context for similar anomalies

        Args:
            anomaly_description: Description of current anomaly
            top_k: Number of similar cases to retrieve

        Returns:
            Context string with historical patterns, or None
        """

        if not self.enabled:
            return None

        with sentry_sdk.start_span(
            op="ai.tool.call",
            description="Senso RAG - Historical Context Retrieval"
        ) as span:
            span.set_data("tool", "senso_rag")
            span.set_data("query", anomaly_description[:100])  # Truncate for privacy
            span.set_data("top_k", top_k)

            try:
                # Query Senso search endpoint (correct API structure)
                headers = {
                    "X-API-Key": self.api_key,  # Senso uses X-API-Key, not Bearer token
                    "Content-Type": "application/json"
                }

                payload = {
                    "query": anomaly_description,
                    "limit": top_k,
                    "org_id": self.org_id
                }

                # Use correct Senso search endpoint
                with sentry_sdk.start_span(
                    op="http.client",
                    description="POST /search to Senso API"
                ) as http_span:
                    http_span.set_data("url", f"{self.base_url}/search")
                    http_span.set_data("method", "POST")

                    response = requests.post(
                        f"{self.base_url}/search",
                        json=payload,
                        headers=headers,
                        timeout=10
                    )

                    http_span.set_data("status_code", response.status_code)

                print(f"[SENSO] 🔍 Querying RAG for similar anomalies...")

                if response.status_code == 200:
                    data = response.json()

                    # Extract relevant context from results
                    context_parts = []
                    results = data.get("results", [])

                    span.set_data("results_count", len(results))

                    for i, result in enumerate(results[:top_k], 1):
                        text = result.get("text", "")
                        score = result.get("score", 0.0)
                        context_parts.append(f"[Match {i}, confidence {score:.2f}]: {text[:200]}")

                    if context_parts:
                        context = "Historical patterns:\n" + "\n".join(context_parts)
                        span.set_data("context_retrieved", True)
                        span.set_data("matches_found", len(context_parts))
                        print(f"[SENSO] 📚 Retrieved {len(context_parts)} similar historical cases")
                        print(f"[SENSO]   └─ Action: Provided RAG context from knowledge base")
                        return context
                    else:
                        span.set_data("context_retrieved", False)
                        print(f"[SENSO] ℹ️  No matching historical patterns found (new anomaly type)")
                        return None

                else:
                    span.set_data("error", f"HTTP {response.status_code}")
                    print(f"[SENSO] ⚠️  API returned status {response.status_code}")
                    return None

            except Exception as e:
                span.set_data("error", str(e))
                print(f"[WARN] Senso RAG query failed: {e}")
                return None

    def store_anomaly(self, verdict: Any) -> bool:
        """
        Store current anomaly in knowledge base for future reference

        Args:
            verdict: Anomaly verdict to store

        Returns:
            True if stored successfully
        """

        if not self.enabled:
            return False

        try:
            headers = {
                "X-API-Key": self.api_key,  # Senso uses X-API-Key, not Bearer token
                "Content-Type": "application/json"
            }

            # Create document for storage
            document = {
                "text": f"Severity {verdict.severity}/10 anomaly: {verdict.summary[:300]}",
                "metadata": {
                    "severity": verdict.severity,
                    "confidence": verdict.confidence,
                    "anomaly_count": len(verdict.anomalies_detected),
                    "recommendation": verdict.recommendation
                },
                "org_id": self.org_id
            }

            # Store in Senso knowledge base using content/raw endpoint
            response = requests.post(
                f"{self.base_url}/content/raw",
                json=document,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 201, 202]:  # 202 = Accepted (async processing)
                print(f"[SENSO] 💾 Stored anomaly in knowledge base")
                print(f"[SENSO]   └─ Action: Added severity {verdict.severity}/10 case to RAG for future learning")
                return True
            else:
                print(f"[SENSO] ⚠️  Storage failed (status {response.status_code})")
                return False

        except Exception as e:
            print(f"[WARN] Senso storage failed: {e}")
            return False
