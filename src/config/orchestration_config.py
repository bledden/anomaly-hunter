"""
Configuration loader for orchestration system (timeouts, stage multipliers, etc.)
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class OrchestrationConfig:
    """Loads and manages orchestration configuration"""

    DEFAULT_CONFIG_PATH = "config/evaluation.yaml"  # Same file as evaluation config

    def __init__(self, config_path: Optional[str] = None):
        """
        Load orchestration configuration from YAML file.

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
                logger.info(f"Loaded orchestration config from {self.config_path}")
                return config

        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'orchestration': {
                'timeouts': {
                    'total_budget_seconds': 900.0,
                    'default_stage_timeout': 180.0,
                    'stage_multipliers': {
                        'architecture': 1.5,
                        'implementation': 1.2,
                        'review': 1.0,
                        'refinement': 1.0,
                        'documentation': 1.0,
                        'testing': 1.0
                    }
                }
            }
        }

    # Convenience getters with environment variable overrides
    def get_total_budget(self) -> float:
        """Get total execution budget in seconds (env var: ORCHESTRATION_TOTAL_BUDGET)"""
        env_val = os.getenv('ORCHESTRATION_TOTAL_BUDGET')
        if env_val:
            try:
                return float(env_val)
            except ValueError:
                logger.warning(f"Invalid ORCHESTRATION_TOTAL_BUDGET: {env_val}, using config value")

        return self.config.get('orchestration', {}).get('timeouts', {}).get('total_budget_seconds', 900.0)

    def get_default_stage_timeout(self) -> float:
        """Get default stage timeout in seconds (env var: ORCHESTRATION_DEFAULT_TIMEOUT)"""
        env_val = os.getenv('ORCHESTRATION_DEFAULT_TIMEOUT')
        if env_val:
            try:
                return float(env_val)
            except ValueError:
                logger.warning(f"Invalid ORCHESTRATION_DEFAULT_TIMEOUT: {env_val}, using config value")

        return self.config.get('orchestration', {}).get('timeouts', {}).get('default_stage_timeout', 180.0)

    def get_stage_multiplier(self, stage_name: str) -> float:
        """
        Get timeout multiplier for a specific stage.

        Args:
            stage_name: Name of stage (architecture, implementation, review, etc.)

        Returns:
            Multiplier to apply to default_stage_timeout (defaults to 1.0 if not found)
        """
        # Check for stage-specific environment variable
        env_var = f'ORCHESTRATION_MULTIPLIER_{stage_name.upper()}'
        env_val = os.getenv(env_var)
        if env_val:
            try:
                return float(env_val)
            except ValueError:
                logger.warning(f"Invalid {env_var}: {env_val}, using config value")

        multipliers = self.config.get('orchestration', {}).get('timeouts', {}).get('stage_multipliers', {})
        return multipliers.get(stage_name, 1.0)

    def get_stage_timeout(self, stage_name: str) -> float:
        """
        Calculate timeout for a specific stage.

        Args:
            stage_name: Name of stage (architecture, implementation, review, etc.)

        Returns:
            Timeout in seconds (default_stage_timeout * stage_multiplier)
        """
        default_timeout = self.get_default_stage_timeout()
        multiplier = self.get_stage_multiplier(stage_name)
        return default_timeout * multiplier


# Singleton instance
_config_instance: Optional[OrchestrationConfig] = None


def get_orchestration_config(config_path: Optional[str] = None) -> OrchestrationConfig:
    """
    Get singleton instance of OrchestrationConfig.

    Args:
        config_path: Optional path to config file (only used on first call)

    Returns:
        OrchestrationConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = OrchestrationConfig(config_path)
    return _config_instance
