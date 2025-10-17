"""
Interactive Fallback Manager
Handles model failures with user-friendly prompting and smart defaults
"""

import yaml
import os
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

console = Console()


class FallbackMode(Enum):
    """Fallback behavior modes"""
    INTERACTIVE = "interactive"  # Prompt user on failures
    AUTO = "auto"  # Auto-escalate based on rules
    STRICT = "strict"  # Never escalate, fail fast


class ModelTier(Enum):
    """Model tiers by cost/performance"""
    TIER_1 = 1  # Premium (e.g., GPT-5, Claude Opus)
    TIER_2 = 2  # Balanced (e.g., Claude Sonnet, DeepSeek)
    TIER_3 = 3  # Budget (e.g., Llama, Qwen)


@dataclass
class ModelInfo:
    """Information about a model"""
    id: str
    tier: ModelTier
    cost_per_million: float  # Cost per 1M tokens
    description: str
    provider: str  # "openai", "anthropic", "open-source"


@dataclass
class FallbackContext:
    """Context for fallback decisions"""
    agent_type: str
    task_description: str
    failed_model: str
    error_type: str  # "rate_limit", "api_error", "timeout", "invalid_model"
    error_message: str
    attempt_number: int
    session_cost: float  # Cumulative cost so far
    estimated_cost: float  # Estimated cost of next attempt


class FallbackManager:
    """Manages model fallback strategy with interactive prompts"""

    def __init__(self, config_path: str = "config/config.yaml", config_dict: Optional[Dict] = None):
        self.config_path = config_path
        # Use provided config dict if available, otherwise load from file
        self.config = config_dict if config_dict is not None else self._load_config()
        self.fallback_mode = None  # Will be set by user or config
        self.user_preferences = {}  # Track user choices
        self.session_cost = 0.0

        # Model catalog with pricing info
        self.model_catalog = self._build_model_catalog()

    def _load_config(self) -> Dict:
        """Load configuration from YAML"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            console.print(f"[yellow]Config file not found: {self.config_path}[/yellow]")
            return {}

    def _build_model_catalog(self) -> Dict[str, ModelInfo]:
        """Build catalog of available models with metadata"""
        return {
            # Tier 1 - Premium Models
            "openai/gpt-5": ModelInfo(
                id="openai/gpt-5",
                tier=ModelTier.TIER_1,
                cost_per_million=5.00,
                description="74.9% SWE-bench, best overall (July 2025)",
                provider="openai"
            ),
            "openai/gpt-5-pro": ModelInfo(
                id="openai/gpt-5-pro",
                tier=ModelTier.TIER_1,
                cost_per_million=7.50,
                description="94.6% AIME, best reasoning (July 2025)",
                provider="openai"
            ),
            "anthropic/claude-opus-4.1": ModelInfo(
                id="anthropic/claude-opus-4.1",
                tier=ModelTier.TIER_1,
                cost_per_million=6.00,
                description="78% AIME, trusted safety (June 2025)",
                provider="anthropic"
            ),
            "anthropic/claude-sonnet-4.5": ModelInfo(
                id="anthropic/claude-sonnet-4.5",
                tier=ModelTier.TIER_1,
                cost_per_million=3.00,
                description="Highest pass@5, catches unique bugs (Sept 2025)",
                provider="anthropic"
            ),
            "mistralai/codestral-2501": ModelInfo(
                id="mistralai/codestral-2501",
                tier=ModelTier.TIER_1,
                cost_per_million=0.90,
                description="95.3% success, 80+ languages (Jan 2025)",
                provider="mistral"
            ),

            # Tier 2 - Balanced Models
            "deepseek/deepseek-chat": ModelInfo(
                id="deepseek/deepseek-chat",
                tier=ModelTier.TIER_2,
                cost_per_million=0.27,
                description="SOTA code gen, 85% perf at 10% cost (Jan 2025)",
                provider="open-source"
            ),
            "anthropic/claude-3-7-sonnet": ModelInfo(
                id="anthropic/claude-3-7-sonnet",
                tier=ModelTier.TIER_2,
                cost_per_million=2.00,
                description="Complex workflows specialist (Feb 2025)",
                provider="anthropic"
            ),
            "openai/o4-mini-high": ModelInfo(
                id="openai/o4-mini-high",
                tier=ModelTier.TIER_2,
                cost_per_million=1.50,
                description="Latest reasoning model (Sept 2025)",
                provider="openai"
            ),

            # Tier 3 - Budget Models
            "qwen/qwen3-coder-plus": ModelInfo(
                id="qwen/qwen3-coder-plus",
                tier=ModelTier.TIER_3,
                cost_per_million=0.20,
                description="Matches GPT-4o, best open-source (2025)",
                provider="open-source"
            ),
            "meta-llama/llama-3.3-70b-instruct": ModelInfo(
                id="meta-llama/llama-3.3-70b-instruct",
                tier=ModelTier.TIER_3,
                cost_per_million=0.18,
                description="Meta's latest 70B model (Jan 2025)",
                provider="open-source"
            ),
            "nvidia/llama-3.3-nemotron-70b-instruct": ModelInfo(
                id="nvidia/llama-3.3-nemotron-70b-instruct",
                tier=ModelTier.TIER_3,
                cost_per_million=0.19,
                description="Enhanced Llama from Nvidia (Jan 2025)",
                provider="open-source"
            ),
        }

    def prompt_initial_strategy(self) -> FallbackMode:
        """
        Prompt user BEFORE task submission to choose fallback strategy
        This runs once at the start of the session
        """
        # Check if user has configured fallback in config.yaml
        config_mode = self.config.get("fallback", {}).get("mode")

        if config_mode:
            # Use configured mode without prompting
            self.fallback_mode = FallbackMode(config_mode)
            console.print(f"[green][OK][/green] Using configured fallback mode: [bold]{config_mode}[/bold]")
            return self.fallback_mode

        # No config found, show interactive prompt
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]Model Fallback Strategy[/bold cyan]\n\n"
            "Choose how to handle model failures during execution:",
            border_style="cyan"
        ))

        # Show options to user
        console.print("\n[bold]Options:[/bold]\n")
        console.print("  [cyan]1. Interactive[/cyan] - Prompt me when models fail (recommended for first time)")
        console.print("  [cyan]2. Auto[/cyan] - Automatically try fallback models based on smart rules")
        console.print("  [cyan]3. Strict[/cyan] - Never use fallback models, fail fast\n")

        choice = Prompt.ask(
            "Select fallback strategy",
            choices=["1", "2", "3", "interactive", "auto", "strict"],
            default="1"
        )

        # Map choice to mode
        mode_map = {
            "1": FallbackMode.INTERACTIVE,
            "2": FallbackMode.AUTO,
            "3": FallbackMode.STRICT,
            "interactive": FallbackMode.INTERACTIVE,
            "auto": FallbackMode.AUTO,
            "strict": FallbackMode.STRICT,
        }

        self.fallback_mode = mode_map[choice]

        # Suggest saving to config
        if self.fallback_mode != FallbackMode.INTERACTIVE:
            console.print(f"\n[yellow][IDEA] Tip:[/yellow] Save this preference by adding to config.yaml:")
            console.print(f"[dim]fallback:")
            console.print(f"  mode: \"{self.fallback_mode.value}\"[/dim]\n")

        return self.fallback_mode

    def handle_model_failure(self, context: FallbackContext) -> Optional[str]:
        """
        Handle a model failure and return the next model to try
        Returns None if user wants to abort
        """
        # If mode not set yet, prompt user
        if self.fallback_mode is None:
            self.fallback_mode = self.prompt_initial_strategy()

        # Handle based on mode
        if self.fallback_mode == FallbackMode.STRICT:
            return self._handle_strict_mode(context)
        elif self.fallback_mode == FallbackMode.AUTO:
            return self._handle_auto_mode(context)
        else:  # INTERACTIVE
            return self._handle_interactive_mode(context)

    def _handle_strict_mode(self, context: FallbackContext) -> Optional[str]:
        """Strict mode: fail immediately"""
        console.print(f"\n[red][FAIL] Model failed:[/red] {context.failed_model}")
        console.print(f"[red]Error:[/red] {context.error_message}")
        console.print(f"[yellow]Strict mode enabled - no fallback attempted[/yellow]\n")
        return None

    def _handle_auto_mode(self, context: FallbackContext) -> Optional[str]:
        """Auto mode: automatically select fallback based on rules"""
        failed_model_info = self.model_catalog.get(context.failed_model)

        # Get candidate models from config
        agent_config = self.config.get("agents", {}).get(context.agent_type, {})
        candidate_models = agent_config.get("candidate_models", [])

        if not failed_model_info:
            # Unknown model - just try the next candidate in the list
            console.print(f"[yellow][WARNING]  Model failed:[/yellow] {context.failed_model} (unknown model)")

            # Find the next available candidate after the failed one
            next_model = None
            found_failed = False
            for model_id in candidate_models:
                if found_failed:
                    next_model = model_id
                    break
                if model_id == context.failed_model:
                    found_failed = True

            if next_model:
                next_info = self.model_catalog.get(next_model)
                console.print(f"[green][REFRESH] Auto-fallback:[/green] Trying {next_model}")
                if next_info:
                    console.print(f"[dim]   {next_info.description}[/dim]")
                    console.print(f"[dim]   Cost: ${next_info.cost_per_million}/M tokens[/dim]\n")
                else:
                    console.print(f"[dim]   (Model not in catalog)[/dim]\n")
            else:
                console.print(f"[red][FAIL] No more fallback models available[/red]\n")

            return next_model

        # Filter candidates by tier and availability
        next_model = self._select_auto_fallback(
            failed_model_info,
            candidate_models,
            context
        )

        if next_model:
            next_info = self.model_catalog.get(next_model)
            console.print(f"\n[yellow][WARNING]  Model failed:[/yellow] {context.failed_model}")
            console.print(f"[green][REFRESH] Auto-fallback:[/green] Trying {next_model}")
            if next_info:
                console.print(f"[dim]   {next_info.description}[/dim]")
                console.print(f"[dim]   Cost: ${next_info.cost_per_million}/M tokens[/dim]\n")
        else:
            console.print(f"[red][FAIL] No suitable fallback found[/red]\n")

        return next_model

    def _handle_interactive_mode(self, context: FallbackContext) -> Optional[str]:
        """Interactive mode: prompt user with options"""
        console.print("\n")
        console.print(Panel.fit(
            f"[bold red][FAIL] Model Failure[/bold red]\n\n"
            f"[bold]Agent:[/bold] {context.agent_type}\n"
            f"[bold]Model:[/bold] {context.failed_model}\n"
            f"[bold]Error:[/bold] {context.error_type}\n"
            f"[bold]Message:[/bold] {context.error_message}\n"
            f"[bold]Attempt:[/bold] {context.attempt_number}",
            border_style="red"
        ))

        # Get available fallback options
        options = self._get_fallback_options(context)

        if not options:
            console.print("[red]No fallback models available[/red]")
            return None

        # Display options in a table
        table = Table(title="[REFRESH] Fallback Options", show_header=True, header_style="bold cyan")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Model", style="white")
        table.add_column("Tier", style="yellow")
        table.add_column("Cost/M", style="green")
        table.add_column("Description", style="dim")

        for i, (model_id, model_info) in enumerate(options.items(), 1):
            tier_emoji = "[STAR]" if model_info.tier == ModelTier.TIER_1 else "[PREMIUM]" if model_info.tier == ModelTier.TIER_2 else "[COST]"
            table.add_row(
                str(i),
                model_id,
                f"{tier_emoji} Tier {model_info.tier.value}",
                f"${model_info.cost_per_million:.2f}",
                model_info.description[:60] + "..." if len(model_info.description) > 60 else model_info.description
            )

        # Add control options
        table.add_row("", "", "", "", "", style="dim")
        table.add_row("S", "[bold]Skip this step[/bold]", "", "", "Use previous output")
        table.add_row("A", "[bold]Abort task[/bold]", "", "", "Stop execution")
        table.add_row("C", "[bold]Switch to Auto mode[/bold]", "", "", "Auto-select for rest of session")

        console.print(table)
        console.print()

        # Show budget info
        if context.session_cost > 0:
            console.print(f"[dim]Session cost so far: ${context.session_cost:.2f}[/dim]")

        # Prompt user
        valid_choices = [str(i) for i in range(1, len(options) + 1)] + ["s", "a", "c", "S", "A", "C"]
        choice = Prompt.ask(
            "Your choice",
            choices=valid_choices,
            default="1"
        )

        # Handle choice
        choice_lower = choice.lower()

        if choice_lower == "s":
            console.print("[yellow]⏭  Skipping this step[/yellow]\n")
            return "__SKIP__"  # Special token to skip
        elif choice_lower == "a":
            console.print("[red][STOP] Aborting task[/red]\n")
            return None
        elif choice_lower == "c":
            console.print("[green][OK] Switched to Auto mode for rest of session[/green]\n")
            self.fallback_mode = FallbackMode.AUTO
            return self._handle_auto_mode(context)
        else:
            # Select model by number
            model_index = int(choice) - 1
            selected_model = list(options.keys())[model_index]
            selected_info = options[selected_model]

            console.print(f"[green][OK] Selected:[/green] {selected_model}")
            console.print(f"[dim]  {selected_info.description}[/dim]\n")

            # Suggest saving preference
            if context.attempt_number == 1:  # First failure
                console.print("[yellow][IDEA] Tip:[/yellow] To avoid these prompts, configure fallback in config.yaml")
                console.print(f"[dim]See: {self.config_path}[/dim]\n")

            return selected_model

    def _get_fallback_options(self, context: FallbackContext) -> Dict[str, ModelInfo]:
        """Get available fallback options based on context"""
        failed_model_info = self.model_catalog.get(context.failed_model)

        # Get candidate models from config
        agent_config = self.config.get("agents", {}).get(context.agent_type, {})
        candidate_models = agent_config.get("candidate_models", [])

        # Build options dict (model_id -> ModelInfo)
        options = {}

        for model_id in candidate_models:
            if model_id == context.failed_model:
                continue  # Don't suggest the failed model

            model_info = self.model_catalog.get(model_id)
            if model_info:
                options[model_id] = model_info

        # Sort by tier (higher tier first for fallback)
        sorted_options = dict(sorted(
            options.items(),
            key=lambda x: (x[1].tier.value, x[1].cost_per_million)
        ))

        return sorted_options

    def _select_auto_fallback(
        self,
        failed_model_info: ModelInfo,
        candidate_models: List[str],
        context: FallbackContext
    ) -> Optional[str]:
        """Automatically select next fallback model based on smart rules"""

        # Rule 1: For rate limits, try another model in same tier first
        if context.error_type == "rate_limit":
            for model_id in candidate_models:
                if model_id == context.failed_model:
                    continue
                model_info = self.model_catalog.get(model_id)
                if model_info and model_info.tier == failed_model_info.tier:
                    return model_id

        # Rule 2: For API errors or invalid models, escalate one tier
        if context.error_type in ["api_error", "invalid_model"]:
            target_tier = ModelTier(max(1, failed_model_info.tier.value - 1))
            for model_id in candidate_models:
                if model_id == context.failed_model:
                    continue
                model_info = self.model_catalog.get(model_id)
                if model_info and model_info.tier == target_tier:
                    return model_id

        # Rule 3: For timeout, try faster model in same or lower tier
        if context.error_type == "timeout":
            for model_id in candidate_models:
                if model_id == context.failed_model:
                    continue
                model_info = self.model_catalog.get(model_id)
                if model_info and model_info.tier.value >= failed_model_info.tier.value:
                    return model_id

        # Fallback: return first available candidate
        for model_id in candidate_models:
            if model_id != context.failed_model:
                return model_id

        return None


# Example usage
if __name__ == "__main__":
    manager = FallbackManager()

    # Simulate initial strategy selection
    mode = manager.prompt_initial_strategy()
    print(f"Selected mode: {mode}")

    # Simulate a failure
    context = FallbackContext(
        agent_type="coder",
        task_description="Implement factorial function",
        failed_model="meta-llama/llama-3.3-70b-instruct",
        error_type="rate_limit",
        error_message="Rate limit exceeded (429)",
        attempt_number=1,
        session_cost=2.50,
        estimated_cost=0.20
    )

    next_model = manager.handle_model_failure(context)
    print(f"Next model: {next_model}")
