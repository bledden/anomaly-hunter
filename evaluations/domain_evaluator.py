"""
Multi-Domain Anomaly Detection Evaluation Suite

Tests Anomaly Hunter across different data domains to demonstrate
domain-agnostic detection capabilities.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import asyncio
import numpy as np
from datetime import datetime, timedelta
from orchestrator import AnomalyOrchestrator, AnomalyContext
from integrations.senso_rag import SensoRAG
import json


class DomainEvaluator:
    """Evaluate anomaly detection across multiple data domains"""

    def __init__(self):
        self.orchestrator = AnomalyOrchestrator()
        self.senso = SensoRAG()
        self.results = []

    def generate_financial_data(self):
        """Generate credit card transaction data with fraud anomaly"""
        np.random.seed(42)

        # Normal transactions: $20-200, mean ~$80
        normal_data = np.random.normal(80, 30, 95)
        normal_data = np.clip(normal_data, 20, 200)

        # Fraud: Sudden spike of large transactions
        fraud_transactions = np.array([850, 920, 1100, 1250, 980])

        data = np.concatenate([normal_data, fraud_transactions])

        # Timestamps: Last 100 hours
        base_time = datetime.now() - timedelta(hours=100)
        timestamps = [base_time + timedelta(hours=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'financial',
                'type': 'credit_card_transactions',
                'card_id': 'XXXX-1234',
                'normal_range': '$20-$200',
                'expected_mean': '$80',
                'anomaly_injected': 'fraud_pattern_at_hour_95'
            }
        )

    def generate_iot_sensor_data(self):
        """Generate manufacturing sensor data with equipment failure"""
        np.random.seed(43)

        # Normal vibration: 0.5-2.0 mm/s
        normal_vibration = np.random.normal(1.2, 0.3, 90)
        normal_vibration = np.clip(normal_vibration, 0.5, 2.0)

        # Equipment degradation + failure spike
        degradation = np.linspace(2.0, 4.5, 5)  # Gradual increase
        failure_spike = np.array([8.2, 9.1, 7.8, 8.5, 9.3])  # Catastrophic failure

        data = np.concatenate([normal_vibration, degradation, failure_spike])

        # Timestamps: Every 5 minutes for ~8 hours
        base_time = datetime.now() - timedelta(minutes=500)
        timestamps = [base_time + timedelta(minutes=i*5) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'iot_manufacturing',
                'type': 'vibration_sensor',
                'machine_id': 'CNC-042',
                'sensor_type': 'accelerometer',
                'location': 'Assembly Line 3',
                'normal_range': '0.5-2.0 mm/s',
                'anomaly_injected': 'bearing_failure_at_minute_450'
            }
        )

    def generate_healthcare_data(self):
        """Generate continuous glucose monitoring data with hypoglycemia"""
        np.random.seed(44)

        # Normal glucose: 80-140 mg/dL
        normal_glucose = np.random.normal(110, 15, 92)
        normal_glucose = np.clip(normal_glucose, 80, 140)

        # Hypoglycemic episode: Sudden drop
        hypo_event = np.array([75, 65, 52, 48, 45, 50, 58, 68])

        data = np.concatenate([normal_glucose, hypo_event])

        # Timestamps: Every 15 minutes for 24 hours
        base_time = datetime.now() - timedelta(hours=25)
        timestamps = [base_time + timedelta(minutes=i*15) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'healthcare',
                'type': 'continuous_glucose_monitor',
                'patient_id': 'PT-7821',
                'device': 'Dexcom G7',
                'normal_range': '80-140 mg/dL',
                'critical_threshold': '<70 mg/dL',
                'anomaly_injected': 'hypoglycemia_at_hour_23'
            }
        )

    def generate_devops_data(self):
        """Generate API response time data with performance degradation"""
        np.random.seed(45)

        # Normal API latency: 50-150ms
        normal_latency = np.random.normal(90, 20, 85)
        normal_latency = np.clip(normal_latency, 50, 150)

        # Database issue causing slowdown
        degradation = np.linspace(150, 800, 10)
        critical_slow = np.array([1200, 1500, 1800, 2100, 1900])

        data = np.concatenate([normal_latency, degradation, critical_slow])

        # Timestamps: Every minute for 100 minutes
        base_time = datetime.now() - timedelta(minutes=100)
        timestamps = [base_time + timedelta(minutes=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'devops',
                'type': 'api_response_time',
                'endpoint': '/api/v2/users',
                'service': 'user-service',
                'normal_range': '50-150ms',
                'sla_threshold': '500ms',
                'anomaly_injected': 'database_connection_pool_exhaustion_at_minute_85'
            }
        )

    def generate_ecommerce_data(self):
        """Generate conversion rate data with checkout bug"""
        np.random.seed(46)

        # Normal conversion rate: 3-5%
        normal_conversion = np.random.normal(4.0, 0.5, 88)
        normal_conversion = np.clip(normal_conversion, 3.0, 5.0)

        # Checkout bug causing drop
        bug_impact = np.array([2.8, 1.5, 0.8, 0.5, 0.3, 0.6, 0.4, 0.7, 0.9, 1.2, 1.8, 2.1])

        data = np.concatenate([normal_conversion, bug_impact])

        # Timestamps: Hourly for ~4 days
        base_time = datetime.now() - timedelta(hours=100)
        timestamps = [base_time + timedelta(hours=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'ecommerce',
                'type': 'hourly_conversion_rate',
                'site': 'www.shop.example.com',
                'page': 'checkout_flow',
                'normal_range': '3-5%',
                'target_rate': '4.5%',
                'anomaly_injected': 'payment_gateway_integration_bug_at_hour_88'
            }
        )

    async def evaluate_domain(self, domain_name: str, context: AnomalyContext):
        """Run evaluation on a single domain"""
        print(f"\n{'='*80}")
        print(f"Evaluating Domain: {domain_name.upper()}")
        print(f"{'='*80}")

        # Retrieve historical context from Senso (optional - graceful degradation)
        senso_query = f"Anomaly in {context.metadata['type']}: mean={np.mean(context.data):.2f}"
        senso_context = self.senso.retrieve_context(senso_query)

        if senso_context is None:
            print(f"[SENSO] No historical context available (continuing without)")

        # Run detection
        start_time = datetime.now()
        verdict = await self.orchestrator.investigate(context, senso_context)
        elapsed = (datetime.now() - start_time).total_seconds()

        # Extract results from AnomalyVerdict dataclass
        agent_findings = {finding.agent_name: finding for finding in verdict.agent_findings}

        result = {
            'domain': domain_name,
            'metadata': context.metadata,
            'detection_time_seconds': elapsed,
            'severity': verdict.severity,
            'anomaly_detected': len(verdict.anomalies_detected) > 0,
            'anomalies_count': len(verdict.anomalies_detected),
            'confidence_scores': {
                'pattern_analyst': agent_findings.get('pattern_analyst', type('obj', (), {'confidence': 0})).confidence,
                'change_detective': agent_findings.get('change_detective', type('obj', (), {'confidence': 0})).confidence,
                'root_cause': agent_findings.get('root_cause', type('obj', (), {'confidence': 0})).confidence
            },
            'avg_confidence': verdict.confidence,
            'consensus': verdict.summary,
            'recommendation': verdict.recommendation,
            'findings': {
                'pattern_analyst': agent_findings.get('pattern_analyst', type('obj', (), {'finding': ''})).finding,
                'change_detective': agent_findings.get('change_detective', type('obj', (), {'finding': ''})).finding,
                'root_cause': agent_findings.get('root_cause', type('obj', (), {'finding': ''})).finding
            }
        }

        self.results.append(result)

        # Print summary
        print(f"\n[RESULT] Anomaly Detected: {result['anomaly_detected']}")
        print(f"[RESULT] Severity: {result['severity']}")
        print(f"[RESULT] Avg Confidence: {result['avg_confidence']:.1f}%")
        print(f"[RESULT] Detection Time: {result['detection_time_seconds']:.2f}s")
        print(f"\n[CONSENSUS] {result['consensus'][:200]}...")

        return result

    async def run_all_evaluations(self):
        """Run evaluations across all domains"""
        print("\n" + "="*80)
        print("MULTI-DOMAIN ANOMALY DETECTION EVALUATION")
        print("="*80)

        domains = [
            ('Financial (Fraud Detection)', self.generate_financial_data()),
            ('IoT Manufacturing (Equipment Failure)', self.generate_iot_sensor_data()),
            ('Healthcare (Hypoglycemia)', self.generate_healthcare_data()),
            ('DevOps (API Performance)', self.generate_devops_data()),
            ('E-Commerce (Conversion Drop)', self.generate_ecommerce_data())
        ]

        for domain_name, context in domains:
            await self.evaluate_domain(domain_name, context)
            await asyncio.sleep(1)  # Rate limiting

        # Generate summary report
        self.generate_report()

    def generate_report(self):
        """Generate evaluation summary report"""
        print("\n" + "="*80)
        print("EVALUATION SUMMARY")
        print("="*80)

        total_domains = len(self.results)
        anomalies_detected = sum(1 for r in self.results if r['anomaly_detected'])
        avg_confidence = np.mean([r['avg_confidence'] for r in self.results])
        avg_detection_time = np.mean([r['detection_time_seconds'] for r in self.results])

        print(f"\nDomains Evaluated: {total_domains}")
        print(f"Anomalies Detected: {anomalies_detected}/{total_domains} ({anomalies_detected/total_domains*100:.1f}%)")
        print(f"Average Confidence: {avg_confidence:.1f}%")
        print(f"Average Detection Time: {avg_detection_time:.2f}s")

        print("\n" + "-"*80)
        print("Per-Domain Results:")
        print("-"*80)

        for result in self.results:
            print(f"\n{result['domain']}:")
            print(f"  Detected: {'✓' if result['anomaly_detected'] else '✗'}")
            print(f"  Severity: {result['severity']}")
            print(f"  Confidence: {result['avg_confidence']:.1f}%")
            print(f"    - Pattern Analyst: {result['confidence_scores']['pattern_analyst']:.1f}%")
            print(f"    - Change Detective: {result['confidence_scores']['change_detective']:.1f}%")
            print(f"    - Root Cause: {result['confidence_scores']['root_cause']:.1f}%")
            print(f"  Time: {result['detection_time_seconds']:.2f}s")

        # Save detailed results to JSON
        output_file = Path(__file__).parent / 'evaluation_results.json'
        with open(output_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_domains': total_domains,
                    'anomalies_detected': anomalies_detected,
                    'detection_rate': f"{anomalies_detected/total_domains*100:.1f}%",
                    'avg_confidence': f"{avg_confidence:.1f}%",
                    'avg_detection_time': f"{avg_detection_time:.2f}s",
                    'timestamp': datetime.now().isoformat()
                },
                'results': self.results
            }, f, indent=2)

        print(f"\n\n[SAVED] Detailed results: {output_file}")


async def main():
    evaluator = DomainEvaluator()
    await evaluator.run_all_evaluations()


if __name__ == "__main__":
    asyncio.run(main())
