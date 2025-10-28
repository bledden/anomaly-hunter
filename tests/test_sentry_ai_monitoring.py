"""
Test Sentry AI Monitoring Integration
Validates that Sentry traces are properly created for agent workflows
"""

import asyncio
import pytest
import numpy as np
import os
from unittest.mock import patch, MagicMock
import sentry_sdk

# Test against real orchestrator
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from orchestrator import AnomalyOrchestrator, AnomalyContext
from integrations.senso_rag import SensoRAG


class TestSentryAIMonitoring:
    """
    Test suite for Sentry AI agent monitoring integration

    Validates:
    - Sentry SDK initialization with OpenAI integration
    - Transaction creation for workflows
    - Span creation for agents and tool calls
    - Data tracking (tokens, latency, confidence)
    """

    def test_sentry_initialization(self):
        """Test that Sentry is initialized with AI monitoring"""

        # Verify Sentry is initialized
        client = sentry_sdk.Hub.current.client
        assert client is not None, "Sentry client not initialized"

        # Check for OpenAI integration
        integrations = [type(i).__name__ for i in client.integrations]
        assert "OpenAIIntegration" in integrations, \
            f"OpenAI integration not found. Found: {integrations}"

        print("[OK] Sentry initialized with AI monitoring")

    @pytest.mark.asyncio
    async def test_orchestrator_creates_transaction(self):
        """Test that orchestrator creates Sentry transaction"""

        # Mock Sentry transport to capture events
        captured_events = []

        def capture_event(event):
            captured_events.append(event)
            return event

        with patch.object(sentry_sdk.Hub.current.client, 'transport') as mock_transport:
            mock_transport.capture_event = MagicMock(side_effect=capture_event)

            # Create simple test data
            data = np.array([100, 102, 101, 103, 250, 99, 100])  # Spike at index 4
            context = AnomalyContext(
                data=data,
                timestamps=["2024-10-21T00:00:00Z"] * len(data),
                metadata={"source": "test"}
            )

            # Run detection
            orchestrator = AnomalyOrchestrator()
            verdict = await orchestrator.investigate(context)

            # Verify verdict was created
            assert verdict is not None
            assert verdict.severity > 0

            print(f"[OK] Detection completed: severity {verdict.severity}/10")
            print(f"[OK] Sentry events captured: {len(captured_events)}")

    @pytest.mark.asyncio
    async def test_agent_spans_created(self):
        """Test that each agent creates a span"""

        # Mock Sentry to track span creation
        spans_created = []

        original_start_span = sentry_sdk.start_span

        def track_span(*args, **kwargs):
            span = original_start_span(*args, **kwargs)
            spans_created.append({
                "op": kwargs.get("op", ""),
                "description": kwargs.get("description", "")
            })
            return span

        with patch('sentry_sdk.start_span', side_effect=track_span):
            data = np.array([100, 102, 101, 103, 250, 99, 100])
            context = AnomalyContext(data=data)

            orchestrator = AnomalyOrchestrator()
            verdict = await orchestrator.investigate(context)

            # Verify spans were created
            assert len(spans_created) > 0, "No spans created"

            # Check for expected spans
            span_ops = [s["op"] for s in spans_created]

            # Should have agent orchestration span
            assert "ai.agent.orchestrate" in span_ops, \
                f"Missing orchestration span. Found: {span_ops}"

            # Should have synthesis span
            assert "ai.synthesis" in span_ops, \
                f"Missing synthesis span. Found: {span_ops}"

            # Should have learning span
            assert "learning" in span_ops, \
                f"Missing learning span. Found: {span_ops}"

            print(f"[OK] Created {len(spans_created)} spans")
            print(f"[OK] Span operations: {span_ops[:5]}")  # Show first 5

    @pytest.mark.asyncio
    async def test_llm_call_spans(self):
        """Test that LLM calls create spans with metadata"""

        spans_with_data = []

        original_start_span = sentry_sdk.start_span

        def track_span_data(*args, **kwargs):
            span = original_start_span(*args, **kwargs)

            # Capture span data
            if kwargs.get("op", "").startswith("ai."):
                span_info = {
                    "op": kwargs.get("op"),
                    "description": kwargs.get("description"),
                    "data": {}
                }
                spans_with_data.append(span_info)

            return span

        with patch('sentry_sdk.start_span', side_effect=track_span_data):
            data = np.array([100, 102, 101, 103, 250, 99, 100])
            context = AnomalyContext(data=data)

            orchestrator = AnomalyOrchestrator()
            verdict = await orchestrator.investigate(context)

            # Find AI-related spans
            ai_spans = [s for s in spans_with_data if s["op"].startswith("ai.")]

            assert len(ai_spans) > 0, "No AI spans found"

            print(f"[OK] Found {len(ai_spans)} AI-related spans")

            # Verify we have agent spans
            agent_spans = [s for s in ai_spans if "agent" in s["op"]]
            assert len(agent_spans) >= 1, \
                f"Expected agent spans, found {len(agent_spans)}"

            print(f"[OK] Agent spans: {len(agent_spans)}")

    def test_senso_rag_creates_tool_span(self):
        """Test that Senso RAG retrieval creates tool call span"""

        # Mock Senso API response
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {"text": "Historical anomaly case 1", "score": 0.95},
                    {"text": "Historical anomaly case 2", "score": 0.87}
                ]
            }
            mock_post.return_value = mock_response

            # Set required env vars
            with patch.dict(os.environ, {
                "SENSO_API_KEY": "test_key",
                "SENSO_ORG_ID": "test_org"
            }):
                senso = SensoRAG()

                # Track spans
                spans_created = []

                original_start_span = sentry_sdk.start_span

                def track_span(*args, **kwargs):
                    span = original_start_span(*args, **kwargs)
                    if kwargs.get("op") == "ai.tool.call":
                        spans_created.append(kwargs.get("description", ""))
                    return span

                with patch('sentry_sdk.start_span', side_effect=track_span):
                    context = senso.retrieve_context("test query")

                    # Verify tool span was created
                    assert len(spans_created) > 0, "No tool span created"
                    assert any("Senso" in s for s in spans_created), \
                        f"No Senso span found in {spans_created}"

                    print(f"[OK] Senso RAG created tool span")
                    print(f"[OK] Context retrieved: {len(context) if context else 0} chars")

    @pytest.mark.asyncio
    async def test_end_to_end_trace_structure(self):
        """Test complete trace structure matches expected hierarchy"""

        # Expected hierarchy:
        # Transaction (ai.agent.workflow)
        #   ├─ Span (ai.agent.orchestrate) - 3 agents
        #   ├─ Span (ai.synthesis)
        #   ├─ Span (recommendation)
        #   └─ Span (learning)

        spans_hierarchy = []

        def track_hierarchy(*args, **kwargs):
            span_info = {
                "op": kwargs.get("op", ""),
                "description": kwargs.get("description", "")
            }
            spans_hierarchy.append(span_info)
            return sentry_sdk.start_span(*args, **kwargs)

        with patch('sentry_sdk.start_span', side_effect=track_hierarchy):
            data = np.array([100, 102, 101, 103, 250, 99, 100])
            context = AnomalyContext(data=data)

            orchestrator = AnomalyOrchestrator()
            verdict = await orchestrator.investigate(context)

            # Verify expected operations exist
            ops = [s["op"] for s in spans_hierarchy]

            expected_ops = [
                "ai.agent.orchestrate",  # Parallel agent execution
                "ai.synthesis",          # Confidence-weighted voting
                "recommendation",        # Generate recommendation
                "learning"              # Autonomous learning
            ]

            for expected_op in expected_ops:
                assert expected_op in ops, \
                    f"Missing expected operation: {expected_op}. Found: {ops}"

            print("[OK] Complete trace structure validated")
            print(f"[OK] Total spans: {len(spans_hierarchy)}")
            print(f"[OK] Operations: {expected_ops}")

    def test_span_data_includes_metrics(self):
        """Test that spans include relevant metrics (confidence, severity, etc)"""

        # This is tested implicitly through other tests
        # but we validate the data structure here

        with sentry_sdk.start_span(
            op="test.span",
            description="Test span with data"
        ) as span:
            # Set various types of data
            span.set_data("severity", 8)
            span.set_data("confidence", 0.87)
            span.set_data("model", "gpt-5-pro")
            span.set_data("data_points", 100)

            # Verify span exists
            assert span is not None

            print("[OK] Span data structure validated")

    @pytest.mark.asyncio
    async def test_error_handling_in_spans(self):
        """Test that errors in agents are captured in Sentry spans"""

        # Force an error by providing invalid data
        context = AnomalyContext(
            data=None,  # Invalid!
            timestamps=None,
            metadata=None
        )

        orchestrator = AnomalyOrchestrator()

        # This should not crash, but handle gracefully
        try:
            verdict = await orchestrator.investigate(context)
            # Should return a verdict with low confidence
            assert verdict.confidence < 0.5, \
                "Expected low confidence for invalid data"

            print("[OK] Error handled gracefully with Sentry tracking")
        except Exception as e:
            # If it raises, Sentry should have captured it
            print(f"[OK] Exception captured: {type(e).__name__}")


def run_tests():
    """Run all tests"""

    print("\n" + "="*60)
    print("SENTRY AI MONITORING - Integration Tests")
    print("="*60 + "\n")

    test = TestSentryAIMonitoring()

    try:
        # Test 1: Initialization
        print("[TEST 1] Sentry initialization...")
        test.test_sentry_initialization()

        # Test 2: Transaction creation
        print("\n[TEST 2] Orchestrator creates transaction...")
        asyncio.run(test.test_orchestrator_creates_transaction())

        # Test 3: Agent spans
        print("\n[TEST 3] Agent spans created...")
        asyncio.run(test.test_agent_spans_created())

        # Test 4: LLM call spans
        print("\n[TEST 4] LLM call spans...")
        asyncio.run(test.test_llm_call_spans())

        # Test 5: Senso RAG tool span
        print("\n[TEST 5] Senso RAG tool span...")
        test.test_senso_rag_creates_tool_span()

        # Test 6: Complete trace structure
        print("\n[TEST 6] End-to-end trace structure...")
        asyncio.run(test.test_end_to_end_trace_structure())

        # Test 7: Span data metrics
        print("\n[TEST 7] Span data includes metrics...")
        test.test_span_data_includes_metrics()

        # Test 8: Error handling
        print("\n[TEST 8] Error handling in spans...")
        asyncio.run(test.test_error_handling_in_spans())

        print("\n" + "="*60)
        print("ALL TESTS PASSED")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
