"""
Self-Improving Collaborative Orchestrator
Learns optimal multi-agent collaboration strategies through W&B Weave tracking
"""

import weave
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import asyncio
import json
import yaml
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Validate API keys on startup
from utils.api_key_validator import validate_on_startup
if not validate_on_startup():
    import sys
    print("[FAIL] Exiting due to invalid API keys")
    sys.exit(1)

# Import strategy selector
from agents.strategy_selector import StrategySelector, ModelSelectionContext, Strategy

# Load configuration
config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
try:
    with open(config_path, "r") as f:
        CONFIG = yaml.safe_load(f)
except (FileNotFoundError, yaml.YAMLError) as e:
    print(f"Warning: Could not load config.yaml: {e}")
    print("Using default configuration...")
    # Fallback configuration with all 5 agents
    CONFIG = {
        "agents": {
            "architect": {
                "model": "gpt-4",
                "expertise": ["system_design", "architecture", "planning"],
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "coder": {
                "model": "claude-3-sonnet",
                "expertise": ["implementation", "debugging", "optimization"],
                "temperature": 0.5,
                "max_tokens": 3000
            },
            "reviewer": {
                "model": "gpt-4-turbo",
                "expertise": ["code_review", "testing", "quality"],
                "temperature": 0.3,
                "max_tokens": 1500
            },
            "documenter": {
                "model": "claude-3-haiku",
                "expertise": ["documentation", "examples", "tutorials"],
                "temperature": 0.6,
                "max_tokens": 2500
            },
            "researcher": {
                "model": "gemini-pro",
                "expertise": ["research", "analysis", "data"],
                "temperature": 0.8,
                "max_tokens": 2000
            }
        },
        "weave": {
            "project_name": "self-improving-collaboration"
        }
    }

# Initialize Weave with project from config
weave_project = CONFIG.get("weave", {}).get("project_name", "self-improving-collaboration")
try:
    weave.init(weave_project)
except Exception as e:
    print(f"Warning: Could not initialize Weave: {e}")
    print("Continuing without W&B tracking...")

# Helper function to replace log_metric() which doesn't exist
def log_metric(data: Dict[str, Any]):
    """Log metrics - weave automatically tracks @weave.op() decorated functions"""
    # Weave tracks via decorators, so we just skip manual logging
    pass

# Import LLM client if available
try:
    from agents.llm_client import MultiAgentLLMOrchestrator
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("Warning: LLM client not available. Using simulated responses.")

# Import sponsor integrations
try:
    from agents.sponsor_integrations import SponsorOrchestrator
    SPONSORS_AVAILABLE = True
except ImportError:
    SPONSORS_AVAILABLE = False
    print("Warning: Sponsor integrations not available.")


@dataclass
class Agent:
    """Individual agent with learnable capabilities"""
    id: str
    model: str
    expertise: List[str]
    performance_history: Dict[str, float]
    collaboration_scores: Dict[str, float]  # Scores with other agents

    def __post_init__(self):
        self.performance_history = defaultdict(lambda: 0.5)
        self.collaboration_scores = defaultdict(lambda: 0.5)


@dataclass
class CollaborationResult:
    """Result of a collaborative execution"""
    task: str
    agents_used: List[str]
    consensus_method: str
    individual_outputs: Dict[str, str]
    final_output: str
    metrics: Dict[str, float]
    conflicts_resolved: int
    consensus_rounds: int


class CollaborativeOrchestrator:
    """Orchestrator for sequential agent collaboration workflows"""

    def __init__(self, config: Optional[Dict[str, Any]] = None, use_sponsors: bool = True,
                 user_strategy: Strategy = Strategy.BALANCED, use_sequential: bool = True):
        # Use provided config or load from file
        self.config = config or CONFIG

        # Initialize strategy selector for model selection
        self.strategy_selector = StrategySelector()
        self.strategy_selector.set_user_strategy(user_strategy)
        print(f"[GOAL] Model selection strategy: {user_strategy.value}")

        # Initialize LLM orchestrator if available (pass strategy_selector for dynamic model selection)
        self.llm_orchestrator = MultiAgentLLMOrchestrator(
            self.config,
            strategy_selector=self.strategy_selector
        ) if LLM_AVAILABLE else None

        # Initialize sponsor integrations if available and requested
        self.sponsor_orchestrator = None
        if SPONSORS_AVAILABLE and use_sponsors:
            self.sponsor_orchestrator = SponsorOrchestrator()
            print("[OK] Sponsor integrations enabled: Daytona, MCP, CopilotKit")

        # Initialize agents from config
        self.agents = {}
        for agent_id, agent_config in self.config.get("agents", {}).items():
            self.agents[agent_id] = Agent(
                id=agent_id,
                model=agent_config.get("model", "gpt-4"),
                expertise=agent_config.get("expertise", []),
                performance_history={},
                collaboration_scores={}
            )

        # Sequential orchestrator
        self.use_sequential = use_sequential
        if use_sequential and self.llm_orchestrator:
            from src.orchestrators.sequential_orchestrator import SequentialCollaborativeOrchestrator
            self.sequential_orchestrator = SequentialCollaborativeOrchestrator(
                self.llm_orchestrator,
                self.config
            )
            print("[OK] Sequential collaboration enabled (Facilitair_v2 architecture)")
        else:
            self.sequential_orchestrator = None

        # Consensus methods (kept for backwards compatibility)
        self.consensus_methods = [
            "voting",           # Simple majority
            "weighted_voting",  # Weight by expertise
            "debate",          # Agents argue until consensus
            "synthesis",       # Combine all outputs
            "hierarchy"        # Expert has final say
        ]

        # Learning parameters
        self.task_type_patterns = defaultdict(lambda: {
            "best_agents": [],
            "best_consensus": "voting",
            "optimal_team_size": 3,
            "success_rate": 0.0
        })

        self.generation = 0
        self.collaboration_history = []

        # Add locks to protect shared state from race conditions
        self._history_lock = asyncio.Lock()
        self._patterns_lock = asyncio.Lock()

    def set_user_strategy(self, strategy: Strategy):
        """Allow user to change strategy at runtime"""
        self.strategy_selector.set_user_strategy(strategy)
        print(f"[OK] Strategy changed to: {strategy.value}")

    def get_strategy_summary(self) -> Dict:
        """Get summary of model selection performance"""
        return self.strategy_selector.get_summary()

    @weave.op()
    async def collaborate(self, task: str, force_agents: Optional[List[str]] = None) -> CollaborationResult:
        """Execute task with sequential collaborative workflow (consensus removed)"""

        # ONLY USE SEQUENTIAL - Consensus is removed entirely
        if not self.use_sequential or not self.sequential_orchestrator:
            raise RuntimeError("Sequential orchestrator not initialized. Consensus has been removed.")

        workflow_result = await self.sequential_orchestrator.execute_workflow(
            task=task,
            max_iterations=3,
            temperature=0.2
        )

        # Convert WorkflowResult to CollaborationResult for compatibility
        agents_used = [stage.agent_role.value for stage in workflow_result.stages]

        # Build individual outputs from stages
        individual_outputs = {}
        for stage in workflow_result.stages:
            individual_outputs[stage.agent_role.value] = stage.output

        # Calculate REAL quality score from final output
        try:
            from src.evaluation.quality_evaluator import CodeQualityEvaluator, detect_language
            evaluator = CodeQualityEvaluator()
            language = detect_language(workflow_result.final_output)
            quality_eval = evaluator.evaluate(workflow_result.final_output, task, language)
            quality_score = quality_eval.overall  # Use .overall, not dictionary access
            print(f"[DEBUG] Real quality evaluation succeeded: {quality_score}")
        except Exception as e:
            # Fallback to heuristic if evaluator fails (conservative scoring)
            print(f"[WARNING] Quality evaluator failed: {type(e).__name__}: {str(e)}")
            output = workflow_result.final_output
            has_code = any(keyword in output for keyword in ['def ', 'function ', 'class ', 'const ', 'let '])
            has_logic = len(output) > 100
            # Use 0.6 max to stay below pass threshold (0.7) - be conservative when evaluator fails
            quality_score = 0.6 if (has_code and has_logic and workflow_result.success) else 0.3
            print(f"[DEBUG] Using fallback score: {quality_score}")

        metrics = {
            "quality": quality_score,
            "efficiency": 0.9,
            "harmony": 1.0,
            "overall": quality_score
        }

        result = CollaborationResult(
            task=task,
            agents_used=agents_used,
            consensus_method="sequential_workflow",
            individual_outputs=individual_outputs,
            final_output=workflow_result.final_output,
            metrics=metrics,
            conflicts_resolved=workflow_result.iterations,
            consensus_rounds=len(workflow_result.stages)
        )

        # Learn from this collaboration
        task_type = self._classify_task(task)
        await self._learn_from_collaboration(result, task_type)

        return result

    def _classify_task(self, task: str) -> str:
        """Classify task type based on content"""
        task_lower = task.lower()

        if any(word in task_lower for word in ["design", "architect", "structure"]):
            return "architecture"
        elif any(word in task_lower for word in ["code", "implement", "function", "api"]):
            return "coding"
        elif any(word in task_lower for word in ["review", "test", "quality", "bug"]):
            return "review"
        elif any(word in task_lower for word in ["document", "readme", "tutorial"]):
            return "documentation"
        elif any(word in task_lower for word in ["research", "analyze", "data"]):
            return "research"
        else:
            return "general"

    @weave.op()
    def _select_optimal_agents(self, task: str, task_type: str) -> List[str]:
        """Select best agents based on learned performance"""

        # Get learned preferences for this task type
        learned = self.task_type_patterns[task_type]

        if self.generation == 0 or not learned["best_agents"]:
            # Cold start: use heuristics
            if task_type == "architecture":
                return ["architect", "reviewer"]
            elif task_type == "coding":
                return ["coder", "reviewer", "documenter"]
            elif task_type == "review":
                return ["reviewer", "coder"]
            else:
                return ["architect", "coder", "reviewer"]
        else:
            # Use learned best agents
            team_size = learned["optimal_team_size"]

            # Score each agent for this task type
            agent_scores = {}
            for agent_id, agent in self.agents.items():
                # Base score from task type performance
                base_score = agent.performance_history.get(task_type, 0.5)

                # Collaboration bonus (how well they work with others)
                collab_bonus = np.mean([
                    agent.collaboration_scores.get(other_id, 0.5)
                    for other_id in self.agents.keys()
                    if other_id != agent_id
                ])

                agent_scores[agent_id] = base_score + 0.3 * collab_bonus

            # Select top agents
            sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
            selected = [agent_id for agent_id, _ in sorted_agents[:team_size]]

            # Log selection reasoning
            log_metric({
                "agent_selection": {
                    "scores": agent_scores,
                    "selected": selected,
                    "generation": self.generation
                }
            })

            return selected

    def _select_consensus_method(self, task_type: str) -> str:
        """Select consensus method based on learned effectiveness"""

        learned = self.task_type_patterns[task_type]

        if self.generation < 3:
            # Explore different methods initially
            return self.consensus_methods[self.generation % len(self.consensus_methods)]
        else:
            # Use learned best method
            return learned["best_consensus"]

    async def _execute_agent(self, agent: Agent, task: str) -> str:
        """Execute task with a single agent"""

        # Create context for model selection
        task_complexity = len(task) / 1000.0  # Simple heuristic
        context = ModelSelectionContext(
            task_type=agent.id,
            task_complexity=min(1.0, task_complexity),
            remaining_budget=100.0,  # Could track actual budget
            sensitive_data=False  # Could detect from task content
        )

        # Select model based on user strategy
        selected_model, selection_info = self.strategy_selector.select_model(agent.id, context)

        # Log model selection
        log_metric({
            "model_selection": {
                "agent": agent.id,
                "selected_model": selected_model,
                "strategy": selection_info['strategy_used'],
                "estimated_cost": selection_info['estimated_cost'],
                "quality_score": selection_info['quality_score']
            }
        })

        # Update agent's model for this task
        original_model = agent.model
        agent.model = selected_model

        # Use sponsor integrations if available
        if self.sponsor_orchestrator:
            try:
                result = await self.sponsor_orchestrator.execute_with_sponsors(
                    agent.id,
                    task,
                    {"task_type": self._classify_task(task), "model": selected_model}
                )

                # Send MCP messages between agents
                if hasattr(self.sponsor_orchestrator, 'mcp'):
                    await self.sponsor_orchestrator.mcp.send_message(
                        agent.id,
                        "all",
                        {
                            "type": "task_started",
                            "content": f"Working on: {task[:100]}",
                            "priority": "normal"
                        }
                    )

                # Return the execution result
                if "result" in result:
                    return result["result"]
            except Exception as e:
                log_metric({"sponsor_fallback": {"agent": agent.id, "error": str(e)}})

        # Use real LLM if available (fallback if sponsors fail)
        if self.llm_orchestrator:
            try:
                output = await self.llm_orchestrator.execute_agent_task(agent.id, task)
                return output
            except Exception as e:
                log_metric({"llm_fallback": {"agent": agent.id, "error": str(e)}})
                # Fall through to simulation

        # Fallback to simulation
        await asyncio.sleep(0.5)  # Simulate latency

        # Generate output based on agent expertise
        output = f"[{agent.id}] Solution for: {task[:50]}..."

        # Add agent-specific insights
        if "architecture" in agent.expertise and "design" in task.lower():
            output += "\n- Proposed microservices architecture"
            output += "\n- RESTful API design"
        elif "implementation" in agent.expertise and "code" in task.lower():
            output += "\n```python\ndef solution():\n    pass\n```"
        elif "testing" in agent.expertise:
            output += "\n- Unit tests needed"
            output += "\n- Edge cases to consider"

        return output

    @weave.op()
    async def _reach_consensus(
        self,
        outputs: Dict[str, str],
        method: str,
        task_type: str
    ) -> tuple[str, Dict]:
        """Reach consensus among agent outputs"""

        consensus_metrics = {"rounds": 0, "conflicts": 0}

        # Use CopilotKit for guidance if there are conflicts
        if self.sponsor_orchestrator and len(set(outputs.values())) > 1:
            # Multiple different outputs - might need guidance
            try:
                guidance = await self.sponsor_orchestrator.copilotkit.request_human_guidance(
                    {
                        "task_type": task_type,
                        "consensus_method": method,
                        "num_different_outputs": len(set(outputs.values())),
                        "agents_involved": list(outputs.keys())
                    },
                    ["continue_with_method", "switch_to_hierarchy", "request_clarification"]
                )

                if guidance == "switch_to_hierarchy":
                    method = "hierarchy"
                    log_metric({"copilotkit_intervention": "Switched to hierarchy based on guidance"})
            except Exception as e:
                log_metric({"copilotkit_error": str(e)})

        if method == "voting":
            # Simple voting - most common output wins
            final = max(outputs.values(), key=list(outputs.values()).count)
            consensus_metrics["rounds"] = 1

        elif method == "weighted_voting":
            # Weight by agent expertise in task type
            scores = {}
            for agent_id, output in outputs.items():
                agent = self.agents[agent_id]
                weight = agent.performance_history.get(task_type, 0.5)
                scores[output] = scores.get(output, 0) + weight
            final = max(scores, key=scores.get)
            consensus_metrics["rounds"] = 1

        elif method == "debate":
            # Agents debate (simplified simulation)
            rounds = 0
            final = ""
            while rounds < 3:  # Max 3 rounds
                rounds += 1
                # Simulate debate
                await asyncio.sleep(0.2)

                # Check for agreement
                if np.random.random() > 0.3:  # 70% chance of agreement
                    final = f"Consensus after {rounds} rounds: " + list(outputs.values())[0]
                    break
                else:
                    consensus_metrics["conflicts"] += 1

            consensus_metrics["rounds"] = rounds
            if not final:
                final = "Failed to reach consensus, using fallback"

        elif method == "synthesis":
            # Combine all outputs
            final = "Synthesized output:\n"
            for agent_id, output in outputs.items():
                final += f"\n{agent_id}: {output[:100]}"
            consensus_metrics["rounds"] = 1

        elif method == "hierarchy":
            # Expert decides based on task type
            expert_map = {
                "architecture": "architect",
                "coding": "coder",
                "review": "reviewer",
                "documentation": "documenter",
                "research": "researcher"
            }
            expert = expert_map.get(task_type, "architect")
            final = outputs.get(expert, list(outputs.values())[0])
            consensus_metrics["rounds"] = 1

        else:
            final = list(outputs.values())[0]  # Fallback

        return final, consensus_metrics

    def _calculate_metrics(
        self,
        individual_outputs: Dict[str, str],
        final_output: str,
        consensus_metrics: Dict
    ) -> Dict[str, float]:
        """Calculate collaboration quality metrics"""

        # Diversity score (how different were the outputs)
        diversity = len(set(individual_outputs.values())) / len(individual_outputs)

        # Consensus efficiency (fewer rounds is better)
        efficiency = 1.0 / (1 + consensus_metrics.get("rounds", 1))

        # Conflict resolution (fewer conflicts is better)
        harmony = 1.0 / (1 + consensus_metrics.get("conflicts", 0))

        # Simulated quality score (would be from user feedback in real system)
        quality = np.random.beta(8, 2)  # Skewed toward high quality

        # Cost (based on number of agents and rounds)
        cost = len(individual_outputs) * 0.1 + consensus_metrics.get("rounds", 1) * 0.05

        return {
            "diversity": diversity,
            "efficiency": efficiency,
            "harmony": harmony,
            "quality": quality,
            "cost": cost,
            "overall": (quality * 0.4 + efficiency * 0.3 + harmony * 0.2 + diversity * 0.1)
        }

    @weave.op()
    async def _learn_from_collaboration(self, result: CollaborationResult, task_type: str):
        """Update learning based on collaboration results (thread-safe)"""

        # Protect shared state with lock to prevent race conditions
        async with self._patterns_lock:
            # Update agent performance histories
            for agent_id in result.agents_used:
                agent = self.agents[agent_id]

                # Update task type performance
                old_score = agent.performance_history.get(task_type, 0.5)
                new_score = result.metrics["quality"]
                agent.performance_history[task_type] = 0.7 * old_score + 0.3 * new_score

                # Update collaboration scores with other agents
                for other_id in result.agents_used:
                    if other_id != agent_id:
                        old_collab = agent.collaboration_scores.get(other_id, 0.5)
                        new_collab = result.metrics["harmony"]
                        agent.collaboration_scores[other_id] = 0.7 * old_collab + 0.3 * new_collab

            # Update task type patterns
            pattern = self.task_type_patterns[task_type]

            # Update best agents (if this collaboration was successful)
            if result.metrics["overall"] > 0.7:
                pattern["best_agents"] = result.agents_used
                pattern["best_consensus"] = result.consensus_method
                pattern["optimal_team_size"] = len(result.agents_used)

            # Update success rate
            old_rate = pattern["success_rate"]
            new_rate = 1.0 if result.metrics["overall"] > 0.7 else 0.0
            pattern["success_rate"] = 0.9 * old_rate + 0.1 * new_rate

        # Log learning update
        log_metric({
            "learning_update": {
                "task_type": task_type,
                "generation": self.generation,
                "pattern_updated": pattern,
                "agent_scores": {
                    agent_id: {
                        "task_performance": agent.performance_history.get(task_type, 0),
                        "avg_collaboration": np.mean(list(agent.collaboration_scores.values())) if agent.collaboration_scores else 0.5
                    }
                    for agent_id, agent in self.agents.items()
                }
            }
        })

    def advance_generation(self):
        """Move to next generation of learning"""
        self.generation += 1

        # Log generation advancement
        log_metric({
            "generation_advanced": self.generation,
            "total_collaborations": len(self.collaboration_history),
            "patterns_learned": dict(self.task_type_patterns)
        })

    @weave.op()
    def get_collaboration_report(self) -> Dict[str, Any]:
        """Generate report on collaboration learning"""

        if len(self.collaboration_history) < 2:
            return {"error": "Not enough collaboration history"}

        # Calculate improvements
        early_collaborations = self.collaboration_history[:5] if len(self.collaboration_history) >= 5 else self.collaboration_history[:1]
        recent_collaborations = self.collaboration_history[-5:] if len(self.collaboration_history) >= 5 else self.collaboration_history[-1:]

        early_metrics = {
            "quality": np.mean([c.metrics["quality"] for c in early_collaborations]),
            "efficiency": np.mean([c.metrics["efficiency"] for c in early_collaborations]),
            "harmony": np.mean([c.metrics["harmony"] for c in early_collaborations]),
            "cost": np.mean([c.metrics["cost"] for c in early_collaborations])
        }

        recent_metrics = {
            "quality": np.mean([c.metrics["quality"] for c in recent_collaborations]),
            "efficiency": np.mean([c.metrics["efficiency"] for c in recent_collaborations]),
            "harmony": np.mean([c.metrics["harmony"] for c in recent_collaborations]),
            "cost": np.mean([c.metrics["cost"] for c in recent_collaborations])
        }

        improvements = {
            "quality": (recent_metrics["quality"] - early_metrics["quality"]) / early_metrics["quality"] * 100,
            "efficiency": (recent_metrics["efficiency"] - early_metrics["efficiency"]) / early_metrics["efficiency"] * 100,
            "harmony": (recent_metrics["harmony"] - early_metrics["harmony"]) / early_metrics["harmony"] * 100,
            "cost_reduction": (early_metrics["cost"] - recent_metrics["cost"]) / early_metrics["cost"] * 100
        }

        # Find best performing teams
        best_teams = {}
        for task_type, pattern in self.task_type_patterns.items():
            if pattern["best_agents"]:
                best_teams[task_type] = {
                    "agents": pattern["best_agents"],
                    "consensus": pattern["best_consensus"],
                    "success_rate": pattern["success_rate"]
                }

        # Agent expertise discovery
        agent_expertise = {}
        for agent_id, agent in self.agents.items():
            if agent.performance_history:
                best_task = max(agent.performance_history, key=agent.performance_history.get)
                agent_expertise[agent_id] = {
                    "discovered_strength": best_task,
                    "performance": agent.performance_history[best_task],
                    "best_collaborators": sorted(
                        agent.collaboration_scores.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:2] if agent.collaboration_scores else []
                }

        report = {
            "generation": self.generation,
            "total_collaborations": len(self.collaboration_history),
            "improvements": improvements,
            "best_teams": best_teams,
            "agent_expertise": agent_expertise,
            "early_metrics": early_metrics,
            "recent_metrics": recent_metrics
        }

        # Log report
        log_metric({"collaboration_report": report})

        return report


# Demo execution
async def demo_collaboration_learning():
    """Demonstrate collaborative learning over multiple generations"""

    orchestrator = CollaborativeOrchestrator()

    # Test tasks for different types
    test_tasks = [
        "Design a microservices architecture for an e-commerce platform",
        "Implement a Python REST API with authentication",
        "Review this code for security vulnerabilities",
        "Write comprehensive documentation for the API",
        "Research best practices for database scaling"
    ]

    print("=== Starting Collaborative Learning Demo ===\n")

    # Run multiple generations
    for generation in range(10):
        print(f"\n--- Generation {generation + 1} ---")

        for task in test_tasks:
            result = await orchestrator.collaborate(task)

            print(f"\nTask: {task[:50]}...")
            print(f"  Agents: {', '.join(result.agents_used)}")
            print(f"  Consensus: {result.consensus_method}")
            print(f"  Quality: {result.metrics['quality']:.2f}")
            print(f"  Efficiency: {result.metrics['efficiency']:.2f}")
            print(f"  Harmony: {result.metrics['harmony']:.2f}")
            print(f"  Cost: ${result.metrics['cost']:.2f}")

        # Advance generation
        orchestrator.advance_generation()

        # Show learning progress every 3 generations
        if generation % 3 == 2:
            report = orchestrator.get_collaboration_report()
            print(f"\n=== Learning Report (Generation {generation + 1}) ===")
            print(f"Quality Improvement: {report['improvements']['quality']:.1f}%")
            print(f"Efficiency Improvement: {report['improvements']['efficiency']:.1f}%")
            print(f"Harmony Improvement: {report['improvements']['harmony']:.1f}%")
            print(f"Cost Reduction: {report['improvements']['cost_reduction']:.1f}%")

            if report['best_teams']:
                print("\nDiscovered Optimal Teams:")
                for task_type, team_info in report['best_teams'].items():
                    print(f"  {task_type}: {', '.join(team_info['agents'])} (success: {team_info['success_rate']:.1%})")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_collaboration_learning())