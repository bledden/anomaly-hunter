"""
Model Strategy Selector
Allows users to choose between QUALITY, COST, or BALANCED approaches
"""

import yaml
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Strategy(Enum):
    """Available model selection strategies"""
    QUALITY_FIRST = "QUALITY_FIRST"
    COST_FIRST = "COST_FIRST"
    BALANCED = "BALANCED"
    SPEED_FIRST = "SPEED_FIRST"
    PRIVACY_FIRST = "PRIVACY_FIRST"


@dataclass
class ModelSelectionContext:
    """Context for making model selection decisions"""
    task_type: str
    task_complexity: float  # 0.0 to 1.0
    remaining_budget: float  # in USD
    sensitive_data: bool = False
    required_latency: Optional[float] = None  # in seconds
    user_waiting: bool = False
    confidence_threshold: float = 0.75


class StrategySelector:
    """Selects appropriate models based on user strategy preference"""

    def __init__(self, config_path: str = "config/model_strategy_config.yaml"):
        """Initialize with strategy configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.current_strategy = Strategy[self.config['user_preference']]
        self.total_cost = 0.0
        self.task_count = 0

    def get_user_strategy(self) -> Strategy:
        """Get current user strategy preference"""
        return self.current_strategy

    def set_user_strategy(self, strategy: Strategy):
        """Allow user to change strategy"""
        self.current_strategy = strategy
        logger.info(f"Strategy changed to: {strategy.value}")

    def select_model(self,
                    agent_type: str,
                    context: ModelSelectionContext) -> Tuple[str, Dict]:
        """
        Select the best model for a given agent and context

        Returns:
            Tuple of (model_id, selection_info)
        """
        # Check if auto-switch should override user preference
        effective_strategy = self._check_auto_switch(context)

        # Get strategy configuration
        strategy_config = self.config['strategies'][effective_strategy.value]
        model_prefs = strategy_config['model_preferences'][agent_type]
        thresholds = strategy_config['thresholds']

        # Select model based on preferences and thresholds
        selected_model = self._pick_model(
            model_prefs,
            thresholds,
            context
        )

        # Calculate estimated cost
        estimated_cost = self._estimate_cost(selected_model, context)

        # Build selection info
        selection_info = {
            'strategy_used': effective_strategy.value,
            'original_strategy': self.current_strategy.value,
            'model': selected_model,
            'estimated_cost': estimated_cost,
            'quality_score': self._get_quality_score(selected_model),
            'reason': self._explain_selection(
                selected_model,
                effective_strategy,
                context
            )
        }

        # Update tracking
        self.total_cost += estimated_cost
        self.task_count += 1

        return selected_model, selection_info

    def _check_auto_switch(self, context: ModelSelectionContext) -> Strategy:
        """Check if we should auto-switch strategy based on context"""
        if not self.config['dynamic_rules']['auto_switch']['enabled']:
            return self.current_strategy

        for rule in self.config['dynamic_rules']['auto_switch']['rules']:
            if self._evaluate_condition(rule['condition'], context):
                new_strategy = Strategy[rule['switch_to']]
                logger.info(f"Auto-switching from {self.current_strategy.value} to {new_strategy.value}")
                return new_strategy

        return self.current_strategy

    def _evaluate_condition(self, condition: str, context: ModelSelectionContext) -> bool:
        """Evaluate a condition string against context using safe parsing"""
        try:
            # Create safe evaluation context with actual values
            eval_context = {
                'task_complexity': context.task_complexity,
                'remaining_budget': context.remaining_budget,
                'sensitive_data': context.sensitive_data,
                'user_waiting_time': 30 if context.user_waiting else 0,
            }

            # Safe evaluation using ast.literal_eval for literals only
            # For simple comparisons, manually parse and evaluate
            condition = condition.strip()

            # Support simple comparison operators
            for op in ['>=', '<=', '==', '!=', '>', '<']:
                if op in condition:
                    left, right = condition.split(op, 1)
                    left = left.strip()
                    right = right.strip()

                    # Get left value from context
                    left_val = eval_context.get(left)
                    if left_val is None:
                        return False

                    # Parse right value (number or boolean)
                    try:
                        # Try to parse as number
                        right_val = float(right)
                    except ValueError:
                        # Try as boolean
                        if right.lower() == 'true':
                            right_val = True
                        elif right.lower() == 'false':
                            right_val = False
                        else:
                            return False

                    # Perform comparison
                    if op == '>=':
                        return left_val >= right_val
                    elif op == '<=':
                        return left_val <= right_val
                    elif op == '==':
                        return left_val == right_val
                    elif op == '!=':
                        return left_val != right_val
                    elif op == '>':
                        return left_val > right_val
                    elif op == '<':
                        return left_val < right_val

            # If it's just a variable name, return its boolean value
            if condition in eval_context:
                return bool(eval_context[condition])

            return False
        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False

    def _pick_model(self,
                   model_prefs: Dict,
                   thresholds: Dict,
                   context: ModelSelectionContext) -> str:
        """Pick the best model from preferences"""
        # Try primary models first
        for model in model_prefs['primary']:
            if self._model_meets_requirements(model, thresholds, context):
                return model

        # Fall back to secondary models
        for model in model_prefs['fallback']:
            if self._model_meets_requirements(model, thresholds, context):
                return model

        # If nothing meets requirements, use first primary
        return model_prefs['primary'][0]

    def _model_meets_requirements(self,
                                 model: str,
                                 thresholds: Dict,
                                 context: ModelSelectionContext) -> bool:
        """Check if model meets the threshold requirements"""
        quality_score = self._get_quality_score(model)

        # Check quality threshold
        if quality_score < thresholds['min_quality_score']:
            return False

        # Check latency if specified
        if context.required_latency:
            model_latency = self._estimate_latency(model)
            if model_latency > context.required_latency:
                return False

        # Check budget
        if context.remaining_budget < 10:  # Less than $10
            # Prefer free models
            if self._estimate_cost(model, context) > 0:
                return False

        return True

    def _get_quality_score(self, model: str) -> float:
        """Get normalized quality score for a model"""
        benchmarks = self.config.get('model_benchmarks', {})

        # Check for exact match
        if model in benchmarks:
            # Normalize to 0-1 scale
            return benchmarks[model] / 100.0

        # Check for wildcard matches (e.g., anthropic/claude-*)
        for pattern, score in benchmarks.items():
            if '*' in pattern:
                prefix = pattern.replace('*', '')
                if model.startswith(prefix):
                    return score / 100.0

        # Default scores by provider
        if 'gpt-5' in model:
            return 0.95
        elif 'claude-4' in model or 'claude-sonnet-4.5' in model:
            return 0.94
        elif 'claude-3' in model:
            return 0.88
        elif 'qwen2.5-coder' in model:
            return 0.85  # Matches GPT-4o!
        elif 'deepseek-v3' in model:
            return 0.80
        elif 'llama-3.3' in model:
            return 0.75
        elif 'gemma' in model or 'phi' in model:
            return 0.65
        else:
            return 0.60

    def _estimate_cost(self, model: str, context: ModelSelectionContext) -> float:
        """Estimate cost for using this model"""
        model_costs = self.config['cost_tracking']['model_costs']

        if model in model_costs:
            input_cost, output_cost = model_costs[model]
            # Estimate tokens based on task complexity
            est_input_tokens = 1000 * (1 + context.task_complexity)
            est_output_tokens = 2000 * (1 + context.task_complexity)

            total_cost = (est_input_tokens * input_cost / 1_000_000 +
                         est_output_tokens * output_cost / 1_000_000)
            return total_cost

        # Open source models are free
        if any(provider in model for provider in
               ['llama', 'qwen', 'deepseek', 'mistral', 'granite', 'gemma', 'phi']):
            return 0.0

        # Default estimate for unknown models
        return 5.0

    def _estimate_latency(self, model: str) -> float:
        """Estimate latency in seconds for a model"""
        # Rough estimates based on model size
        if 'flash' in model or 'mini' in model:
            return 2.0
        elif 'small' in model or '4b' in model or '7b' in model or '8b' in model:
            return 3.0
        elif '32b' in model or '34b' in model:
            return 5.0
        elif '70b' in model or '72b' in model:
            return 8.0
        elif 'v3' in model:  # DeepSeek V3 (671B but MoE)
            return 10.0
        elif 'gpt-5' in model or 'claude-4' in model:
            return 12.0
        else:
            return 7.0

    def _explain_selection(self,
                          model: str,
                          strategy: Strategy,
                          context: ModelSelectionContext) -> str:
        """Explain why this model was selected"""
        explanations = []

        # Strategy explanation
        strategy_info = self.config['strategies'][strategy.value]
        explanations.append(f"Using {strategy_info['name']} strategy: {strategy_info['description']}")

        # Model characteristics
        quality = self._get_quality_score(model)
        cost = self._estimate_cost(model, context)

        if cost == 0:
            explanations.append(f"Selected {model} (open-source, free)")
        else:
            explanations.append(f"Selected {model} (${cost:.2f} estimated)")

        explanations.append(f"Quality score: {quality:.1%}")

        # Context factors
        if context.task_complexity > 0.8:
            explanations.append("High complexity task - prioritizing capability")
        if context.remaining_budget < 50:
            explanations.append("Low budget - favoring cost-effective models")
        if context.sensitive_data:
            explanations.append("Sensitive data - using privacy-focused selection")

        return " | ".join(explanations)

    def get_summary(self) -> Dict:
        """Get summary of model selection statistics"""
        return {
            'current_strategy': self.current_strategy.value,
            'total_cost': self.total_cost,
            'task_count': self.task_count,
            'avg_cost_per_task': self.total_cost / max(1, self.task_count),
            'remaining_daily_budget': self.config['cost_tracking']['budget_limits']['daily'] - self.total_cost,
        }

    def recommend_strategy(self, user_profile: Dict) -> Strategy:
        """Recommend a strategy based on user profile"""
        # Analyze user needs
        if user_profile.get('enterprise', False):
            return Strategy.QUALITY_FIRST
        elif user_profile.get('student', False) or user_profile.get('hobbyist', False):
            return Strategy.COST_FIRST
        elif user_profile.get('startup', False):
            return Strategy.BALANCED
        elif user_profile.get('real_time', False):
            return Strategy.SPEED_FIRST
        elif user_profile.get('healthcare', False) or user_profile.get('finance', False):
            return Strategy.PRIVACY_FIRST
        else:
            return Strategy.BALANCED


# Interactive strategy selection
def interactive_setup():
    """Interactive setup for user preference"""
    print("\n[GOAL] Model Selection Strategy Setup")
    print("="*50)
    print("\nChoose your priority:")
    print("1. QUALITY_FIRST - Best models, regardless of cost")
    print("2. COST_FIRST - Free open-source models only")
    print("3. BALANCED - Smart mix for best value")
    print("4. SPEED_FIRST - Fastest response times")
    print("5. PRIVACY_FIRST - Local models only, no cloud")

    choice = input("\nEnter your choice (1-5) [default: 3]: ").strip()

    strategy_map = {
        '1': Strategy.QUALITY_FIRST,
        '2': Strategy.COST_FIRST,
        '3': Strategy.BALANCED,
        '4': Strategy.SPEED_FIRST,
        '5': Strategy.PRIVACY_FIRST,
    }

    return strategy_map.get(choice, Strategy.BALANCED)


# Example usage
if __name__ == "__main__":
    # Initialize selector
    selector = StrategySelector()

    # Interactive setup
    user_strategy = interactive_setup()
    selector.set_user_strategy(user_strategy)

    # Example task
    context = ModelSelectionContext(
        task_type="coding",
        task_complexity=0.7,
        remaining_budget=50.0,
        sensitive_data=False
    )

    # Select model for coder agent
    model, info = selector.select_model("coder", context)

    print(f"\n[OK] Selected Model: {model}")
    print(f"[CHART] Strategy: {info['strategy_used']}")
    print(f"[COST] Estimated Cost: ${info['estimated_cost']:.2f}")
    print(f"[STAR] Quality Score: {info['quality_score']:.1%}")
    print(f"Documenter Reason: {info['reason']}")

    # Show summary
    summary = selector.get_summary()
    print(f"\n[UP] Session Summary:")
    print(f"   Total Cost: ${summary['total_cost']:.2f}")
    print(f"   Tasks: {summary['task_count']}")
    print(f"   Remaining Budget: ${summary['remaining_daily_budget']:.2f}")