"""
Configuration loader for enhanced evaluation system
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EvaluationConfig:
    """Loads and manages evaluation system configuration"""

    DEFAULT_CONFIG_PATH = "config/evaluation.yaml"

    def __init__(self, config_path: Optional[str] = None):
        """
        Load evaluation configuration from YAML file.

        Args:
            config_path: Path to config file (defaults to config/evaluation.yaml)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.warning(f"Config file not found: {self.config_path}, using defaults")
                return self._get_default_config()

            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded evaluation config from {self.config_path}")
                return config

        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'evaluation': {
                'enabled': True,
                'hooks': {
                    'post_refiner': True,
                    'post_documenter': False
                },
                'gate_on_failure': False,
                'pass_threshold': 0.7,
                'evaluators': {
                    'security': {
                        'enabled': True,
                        'weight': 0.30,
                        'min_score': 0.6,
                        'severity_threshold': 'MEDIUM'
                    },
                    'static_analysis': {
                        'enabled': True,
                        'weight': 0.30,
                        'min_score': 0.6,
                        'pylint_threshold': 7.0,
                        'flake8_max_violations': 20,
                        'mypy_max_errors': 10
                    },
                    'complexity': {
                        'enabled': True,
                        'weight': 0.20,
                        'min_score': 0.6,
                        'max_acceptable_complexity': 10,
                        'min_maintainability': 20.0
                    },
                    'llm_judge': {
                        'enabled': True,
                        'weight': 0.20,
                        'min_score': 0.6,
                        'model': 'anthropic/claude-3.5-sonnet',
                        'temperature': 0.3
                    }
                },
                'timeouts': {
                    'security': 30,
                    'static_analysis': 30,
                    'complexity': 30,
                    'llm_judge': 60
                },
                'logging': {
                    'log_to_weave': True,
                    'log_to_console': True,
                    'verbose': False
                }
            }
        }

    # Convenience getters
    def is_enabled(self) -> bool:
        """Check if evaluation system is enabled"""
        return self.config.get('evaluation', {}).get('enabled', True)

    def should_run_post_refiner(self) -> bool:
        """Check if evaluations should run after refiner"""
        return self.config.get('evaluation', {}).get('hooks', {}).get('post_refiner', True)

    def should_run_post_documenter(self) -> bool:
        """Check if evaluations should run after documenter"""
        return self.config.get('evaluation', {}).get('hooks', {}).get('post_documenter', False)

    def is_evaluator_enabled(self, evaluator_name: str) -> bool:
        """Check if a specific evaluator is enabled"""
        evaluators = self.config.get('evaluation', {}).get('evaluators', {})
        return evaluators.get(evaluator_name, {}).get('enabled', True)

    def get_evaluator_config(self, evaluator_name: str) -> Dict[str, Any]:
        """Get configuration for a specific evaluator"""
        evaluators = self.config.get('evaluation', {}).get('evaluators', {})
        return evaluators.get(evaluator_name, {})

    def get_pass_threshold(self) -> float:
        """Get overall pass threshold"""
        return self.config.get('evaluation', {}).get('pass_threshold', 0.7)

    def should_gate_on_failure(self) -> bool:
        """Check if workflow should block on evaluation failure"""
        return self.config.get('evaluation', {}).get('gate_on_failure', False)

    def get_timeout(self, evaluator_name: str) -> int:
        """Get timeout for specific evaluator"""
        timeouts = self.config.get('evaluation', {}).get('timeouts', {})
        return timeouts.get(evaluator_name, 30)

    def should_log_to_weave(self) -> bool:
        """Check if should log to W&B Weave"""
        return self.config.get('evaluation', {}).get('logging', {}).get('log_to_weave', True)

    def should_log_to_console(self) -> bool:
        """Check if should log to console"""
        return self.config.get('evaluation', {}).get('logging', {}).get('log_to_console', True)

    def is_verbose(self) -> bool:
        """Check if verbose logging is enabled"""
        return self.config.get('evaluation', {}).get('logging', {}).get('verbose', False)
