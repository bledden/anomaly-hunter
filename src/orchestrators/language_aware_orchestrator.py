"""
Language-Aware Multi-Agent Orchestrator

Solves the language thrashing problem by:
1. Analyzing task to determine optimal language(s) upfront
2. Selecting models with proven expertise in those languages
3. Maintaining language consistency throughout the workflow
4. Supporting multi-language systems with clear boundaries
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProgrammingLanguage(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    CPP = "cpp"


class TaskType(Enum):
    ALGORITHM = "algorithm"  # Math/algorithms → Python
    WEB_BACKEND = "web_backend"  # APIs → Python/Go
    WEB_FRONTEND = "web_frontend"  # UI → TypeScript/React
    CLI_TOOL = "cli_tool"  # Command-line → Python/Rust
    DATA_SCIENCE = "data_science"  # ML/Analytics → Python
    SYSTEMS = "systems"  # Low-level → Rust/C++
    MOBILE = "mobile"  # Apps → Swift/Kotlin
    FULLSTACK = "fullstack"  # Multiple languages


@dataclass
class LanguageDecision:
    """Decision about which language(s) to use"""
    primary_language: ProgrammingLanguage
    secondary_languages: List[ProgrammingLanguage]
    task_type: TaskType
    rationale: str
    multi_language: bool = False


@dataclass
class ModelLanguageExpertise:
    """Track which models excel at which languages"""
    model_id: str
    language: ProgrammingLanguage
    expertise_score: float  # 0.0-1.0 based on benchmarks
    specialties: List[str]  # e.g., ["async", "type-safety", "performance"]


class LanguageRouter:
    """
    Analyzes tasks and routes to appropriate language-specialized models.
    """

    # Model expertise mapping (based on benchmark data + known strengths)
    MODEL_EXPERTISE = {
        "deepseek/deepseek-chat": {
            ProgrammingLanguage.PYTHON: 0.95,  # Excellent
            ProgrammingLanguage.JAVA: 0.80,
            ProgrammingLanguage.CPP: 0.85,
            ProgrammingLanguage.JAVASCRIPT: 0.75
        },
        "anthropic/claude-3.5-sonnet": {
            ProgrammingLanguage.PYTHON: 0.90,
            ProgrammingLanguage.TYPESCRIPT: 0.92,  # Excellent
            ProgrammingLanguage.RUST: 0.88,
            ProgrammingLanguage.GO: 0.85
        },
        "openai/gpt-4o": {
            ProgrammingLanguage.PYTHON: 0.88,
            ProgrammingLanguage.TYPESCRIPT: 0.90,
            ProgrammingLanguage.JAVASCRIPT: 0.89,
            ProgrammingLanguage.JAVA: 0.85
        },
        "qwen/qwen-2.5-coder-32b-instruct": {
            ProgrammingLanguage.PYTHON: 0.92,
            ProgrammingLanguage.JAVASCRIPT: 0.88,
            ProgrammingLanguage.TYPESCRIPT: 0.87,
            ProgrammingLanguage.CPP: 0.85
        },
        "mistralai/codestral-2501": {
            ProgrammingLanguage.PYTHON: 0.87,
            ProgrammingLanguage.TYPESCRIPT: 0.85,
            ProgrammingLanguage.RUST: 0.82,
            ProgrammingLanguage.GO: 0.80
        }
    }

    # Task patterns that hint at language choice
    TASK_PATTERNS = {
        TaskType.ALGORITHM: {
            "keywords": ["algorithm", "sort", "search", "prime", "factorial", "fibonacci", "dynamic programming"],
            "preferred_language": ProgrammingLanguage.PYTHON,
            "rationale": "Python excels at algorithmic tasks with clear, readable code"
        },
        TaskType.WEB_BACKEND: {
            "keywords": ["api", "backend", "server", "endpoint", "rest", "graphql", "database"],
            "preferred_language": ProgrammingLanguage.PYTHON,
            "rationale": "Python + FastAPI provides modern, type-safe API development"
        },
        TaskType.WEB_FRONTEND: {
            "keywords": ["react", "component", "ui", "frontend", "html", "css", "web app", "interface"],
            "preferred_language": ProgrammingLanguage.TYPESCRIPT,
            "rationale": "TypeScript + React provides type-safe frontend development"
        },
        TaskType.CLI_TOOL: {
            "keywords": ["command line", "cli", "terminal", "script", "automation"],
            "preferred_language": ProgrammingLanguage.PYTHON,
            "rationale": "Python provides rich CLI libraries and cross-platform support"
        },
        TaskType.DATA_SCIENCE: {
            "keywords": ["machine learning", "data analysis", "pandas", "numpy", "visualization", "statistics"],
            "preferred_language": ProgrammingLanguage.PYTHON,
            "rationale": "Python dominates ML/data science ecosystem"
        },
        TaskType.SYSTEMS: {
            "keywords": ["performance", "memory", "concurrent", "low-level", "systems programming"],
            "preferred_language": ProgrammingLanguage.RUST,
            "rationale": "Rust provides memory safety with C++-level performance"
        }
    }

    def __init__(self, llm_client):
        self.llm = llm_client

    async def analyze_task_language(self, task: str, user_preference: Optional[str] = None) -> LanguageDecision:
        """
        Analyze task to determine optimal language(s).

        Args:
            task: The user's task description
            user_preference: Optional explicit language preference

        Returns:
            LanguageDecision with chosen language(s) and rationale
        """

        # 1. Check explicit user preference
        if user_preference:
            try:
                lang = ProgrammingLanguage(user_preference.lower())
                return LanguageDecision(
                    primary_language=lang,
                    secondary_languages=[],
                    task_type=TaskType.ALGORITHM,  # Default
                    rationale=f"User explicitly requested {user_preference}",
                    multi_language=False
                )
            except ValueError:
                logger.warning(f"Invalid language preference: {user_preference}")

        # 2. Pattern matching for task type
        task_lower = task.lower()
        detected_type = TaskType.ALGORITHM  # Default

        for task_type, config in self.TASK_PATTERNS.items():
            if any(keyword in task_lower for keyword in config["keywords"]):
                detected_type = task_type
                preferred_lang = config["preferred_language"]
                rationale = config["rationale"]

                logger.info(f"Detected task type: {task_type.value} → {preferred_lang.value}")

                return LanguageDecision(
                    primary_language=preferred_lang,
                    secondary_languages=[],
                    task_type=detected_type,
                    rationale=rationale,
                    multi_language=False
                )

        # 3. Check for multi-language system
        multi_lang_keywords = ["fullstack", "frontend and backend", "microservice", "api and ui"]
        if any(keyword in task_lower for keyword in multi_lang_keywords):
            return LanguageDecision(
                primary_language=ProgrammingLanguage.PYTHON,
                secondary_languages=[ProgrammingLanguage.TYPESCRIPT],
                task_type=TaskType.FULLSTACK,
                rationale="Multi-component system: Python backend + TypeScript frontend",
                multi_language=True
            )

        # 4. Default to Python for general tasks
        return LanguageDecision(
            primary_language=ProgrammingLanguage.PYTHON,
            secondary_languages=[],
            task_type=TaskType.ALGORITHM,
            rationale="Default to Python for general-purpose tasks",
            multi_language=False
        )

    def select_models_for_language(
        self,
        language: ProgrammingLanguage,
        available_models: List[str]
    ) -> Dict[str, str]:
        """
        Select best models for each role given a target language.

        Returns dict of role -> model_id
        """

        # Score each model for this language
        scored_models = []
        for model_id in available_models:
            expertise = self.MODEL_EXPERTISE.get(model_id, {})
            score = expertise.get(language, 0.5)  # Default to 0.5 if unknown
            scored_models.append((model_id, score))

        # Sort by expertise (descending)
        scored_models.sort(key=lambda x: x[1], reverse=True)

        # Assign best models to roles
        if len(scored_models) == 0:
            return {}

        best_model = scored_models[0][0]
        second_best = scored_models[1][0] if len(scored_models) > 1 else best_model
        third_best = scored_models[2][0] if len(scored_models) > 2 else second_best

        return {
            "architect": best_model,
            "coder": best_model,  # Use best model for implementation
            "reviewer": second_best,  # Use different model for review
            "documenter": third_best  # Budget model for docs
        }


class LanguageAwareOrchestrator:
    """
    Orchestrator that maintains language consistency.
    """

    def __init__(self, llm_client, config: Dict[str, Any]):
        self.llm = llm_client
        self.config = config
        self.router = LanguageRouter(llm_client)

    async def collaborate(
        self,
        task: str,
        language_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute language-aware collaborative workflow.
        """

        # 1. Analyze task and decide language
        language_decision = await self.router.analyze_task_language(task, language_preference)

        logger.info(f"Language decision: {language_decision.primary_language.value}")
        logger.info(f"Rationale: {language_decision.rationale}")

        # 2. Select language-specialized models
        available_models = self._get_available_models()
        model_assignments = self.router.select_models_for_language(
            language_decision.primary_language,
            available_models
        )

        logger.info(f"Model assignments: {model_assignments}")

        # 3. Execute workflow with language constraints
        if language_decision.multi_language:
            return await self._execute_multi_language_workflow(
                task, language_decision, model_assignments
            )
        else:
            return await self._execute_single_language_workflow(
                task, language_decision, model_assignments
            )

    async def _execute_single_language_workflow(
        self,
        task: str,
        language_decision: LanguageDecision,
        model_assignments: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Execute workflow maintaining single language throughout.
        """

        language = language_decision.primary_language.value

        # Stage 1: Architecture (with language constraint)
        arch_prompt = f"""As a software architect, design a solution for this task IN {language.upper()}:

Task: {task}

IMPORTANT: Design specifically for {language}, leveraging its:
- Standard library and ecosystem
- Idiomatic patterns and best practices
- Type system and safety features
- Performance characteristics

Provide:
1. High-level architecture
2. {language.capitalize()} modules/packages to use
3. Key design decisions for {language}
4. Data structures and types
5. Interface definitions

Return a design document in Markdown."""

        architect_model = model_assignments.get("architect", "openai/gpt-4o")
        architecture = await self._call_llm(architect_model, arch_prompt)

        # Stage 2: Implementation (with language enforcement)
        impl_prompt = f"""Implement this solution in {language.upper()} based on the architecture:

Original Task: {task}

Architecture:
{architecture}

Generate complete, production-ready {language.upper()} code that:
1. Follows the architectural design
2. Uses idiomatic {language} patterns
3. Includes type hints/annotations (if applicable)
4. Has robust error handling
5. Is well-structured and maintainable

Return ONLY {language.upper()} code with appropriate syntax (```{language}), no explanations."""

        coder_model = model_assignments.get("coder", "deepseek/deepseek-chat")
        implementation = await self._call_llm(coder_model, impl_prompt)

        # Stage 3: Review (language-aware)
        review_prompt = f"""Review this {language.upper()} code:

Original Task: {task}

Architecture:
{architecture}

Implementation:
{implementation}

Check specifically for {language} best practices:
- Idiomatic {language} patterns
- Proper use of language features
- Type safety (if applicable)
- Error handling patterns
- Performance considerations

Return JSON with: {{"issues_found": bool, "critical_issues": [], "suggestions": []}}"""

        reviewer_model = model_assignments.get("reviewer", "anthropic/claude-3.5-sonnet")
        review = await self._call_llm(reviewer_model, review_prompt, temperature=0.0)

        return {
            "task": task,
            "language": language,
            "language_rationale": language_decision.rationale,
            "architecture": architecture,
            "implementation": implementation,
            "review": review,
            "model_assignments": model_assignments
        }

    async def _execute_multi_language_workflow(
        self,
        task: str,
        language_decision: LanguageDecision,
        model_assignments: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Execute workflow for multi-language systems.
        Each component uses its optimal language.
        """
        # TODO: Implement multi-language workflow
        # - Backend team (Python)
        # - Frontend team (TypeScript)
        # - Integration contracts (OpenAPI/GraphQL)
        pass

    async def _call_llm(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.2
    ) -> str:
        """Call LLM with timeout and error handling"""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.complete(
                model=model,
                messages=messages,
                temperature=temperature
            )
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"[ERROR] {str(e)}"

    def _get_available_models(self) -> List[str]:
        """Get list of available models from config"""
        # Extract from config based on strategy
        models = []
        for role_config in self.config.get("agents", {}).values():
            default_model = role_config.get("default_model")
            if default_model:
                models.append(default_model)
        return list(set(models))  # Deduplicate


# Example usage
if __name__ == "__main__":
    async def test():
        # Mock LLM client
        class MockLLM:
            async def complete(self, **kwargs):
                return "Mock response"

        orchestrator = LanguageAwareOrchestrator(
            llm_client=MockLLM(),
            config={}
        )

        # Test cases
        test_tasks = [
            "Write a function to check if a number is prime",
            "Build a REST API with FastAPI for user management",
            "Create a React component for a todo list",
            "Implement a concurrent web scraper",
        ]

        for task in test_tasks:
            decision = await orchestrator.router.analyze_task_language(task)
            print(f"\nTask: {task}")
            print(f"Language: {decision.primary_language.value}")
            print(f"Rationale: {decision.rationale}")

    asyncio.run(test())
