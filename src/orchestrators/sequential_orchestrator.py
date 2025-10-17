"""
Sequential Collaborative Orchestrator for WeaveHacks 2
Port of Facilitair_v2's proven sequential collaboration architecture.

Instead of consensus/voting, models work sequentially:
  Architect → Implementer → Reviewer → Refiner (iterate) → Tester + Documenter

Each agent:
- Receives outputs from previous stages
- Has format preferences (JSON, XML, Markdown)
- Gets the original user request preserved throughout
"""

import weave
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import asyncio
from datetime import datetime
import time
import re
import uuid
import logging

# Import middleware
try:
    from src.middleware import MiddlewareHook, MiddlewareContext
except ImportError:
    # Middleware is optional
    MiddlewareHook = None
    MiddlewareContext = None

# Import configuration
from src.config import get_orchestration_config

logger = logging.getLogger(__name__)

# Load orchestration configuration (timeouts, stage multipliers)
_orchestration_config = get_orchestration_config()

# Timeout constants loaded from config (with environment variable override support)
TOTAL_BUDGET_S = _orchestration_config.get_total_budget()
STAGE_TIMEOUT_S = _orchestration_config.get_default_stage_timeout()
ARCHITECTURE_TIMEOUT_MULTIPLIER = _orchestration_config.get_stage_multiplier('architecture')
IMPLEMENTATION_TIMEOUT_MULTIPLIER = _orchestration_config.get_stage_multiplier('implementation')


class AgentRole(Enum):
    """Roles in sequential collaboration workflow"""
    ARCHITECT = "architect"      # High-level design (outputs Markdown)
    CODER = "coder"  # Code generation (outputs code)
    REVIEWER = "reviewer"        # Code review (outputs JSON)
    REFINER = "refiner"         # Fix issues (outputs code)
    TESTER = "tester"           # Test generation (outputs code)
    DOCUMENTER = "documenter"   # Documentation (outputs Markdown)


@dataclass
class AgentCommunicationProfile:
    """Communication preferences for an agent"""
    role: AgentRole
    model_id: str
    preferred_input_format: str   # "json", "xml", "markdown", "code"
    preferred_output_format: str
    context_requirements: List[str]  # What info from previous stages


@dataclass
class StageResult:
    """Result from a single workflow stage"""
    stage: str
    agent_role: AgentRole
    model_id: str
    timestamp: str
    input_context: Dict[str, Any]
    output: str
    format: str
    duration_seconds: float
    success: bool
    error: Optional[str] = None
    evaluation: Optional[Dict[str, Any]] = None  # Evaluation results from middleware


@dataclass
class WorkflowResult:
    """Complete workflow execution result"""
    run_id: str
    original_request: str
    workflow_name: str
    stages: List[StageResult]
    final_output: str
    iterations: int
    total_duration_seconds: float
    success: bool


class FormatConverter:
    """Converts between agent communication formats"""

    @staticmethod
    def to_json(data: Any) -> str:
        """Convert data to JSON format"""
        if isinstance(data, str):
            # Try to parse as JSON first
            try:
                parsed = json.loads(data)
                return json.dumps(parsed, indent=2)
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning(f"Failed to parse JSON string: {e}")
                # Wrap string in JSON object
                return json.dumps({"content": data}, indent=2)
        return json.dumps(data, indent=2)

    @staticmethod
    def to_markdown(data: Any) -> str:
        """Convert data to Markdown format"""
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            lines = ["# Data\n"]
            for key, value in data.items():
                lines.append(f"## {key}\n")
                lines.append(f"{value}\n")
            return "\n".join(lines)
        return str(data)

    @staticmethod
    def to_xml(data: Any) -> str:
        """Convert data to XML format"""
        if isinstance(data, str):
            return f"<content>{data}</content>"
        elif isinstance(data, dict):
            lines = ["<data>"]
            for key, value in data.items():
                lines.append(f"  <{key}>{value}</{key}>")
            lines.append("</data>")
            return "\n".join(lines)
        return f"<content>{str(data)}</content>"

    @staticmethod
    def extract_code(text: str) -> str:
        """Extract code blocks from markdown/mixed content"""
        if not text:
            return text
        # Find fenced code blocks
        blocks = re.findall(r"```(?:[a-zA-Z0-9_+\-#]+)?\s*([\s\S]*?)```", text)
        if blocks:
            # Return the largest code block
            blocks_sorted = sorted(blocks, key=lambda b: len(b), reverse=True)
            return blocks_sorted[0].strip()
        # If looks like code but no fences, return as-is
        if any(tok in text for tok in ("def ", "class ", "import ", "from ", "function", "const ")):
            return text
        return text

    def convert(self, content: str, from_format: str, to_format: str) -> str:
        """Convert content between formats"""
        if from_format == to_format:
            return content

        # Parse source format
        if from_format == "json":
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON in convert(): {e}")
                parsed = {"content": content}
        elif from_format == "code":
            parsed = {"code": self.extract_code(content)}
        else:  # markdown or plain text
            parsed = {"content": content}

        # Convert to target format
        if to_format == "json":
            return self.to_json(parsed)
        elif to_format == "xml":
            return self.to_xml(parsed)
        elif to_format == "markdown":
            return self.to_markdown(parsed)
        elif to_format == "code":
            if isinstance(parsed, dict) and "code" in parsed:
                return parsed["code"]
            return content
        else:
            return str(parsed)


class SequentialCollaborativeOrchestrator:
    """
    Sequential multi-agent collaboration orchestrator for WeaveHacks.
    Based on Facilitair_v2's proven architecture.
    """

    def __init__(self, llm_orchestrator, config: Optional[Dict] = None, middleware: Optional[List] = None):
        """
        Initialize with LLM orchestrator from weavehacks-collaborative.

        Args:
            llm_orchestrator: MultiAgentLLMOrchestrator instance
            config: Optional agent configuration
            middleware: Optional list of middleware instances
        """
        self.llm = llm_orchestrator
        self.config = config or {}
        self.format_converter = FormatConverter()
        self.middleware = middleware or []

        # Define agent communication profiles
        self.agent_profiles = self._setup_agent_profiles()

    def _setup_agent_profiles(self) -> Dict[AgentRole, AgentCommunicationProfile]:
        """Setup communication profiles for each agent"""

        # Get model assignments from config or use defaults
        architect_model = self.config.get("architect", {}).get("default_model", "anthropic/claude-3.5-sonnet")
        coder_model = self.config.get("coder", {}).get("default_model", "openai/gpt-4-turbo-preview")
        reviewer_model = self.config.get("reviewer", {}).get("default_model", "anthropic/claude-3.5-sonnet")
        refiner_model = coder_model  # Same as coder
        tester_model = self.config.get("coder", {}).get("default_model", "openai/gpt-3.5-turbo")
        doc_model = self.config.get("documenter", {}).get("default_model", "openai/gpt-3.5-turbo")

        return {
            AgentRole.ARCHITECT: AgentCommunicationProfile(
                role=AgentRole.ARCHITECT,
                model_id=architect_model,
                preferred_input_format="markdown",
                preferred_output_format="markdown",
                context_requirements=["original_request"]
            ),
            AgentRole.CODER: AgentCommunicationProfile(
                role=AgentRole.CODER,
                model_id=coder_model,
                preferred_input_format="markdown",
                preferred_output_format="code",
                context_requirements=["original_request", "architecture"]
            ),
            AgentRole.REVIEWER: AgentCommunicationProfile(
                role=AgentRole.REVIEWER,
                model_id=reviewer_model,
                preferred_input_format="code",
                preferred_output_format="json",
                context_requirements=["original_request", "architecture", "implementation"]
            ),
            AgentRole.DOCUMENTER: AgentCommunicationProfile(
                role=AgentRole.DOCUMENTER,
                model_id=doc_model,
                preferred_input_format="markdown",
                preferred_output_format="markdown",
                context_requirements=["original_request", "architecture", "final_implementation"]
            )
        }

    @weave.op()
    async def execute_workflow(
        self,
        task: str,
        max_iterations: int = 3,
        temperature: float = 0.2
    ) -> WorkflowResult:
        """
        Execute sequential collaborative workflow.

        Args:
            task: User's original request
            max_iterations: Max review-refine iterations
            temperature: LLM temperature

        Returns:
            WorkflowResult with all stage outputs
        """
        run_id = str(uuid.uuid4())
        start_time = time.time()

        def budget_left() -> float:
            return max(0.1, TOTAL_BUDGET_S - (time.time() - start_time))

        stages: List[StageResult] = []
        context = {
            "original_request": task,
            "run_id": run_id
        }

        try:
            # Stage 1: Architecture
            logger.info(f"[{run_id}] Stage 1: Architecture")
            arch_timeout = min(STAGE_TIMEOUT_S * ARCHITECTURE_TIMEOUT_MULTIPLIER, budget_left())
            arch_result = await self._architect_stage(context, timeout=arch_timeout, temperature=temperature)
            stages.append(arch_result)
            context["architecture"] = arch_result.output

            # Stage 2: Implementation
            logger.info(f"[{run_id}] Stage 2: Implementation")
            impl_timeout = min(STAGE_TIMEOUT_S * IMPLEMENTATION_TIMEOUT_MULTIPLIER, budget_left())
            impl_result = await self._coder_stage(context, timeout=impl_timeout, temperature=temperature)
            stages.append(impl_result)
            context["implementation"] = impl_result.output

            # Stage 3: Review
            logger.info(f"[{run_id}] Stage 3: Review")
            review_timeout = min(STAGE_TIMEOUT_S, budget_left())
            review_result = await self._reviewer_stage(context, timeout=review_timeout, temperature=0.0)
            stages.append(review_result)
            context["review"] = review_result.output

            # Stage 4: Refinement (iterate if issues found)
            # REFINER = CODER agent with review context
            iterations = 0
            issues_found = self._parse_review_result(review_result.output)

            while issues_found and iterations < max_iterations and budget_left() > 10:
                iterations += 1
                logger.info(f"[{run_id}] Stage 4: Refinement (iteration {iterations}) - using CODER as refiner")

                refine_timeout = min(STAGE_TIMEOUT_S, budget_left())
                # Use coder_stage as refiner with review context
                refine_result = await self._coder_refine_stage(context, timeout=refine_timeout, temperature=temperature)
                stages.append(refine_result)
                context["implementation"] = refine_result.output  # Update implementation

                # Re-review
                review_timeout = min(STAGE_TIMEOUT_S, budget_left())
                review_result = await self._reviewer_stage(context, timeout=review_timeout, temperature=0.0)
                stages.append(review_result)
                context["review"] = review_result.output

                issues_found = self._parse_review_result(review_result.output)

            context["final_implementation"] = context["implementation"]

            # POST_REFINER Hook - Run evaluation middleware
            if self.middleware and MiddlewareHook:
                logger.info(f"[{run_id}] Running POST_REFINER middleware")
                try:
                    for mw in self.middleware:
                        if mw.should_execute(MiddlewareHook.POST_REFINER):
                            mw_context = MiddlewareContext(
                                hook=MiddlewareHook.POST_REFINER,
                                stage_name="post_refiner",
                                input_data=context,
                                output_data={"code": context["final_implementation"]}
                            )
                            mw_result = mw.execute(mw_context)
                            if mw_result.get("evaluation"):
                                context["refiner_evaluation"] = mw_result["evaluation"]
                                logger.info(f"Evaluation: {mw_result['evaluation'].overall_score:.3f}")
                                # Log to Weave
                                weave.attributes({"eval_overall": mw_result['evaluation'].overall_score, "eval_security": mw_result['evaluation'].security_score, "eval_static": mw_result['evaluation'].static_analysis_score, "eval_complexity": mw_result['evaluation'].complexity_score, "eval_llm": mw_result['evaluation'].llm_judge_score})
                except Exception as e:
                    logger.error(f"POST_REFINER middleware failed: {e}")

            # Stage 5: Documentation (no testing - can be requested post-delivery)
            logger.info(f"[{run_id}] Stage 5: Documentation")
            if budget_left() > 10:
                doc_timeout = min(STAGE_TIMEOUT_S, budget_left())
                doc_result = await self._documenter_stage(context, timeout=doc_timeout, temperature=temperature)
                stages.append(doc_result)

                # POST_DOCUMENTER Hook - Run evaluation middleware on documentation
                if self.middleware and MiddlewareHook:
                    logger.info(f"[{run_id}] Running POST_DOCUMENTER middleware")
                    try:
                        for mw in self.middleware:
                            if mw.should_execute(MiddlewareHook.POST_DOCUMENTER):
                                mw_context = MiddlewareContext(
                                    hook=MiddlewareHook.POST_DOCUMENTER,
                                    stage_name="post_documenter",
                                    input_data=context,
                                    output_data={"documentation": doc_result.output}
                                )
                                mw_result = mw.execute(mw_context)
                                if mw_result.get("evaluation"):
                                    context["documenter_evaluation"] = mw_result["evaluation"]
                    except Exception as e:
                        logger.error(f"POST_DOCUMENTER middleware failed: {e}")
                context["documentation"] = doc_result.output

            total_duration = time.time() - start_time

            # Check if all stages succeeded (protect against empty stages list)
            all_stages_succeeded = len(stages) > 0 and all(stage.success for stage in stages)
            has_valid_output = len(context.get("final_implementation", "").strip()) > 50

            return WorkflowResult(
                run_id=run_id,
                original_request=task,
                workflow_name="feature_development",
                stages=stages,
                final_output=context.get("final_implementation", ""),
                iterations=iterations,
                total_duration_seconds=total_duration,
                success=all_stages_succeeded and has_valid_output
            )

        except Exception as e:
            logger.error(f"[{run_id}] Workflow failed: {e}")
            total_duration = time.time() - start_time

            return WorkflowResult(
                run_id=run_id,
                original_request=task,
                workflow_name="feature_development",
                stages=stages,
                final_output="",
                iterations=0,
                total_duration_seconds=total_duration,
                success=False
            )

    async def _architect_stage(
        self,
        context: Dict[str, Any],
        timeout: float,
        temperature: float
    ) -> StageResult:
        """Architecture and design stage"""
        start = time.time()
        profile = self.agent_profiles[AgentRole.ARCHITECT]

        task = context["original_request"]

        prompt = f"""As a software architect, design a solution for this task:

Task: {task}

Provide:
1. High-level architecture
2. Component breakdown
3. Key design decisions
4. Data flow
5. Interface definitions

Return a structured design document in Markdown format."""

        try:
            output = await self._call_llm(
                agent_role=profile.role,
                prompt=prompt,
                temperature=temperature,
                timeout=timeout
            )

            # Better success detection: check output quality
            has_substantial_content = len(output.strip()) > 100
            not_error = not output.startswith("[ERROR]")
            has_architecture_keywords = any(keyword in output.lower() for keyword in ['architecture', 'design', 'component', 'system', 'structure'])

            return StageResult(
                stage="architecture",
                agent_role=AgentRole.ARCHITECT,
                model_id=profile.model_id,
                timestamp=datetime.now().isoformat(),
                input_context={"original_request": task},
                output=output,
                format="markdown",
                duration_seconds=time.time() - start,
                success=not_error and has_substantial_content and has_architecture_keywords
            )
        except Exception as e:
            return StageResult(
                stage="architecture",
                agent_role=AgentRole.ARCHITECT,
                model_id=profile.model_id,
                timestamp=datetime.now().isoformat(),
                input_context={"original_request": task},
                output=f"[ERROR] {str(e)}",
                format="markdown",
                duration_seconds=time.time() - start,
                success=False,
                error=str(e)
            )

    async def _coder_stage(
        self,
        context: Dict[str, Any],
        timeout: float,
        temperature: float
    ) -> StageResult:
        """Implementation stage"""
        start = time.time()
        profile = self.agent_profiles[AgentRole.CODER]

        task = context["original_request"]
        architecture = context.get("architecture", "")

        prompt = f"""Implement this solution based on the architecture.

=== ORIGINAL USER REQUEST ===
{task}

=== ARCHITECTURAL DESIGN (Context) ===
{architecture}

=== YOUR TASK ===
Generate complete, production-ready code that:
1. Fulfills the original user request above
2. Implements the architectural design faithfully
3. Includes robust error handling
4. Is well-structured and maintainable
5. Follows language best practices

=== REASONING TRACE ===
Before coding, consider:
- How does the architecture map to the user's request?
- What are the key components needed?
- What edge cases should be handled?
- What dependencies/imports are required?

Return ONLY the complete, working code. No explanations outside code comments."""

        try:
            output = await self._call_llm(
                agent_role=profile.role,
                prompt=prompt,
                temperature=temperature,
                timeout=timeout
            )

            # Extract code blocks
            code = self.format_converter.extract_code(output)

            return StageResult(
                stage="implementation",
                agent_role=AgentRole.CODER,
                model_id=profile.model_id,
                timestamp=datetime.now().isoformat(),
                input_context={"original_request": task, "architecture": architecture},
                output=code,
                format="code",
                duration_seconds=time.time() - start,
                success=not output.startswith("[ERROR]")
            )
        except Exception as e:
            return StageResult(
                stage="implementation",
                agent_role=AgentRole.CODER,
                model_id=profile.model_id,
                timestamp=datetime.now().isoformat(),
                input_context={"original_request": task, "architecture": architecture},
                output=f"[ERROR] {str(e)}",
                format="code",
                duration_seconds=time.time() - start,
                success=False,
                error=str(e)
            )

    async def _reviewer_stage(
        self,
        context: Dict[str, Any],
        timeout: float,
        temperature: float
    ) -> StageResult:
        """Code review stage"""
        start = time.time()
        profile = self.agent_profiles[AgentRole.REVIEWER]

        code = context.get("implementation", "")
        architecture = context.get("architecture", "")

        prompt = f"""Review this code implementation for correctness and quality.

=== ORIGINAL USER REQUEST ===
{context.get("original_request", "")}

=== ARCHITECTURAL DESIGN (Expected Implementation) ===
{architecture}

=== CODE TO REVIEW ===
{code}

=== YOUR TASK ===
Review the code against BOTH the architectural intent AND the original user request.

=== REASONING TRACE ===
Before reviewing, consider:
1. Does the code fulfill the original user's request?
2. Does it implement the architectural design correctly?
3. Are there security vulnerabilities?
4. Are edge cases handled?
5. Is error handling robust?
6. Does it follow language best practices?

Return ONLY JSON with this exact schema:
{{
  "issues_found": true,
  "critical_issues": ["Security: eval() usage detected", "..."],
  "suggestions": ["Add input validation for...", "..."],
  "code_quality_score": 7
}}"""

        try:
            output = await self._call_llm(
                agent_role=profile.role,
                prompt=prompt,
                temperature=temperature,
                timeout=timeout
            )

            return StageResult(
                stage="review",
                agent_role=AgentRole.REVIEWER,
                model_id=profile.model_id,
                timestamp=datetime.now().isoformat(),
                input_context={"implementation": code[:200], "architecture": architecture[:200]},
                output=output,
                format="json",
                duration_seconds=time.time() - start,
                success=not output.startswith("[ERROR]")
            )
        except Exception as e:
            return StageResult(
                stage="review",
                agent_role=AgentRole.REVIEWER,
                model_id=profile.model_id,
                timestamp=datetime.now().isoformat(),
                input_context={"implementation": code[:200], "architecture": architecture[:200]},
                output=f"[ERROR] {str(e)}",
                format="json",
                duration_seconds=time.time() - start,
                success=False,
                error=str(e)
            )

    async def _coder_refine_stage(
        self,
        context: Dict[str, Any],
        timeout: float,
        temperature: float
    ) -> StageResult:
        """Refinement stage - REUSES CODER agent with review context"""
        start = time.time()
        profile = self.agent_profiles[AgentRole.CODER]

        code = context.get("implementation", "")
        review = context.get("review", "")
        task = context.get("original_request", "")

        prompt = f"""Refine the code based on review feedback.

=== ORIGINAL USER REQUEST ===
{task}

=== ARCHITECTURAL DESIGN (Original Intent) ===
{context.get("architecture", "")}

=== CURRENT IMPLEMENTATION ===
{code}

=== REVIEW FINDINGS (Issues to Address) ===
{review}

=== YOUR TASK ===
Fix the identified issues while maintaining:
1. Alignment with the original user request
2. Adherence to the architectural design
3. Code correctness and functionality
4. Best practices and maintainability

=== REASONING TRACE ===
Before refining, consider:
1. Which issues are critical vs. nice-to-have?
2. How can fixes maintain the architectural intent?
3. Are there unintended side effects of proposed changes?
4. Does the refined code still solve the original request?

Return ONLY the complete, refined code. No explanations outside code comments."""

        try:
            output = await self._call_llm(
                agent_role=profile.role,
                prompt=prompt,
                temperature=temperature,
                timeout=timeout
            )

            # Extract code blocks
            refined_code = self.format_converter.extract_code(output)

            return StageResult(
                stage="refinement",
                agent_role=AgentRole.CODER,  # ← CODER acting as refiner
                model_id=profile.model_id,
                timestamp=datetime.now().isoformat(),
                input_context={"implementation": code[:200], "review": review[:200]},
                output=refined_code,
                format="code",
                duration_seconds=time.time() - start,
                success=not output.startswith("[ERROR]")
            )
        except Exception as e:
            return StageResult(
                stage="refinement",
                agent_role=AgentRole.CODER,
                model_id=profile.model_id,
                timestamp=datetime.now().isoformat(),
                input_context={"implementation": code[:200], "review": review[:200]},
                output=f"[ERROR] {str(e)}",
                format="code",
                duration_seconds=time.time() - start,
                success=False,
                error=str(e)
            )

    async def _documenter_stage(
        self,
        context: Dict[str, Any],
        timeout: float,
        temperature: float
    ) -> StageResult:
        """Documentation generation stage"""
        start = time.time()
        profile = self.agent_profiles[AgentRole.DOCUMENTER]

        architecture = context.get("architecture", "")
        code = context.get("final_implementation", "")
        task = context.get("original_request", "")

        prompt = f"""Create comprehensive documentation for the implemented solution.

=== ORIGINAL USER REQUEST ===
{task}

=== ARCHITECTURAL DESIGN (Context) ===
{architecture}

=== IMPLEMENTATION (Code to Document) ===
{code}

=== YOUR TASK ===
Generate complete, user-friendly documentation that:
1. Explains what the solution does (aligned with original request)
2. Shows how to use it with clear examples
3. Documents the architecture and design decisions
4. Includes setup/installation instructions
5. Provides API reference if applicable

=== REASONING TRACE ===
Before documenting, consider:
- What does a user need to understand to use this solution?
- How does the implementation fulfill the original request?
- What are the key architectural concepts to explain?
- What examples would be most helpful?
- What edge cases or limitations should be documented?

Return ONLY the complete Markdown documentation. Use clear headings, code blocks, and examples."""

        try:
            output = await self._call_llm(
                agent_role=profile.role,
                prompt=prompt,
                temperature=temperature,
                timeout=timeout
            )

            return StageResult(
                stage="documentation",
                agent_role=AgentRole.DOCUMENTER,
                model_id=profile.model_id,
                timestamp=datetime.now().isoformat(),
                input_context={"architecture": architecture[:200], "final_implementation": code[:200]},
                output=output,
                format="markdown",
                duration_seconds=time.time() - start,
                success=not output.startswith("[ERROR]")
            )
        except Exception as e:
            return StageResult(
                stage="documentation",
                agent_role=AgentRole.DOCUMENTER,
                model_id=profile.model_id,
                timestamp=datetime.now().isoformat(),
                input_context={"architecture": architecture[:200], "final_implementation": code[:200]},
                output=f"[ERROR] {str(e)}",
                format="markdown",
                duration_seconds=time.time() - start,
                success=False,
                error=str(e)
            )

    async def _call_llm(
        self,
        agent_role: AgentRole,
        prompt: str,
        temperature: float,
        timeout: float
    ) -> str:
        """Call LLM with timeout and error handling"""
        try:
            async def _call():
                # Convert AgentRole enum to agent_id string (e.g., AgentRole.CODER -> "coder")
                agent_id = agent_role.value
                # Note: temperature is configured in agent config, not passed as parameter
                return await self.llm.execute_agent_task(agent_id, prompt)

            output = await asyncio.wait_for(_call(), timeout=timeout)
            return output if isinstance(output, str) else str(output)

        except asyncio.TimeoutError:
            return "[ERROR] LLM timeout"
        except Exception as e:
            return f"[ERROR] LLM error: {e}"

    def _parse_review_result(self, review_output: str) -> bool:
        """Parse review output to determine if issues were found"""
        try:
            # Try to parse as JSON
            match = re.search(r"\{.*\}", review_output, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return bool(data.get("issues_found", False))
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Failed to parse review result as JSON: {e}")

        # Fallback: keyword heuristic
        lower = review_output.lower()
        return ("critical" in lower) or ("bug" in lower) or ("issue" in lower)
