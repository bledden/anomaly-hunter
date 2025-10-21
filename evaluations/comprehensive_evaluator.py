"""
Comprehensive Multi-Domain Anomaly Detection Evaluation Suite

Expanded evaluation with multiple scenarios per domain to demonstrate
versatility and gather comprehensive statistics.
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


class ComprehensiveEvaluator:
    """Comprehensive evaluation across multiple domains and scenarios"""

    def __init__(self):
        self.orchestrator = AnomalyOrchestrator()
        self.senso = SensoRAG()
        self.results = []

    # ========== FINANCIAL DOMAIN ==========

    def generate_financial_fraud(self):
        """Credit card fraud with sudden large transactions"""
        np.random.seed(100)
        normal = np.random.normal(80, 30, 95)
        normal = np.clip(normal, 20, 200)
        fraud = np.array([850, 920, 1100, 1250, 980])
        data = np.concatenate([normal, fraud])

        base_time = datetime.now() - timedelta(hours=100)
        timestamps = [base_time + timedelta(hours=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'financial',
                'scenario': 'fraud_detection',
                'type': 'credit_card_transactions',
                'description': 'Sudden spike in transaction amounts indicating fraud'
            }
        )

    def generate_financial_trading_flash_crash(self):
        """Stock trading flash crash"""
        np.random.seed(101)
        normal = np.random.normal(150, 10, 85)
        crash = np.linspace(150, 50, 10)  # Rapid drop
        recovery = np.linspace(50, 140, 5)
        data = np.concatenate([normal, crash, recovery])

        base_time = datetime.now() - timedelta(minutes=100)
        timestamps = [base_time + timedelta(minutes=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'financial',
                'scenario': 'flash_crash',
                'type': 'stock_price',
                'description': 'Rapid price drop and recovery in trading system'
            }
        )

    def generate_financial_account_takeover(self):
        """Account takeover with unusual login locations"""
        np.random.seed(102)
        normal = np.random.normal(1, 0.2, 92)  # 1 login/hour
        normal = np.clip(normal, 0, 3)
        takeover = np.array([15, 18, 22, 19, 16, 20, 17, 14])  # Burst of activity
        data = np.concatenate([normal, takeover])

        base_time = datetime.now() - timedelta(hours=100)
        timestamps = [base_time + timedelta(hours=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'financial',
                'scenario': 'account_takeover',
                'type': 'login_frequency',
                'description': 'Unusual spike in account activity suggesting takeover'
            }
        )

    # ========== IOT / MANUFACTURING DOMAIN ==========

    def generate_iot_bearing_failure(self):
        """Bearing failure with vibration increase"""
        np.random.seed(200)
        normal = np.random.normal(1.2, 0.3, 90)
        normal = np.clip(normal, 0.5, 2.0)
        degradation = np.linspace(2.0, 4.5, 5)
        failure = np.array([8.2, 9.1, 7.8, 8.5, 9.3])
        data = np.concatenate([normal, degradation, failure])

        base_time = datetime.now() - timedelta(minutes=500)
        timestamps = [base_time + timedelta(minutes=i*5) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'iot_manufacturing',
                'scenario': 'bearing_failure',
                'type': 'vibration_sensor',
                'description': 'Progressive bearing degradation leading to failure'
            }
        )

    def generate_iot_temperature_spike(self):
        """Temperature sensor detecting overheating"""
        np.random.seed(201)
        normal = np.random.normal(65, 5, 88)  # 65°C normal
        normal = np.clip(normal, 55, 75)
        overheat = np.array([85, 92, 98, 105, 110, 115, 118, 120, 117, 112, 108, 95])
        data = np.concatenate([normal, overheat])

        base_time = datetime.now() - timedelta(minutes=100)
        timestamps = [base_time + timedelta(minutes=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'iot_manufacturing',
                'scenario': 'temperature_spike',
                'type': 'temperature_sensor',
                'description': 'Equipment overheating beyond safe operating temperature'
            }
        )

    def generate_iot_pressure_drop(self):
        """Pressure sensor detecting leak"""
        np.random.seed(202)
        normal = np.random.normal(100, 3, 85)  # 100 PSI normal
        normal = np.clip(normal, 94, 106)
        leak = np.linspace(100, 45, 15)  # Gradual pressure loss
        data = np.concatenate([normal, leak])

        base_time = datetime.now() - timedelta(minutes=100)
        timestamps = [base_time + timedelta(minutes=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'iot_manufacturing',
                'scenario': 'pressure_leak',
                'type': 'pressure_sensor',
                'description': 'Gradual pressure loss indicating system leak'
            }
        )

    # ========== HEALTHCARE DOMAIN ==========

    def generate_healthcare_hypoglycemia(self):
        """Dangerous low blood sugar event"""
        np.random.seed(300)
        normal = np.random.normal(110, 15, 92)
        normal = np.clip(normal, 80, 140)
        hypo = np.array([75, 65, 52, 48, 45, 50, 58, 68])
        data = np.concatenate([normal, hypo])

        base_time = datetime.now() - timedelta(hours=25)
        timestamps = [base_time + timedelta(minutes=i*15) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'healthcare',
                'scenario': 'hypoglycemia',
                'type': 'continuous_glucose_monitor',
                'description': 'Dangerous blood sugar drop below safe levels'
            }
        )

    def generate_healthcare_heart_rate_spike(self):
        """Abnormal heart rate increase"""
        np.random.seed(301)
        normal = np.random.normal(72, 8, 90)  # 72 bpm normal
        normal = np.clip(normal, 60, 85)
        tachycardia = np.array([95, 110, 125, 140, 155, 165, 158, 145, 130, 115])
        data = np.concatenate([normal, tachycardia])

        base_time = datetime.now() - timedelta(minutes=100)
        timestamps = [base_time + timedelta(minutes=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'healthcare',
                'scenario': 'tachycardia',
                'type': 'heart_rate_monitor',
                'description': 'Abnormal heart rate elevation requiring attention'
            }
        )

    def generate_healthcare_blood_pressure_crisis(self):
        """Hypertensive crisis"""
        np.random.seed(302)
        normal = np.random.normal(120, 10, 88)  # 120 mmHg normal systolic
        normal = np.clip(normal, 100, 135)
        crisis = np.array([145, 160, 175, 185, 195, 200, 198, 190, 180, 170, 160, 150])
        data = np.concatenate([normal, crisis])

        base_time = datetime.now() - timedelta(hours=100)
        timestamps = [base_time + timedelta(hours=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'healthcare',
                'scenario': 'hypertensive_crisis',
                'type': 'blood_pressure_monitor',
                'description': 'Dangerous blood pressure elevation'
            }
        )

    # ========== DEVOPS DOMAIN ==========

    def generate_devops_api_latency(self):
        """API performance degradation"""
        np.random.seed(400)
        normal = np.random.normal(90, 20, 85)
        normal = np.clip(normal, 50, 150)
        degradation = np.linspace(150, 800, 10)
        critical = np.array([1200, 1500, 1800, 2100, 1900])
        data = np.concatenate([normal, degradation, critical])

        base_time = datetime.now() - timedelta(minutes=100)
        timestamps = [base_time + timedelta(minutes=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'devops',
                'scenario': 'api_latency',
                'type': 'response_time_ms',
                'description': 'API performance degradation from database issues'
            }
        )

    def generate_devops_memory_leak(self):
        """Memory leak causing progressive slowdown"""
        np.random.seed(401)
        normal = np.random.normal(45, 5, 30)  # 45% memory usage
        normal = np.clip(normal, 35, 55)
        leak = np.linspace(45, 95, 70)  # Gradual memory increase
        data = np.concatenate([normal, leak])

        base_time = datetime.now() - timedelta(hours=100)
        timestamps = [base_time + timedelta(hours=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'devops',
                'scenario': 'memory_leak',
                'type': 'memory_usage_percent',
                'description': 'Progressive memory leak requiring restart'
            }
        )

    def generate_devops_error_rate_spike(self):
        """Error rate spike from deployment"""
        np.random.seed(402)
        normal = np.random.normal(0.5, 0.2, 85)  # 0.5% error rate
        normal = np.clip(normal, 0, 1.5)
        spike = np.array([5, 12, 18, 25, 22, 19, 15, 10, 7, 4, 3, 2, 1.5, 1, 0.8])
        data = np.concatenate([normal, spike])

        base_time = datetime.now() - timedelta(minutes=100)
        timestamps = [base_time + timedelta(minutes=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'devops',
                'scenario': 'error_spike',
                'type': 'error_rate_percent',
                'description': 'Error rate spike from bad deployment'
            }
        )

    # ========== E-COMMERCE DOMAIN ==========

    def generate_ecommerce_conversion_drop(self):
        """Conversion rate drop from checkout bug"""
        np.random.seed(500)
        normal = np.random.normal(4.0, 0.5, 88)
        normal = np.clip(normal, 3.0, 5.0)
        bug = np.array([2.8, 1.5, 0.8, 0.5, 0.3, 0.6, 0.4, 0.7, 0.9, 1.2, 1.8, 2.1])
        data = np.concatenate([normal, bug])

        base_time = datetime.now() - timedelta(hours=100)
        timestamps = [base_time + timedelta(hours=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'ecommerce',
                'scenario': 'conversion_drop',
                'type': 'conversion_rate_percent',
                'description': 'Checkout bug causing conversion rate collapse'
            }
        )

    def generate_ecommerce_cart_abandonment(self):
        """Cart abandonment rate spike"""
        np.random.seed(501)
        normal = np.random.normal(68, 5, 85)  # 68% abandonment normal
        normal = np.clip(normal, 60, 76)
        spike = np.array([78, 82, 88, 92, 95, 97, 94, 90, 86, 82, 80, 78, 76, 74, 72])
        data = np.concatenate([normal, spike])

        base_time = datetime.now() - timedelta(hours=100)
        timestamps = [base_time + timedelta(hours=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'ecommerce',
                'scenario': 'cart_abandonment',
                'type': 'abandonment_rate_percent',
                'description': 'Unusual increase in shopping cart abandonment'
            }
        )

    def generate_ecommerce_return_rate_spike(self):
        """Product return rate increase"""
        np.random.seed(502)
        normal = np.random.normal(5, 1.5, 80)  # 5% return rate
        normal = np.clip(normal, 2, 9)
        quality_issue = np.array([12, 15, 18, 22, 25, 28, 30, 29, 27, 24, 20, 18, 15, 13, 11, 10, 9, 8, 7, 6])
        data = np.concatenate([normal, quality_issue])

        base_time = datetime.now() - timedelta(days=100)
        timestamps = [base_time + timedelta(days=i) for i in range(100)]

        return AnomalyContext(
            data=data,
            timestamps=np.array([ts.isoformat() for ts in timestamps]),
            metadata={
                'domain': 'ecommerce',
                'scenario': 'return_spike',
                'type': 'return_rate_percent',
                'description': 'Product quality issue causing return spike'
            }
        )

    async def evaluate_scenario(self, domain_name: str, scenario_name: str, context: AnomalyContext):
        """Run evaluation on a single scenario"""
        print(f"\n{'='*80}")
        print(f"Domain: {domain_name} | Scenario: {scenario_name}")
        print(f"{'='*80}")

        # Retrieve Senso context
        senso_query = f"{scenario_name} in {context.metadata['type']}"
        senso_context = self.senso.retrieve_context(senso_query)

        if senso_context is None:
            print(f"[SENSO] No historical context")

        # Run detection
        start_time = datetime.now()
        verdict = await self.orchestrator.investigate(context, senso_context)
        elapsed = (datetime.now() - start_time).total_seconds()

        # Extract results
        agent_findings = {finding.agent_name: finding for finding in verdict.agent_findings}

        result = {
            'domain': domain_name,
            'scenario': scenario_name,
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
            'consensus': verdict.summary[:200],
            'recommendation': verdict.recommendation
        }

        self.results.append(result)

        print(f"✓ Detected: {result['anomaly_detected']} | Severity: {result['severity']} | Confidence: {result['avg_confidence']:.1%} | Time: {elapsed:.3f}s")

        return result

    async def run_all_evaluations(self):
        """Run comprehensive evaluation suite"""
        print("\n" + "="*80)
        print("COMPREHENSIVE MULTI-DOMAIN EVALUATION SUITE")
        print("Testing 15 scenarios across 5 domains")
        print("="*80)

        scenarios = [
            # Financial (3 scenarios)
            ('Financial', 'Fraud Detection', self.generate_financial_fraud()),
            ('Financial', 'Flash Crash', self.generate_financial_trading_flash_crash()),
            ('Financial', 'Account Takeover', self.generate_financial_account_takeover()),

            # IoT Manufacturing (3 scenarios)
            ('IoT Manufacturing', 'Bearing Failure', self.generate_iot_bearing_failure()),
            ('IoT Manufacturing', 'Temperature Spike', self.generate_iot_temperature_spike()),
            ('IoT Manufacturing', 'Pressure Leak', self.generate_iot_pressure_drop()),

            # Healthcare (3 scenarios)
            ('Healthcare', 'Hypoglycemia', self.generate_healthcare_hypoglycemia()),
            ('Healthcare', 'Tachycardia', self.generate_healthcare_heart_rate_spike()),
            ('Healthcare', 'Hypertensive Crisis', self.generate_healthcare_blood_pressure_crisis()),

            # DevOps (3 scenarios)
            ('DevOps', 'API Latency', self.generate_devops_api_latency()),
            ('DevOps', 'Memory Leak', self.generate_devops_memory_leak()),
            ('DevOps', 'Error Spike', self.generate_devops_error_rate_spike()),

            # E-Commerce (3 scenarios)
            ('E-Commerce', 'Conversion Drop', self.generate_ecommerce_conversion_drop()),
            ('E-Commerce', 'Cart Abandonment', self.generate_ecommerce_cart_abandonment()),
            ('E-Commerce', 'Return Spike', self.generate_ecommerce_return_rate_spike())
        ]

        for domain_name, scenario_name, context in scenarios:
            await self.evaluate_scenario(domain_name, scenario_name, context)
            await asyncio.sleep(0.5)  # Rate limiting

        self.generate_report()

    def generate_report(self):
        """Generate comprehensive summary report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE EVALUATION SUMMARY")
        print("="*80)

        # Overall metrics
        total_scenarios = len(self.results)
        anomalies_detected = sum(1 for r in self.results if r['anomaly_detected'])
        avg_confidence = np.mean([r['avg_confidence'] for r in self.results])
        avg_detection_time = np.mean([r['detection_time_seconds'] for r in self.results])

        print(f"\nTotal Scenarios: {total_scenarios}")
        print(f"Anomalies Detected: {anomalies_detected}/{total_scenarios} ({anomalies_detected/total_scenarios*100:.1f}%)")
        print(f"Average Confidence: {avg_confidence:.1%}")
        print(f"Average Detection Time: {avg_detection_time:.3f}s")

        # Per-domain aggregation
        print("\n" + "-"*80)
        print("Per-Domain Performance:")
        print("-"*80)

        domains = {}
        for result in self.results:
            domain = result['domain']
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(result)

        for domain, results in domains.items():
            detected = sum(1 for r in results if r['anomaly_detected'])
            avg_conf = np.mean([r['avg_confidence'] for r in results])
            avg_time = np.mean([r['detection_time_seconds'] for r in results])

            print(f"\n{domain}:")
            print(f"  Scenarios: {len(results)}")
            print(f"  Detection Rate: {detected}/{len(results)} ({detected/len(results)*100:.1f}%)")
            print(f"  Avg Confidence: {avg_conf:.1%}")
            print(f"  Avg Time: {avg_time:.3f}s")

        # Save results
        output_file = Path(__file__).parent / 'comprehensive_results.json'
        with open(output_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_scenarios': total_scenarios,
                    'domains': len(domains),
                    'detection_rate': f"{anomalies_detected/total_scenarios*100:.1f}%",
                    'avg_confidence': f"{avg_confidence:.1%}",
                    'avg_detection_time': f"{avg_detection_time:.3f}s",
                    'timestamp': datetime.now().isoformat()
                },
                'per_domain': {
                    domain: {
                        'scenarios': len(results),
                        'detection_rate': f"{sum(1 for r in results if r['anomaly_detected'])}/{len(results)}",
                        'avg_confidence': f"{np.mean([r['avg_confidence'] for r in results]):.1%}",
                        'avg_time': f"{np.mean([r['detection_time_seconds'] for r in results]):.3f}s"
                    }
                    for domain, results in domains.items()
                },
                'results': self.results
            }, f, indent=2)

        print(f"\n\n[SAVED] Comprehensive results: {output_file}")


async def main():
    evaluator = ComprehensiveEvaluator()
    await evaluator.run_all_evaluations()


if __name__ == "__main__":
    asyncio.run(main())
