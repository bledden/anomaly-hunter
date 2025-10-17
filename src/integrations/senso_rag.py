"""
Senso RAG Knowledge Base Integration
Retrieve historical anomaly patterns and context
"""

import os
import requests
from typing import Optional, Dict, Any


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

        self.base_url = "https://api.senso.ai/v1"
        self.enabled = True
        print("[SENSO] ✅ RAG knowledge base initialized")

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

        try:
            # Query Senso RAG endpoint
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "query": anomaly_description,
                "org_id": self.org_id,
                "top_k": top_k,
                "include_metadata": True
            }

            # Note: Using generic endpoint structure - adjust based on actual Senso API docs
            response = requests.post(
                f"{self.base_url}/query",
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                # Extract relevant context from results
                context_parts = []
                results = data.get("results", [])

                for i, result in enumerate(results[:top_k], 1):
                    text = result.get("text", "")
                    score = result.get("score", 0.0)
                    context_parts.append(f"[Match {i}, confidence {score:.2f}]: {text[:200]}")

                if context_parts:
                    context = "Historical patterns:\n" + "\n".join(context_parts)
                    print(f"[SENSO] 📚 Retrieved {len(context_parts)} similar cases")
                    return context

            return None

        except Exception as e:
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
                "Authorization": f"Bearer {self.api_key}",
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

            # Store in Senso knowledge base
            response = requests.post(
                f"{self.base_url}/documents",
                json=document,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 201]:
                print(f"[SENSO] 💾 Stored anomaly in knowledge base")
                return True

            return False

        except Exception as e:
            print(f"[WARN] Senso storage failed: {e}")
            return False
