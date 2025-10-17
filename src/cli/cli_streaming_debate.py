#!/usr/bin/env python3
"""
CLI Streaming Debate Interface
Real-time collaborative AI debate visualization in the terminal
"""

import asyncio
import random
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.table import Table
from rich import box

from src.orchestrators.collaborative_orchestrator import CollaborativeOrchestrator
from agents.llm_client import MultiAgentLLMOrchestrator
import yaml

console = Console()


class AgentRole(Enum):
    """Agent roles with visual styling"""
    ARCHITECT = ("architect", "[ARCH]", "cyan")
    CODER = ("coder", "[CODE]", "green")
    REVIEWER = ("reviewer", "[REVW]", "yellow")
    REFINER = ("refiner", "[REFN]", "magenta")
    DOCUMENTER = ("documenter", "[DOCS]", "blue")

    def __init__(self, role: str, icon: str, color: str):
        self.role = role
        self.icon = icon
        self.color = color


@dataclass
class DebateEvent:
    """Event emitted during streaming debate"""
    type: str  # "agent_thinking", "agent_output", "synthesis", "chunk_started"
    agent: Optional[str] = None
    content: str = ""
    timestamp: Optional[str] = None
    title: Optional[str] = None
    agent_icon: Optional[str] = None
    agent_color: Optional[str] = None


class CLIDebateInterface:
    """Terminal-based streaming debate interface using Rich"""

    def __init__(self):
        self.layout = Layout()
        self.messages: List[str] = []
        self.synthesis_results: List[str] = []
        self.agent_status: Dict[str, str] = {}
        self.start_time = None

    def get_elapsed_time(self) -> str:
        """Get elapsed time since start"""
        if not self.start_time:
            return "[00:00.00]"
        elapsed = (datetime.now() - self.start_time).total_seconds()
        minutes = int(elapsed // 60)
        seconds = elapsed % 60
        return f"[{minutes:02d}:{seconds:05.2f}]"

    def add_message(self, message: str, style: str = "white"):
        """Add a message to the debate log"""
        styled_message = f"[{style}]{message}[/{style}]"
        self.messages.append(styled_message)
        # Keep last 50 messages for performance
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]

    def create_header(self, task: str, strategy: str = "BALANCED") -> Panel:
        """Create header panel"""
        content = Text()
        content.append("Task: ", style="bold cyan")
        content.append(f"{task}\n", style="white")
        content.append("Strategy: ", style="bold yellow")
        content.append(f"{strategy}\n", style="white")
        content.append("Elapsed: ", style="bold magenta")
        content.append(self.get_elapsed_time(), style="white")

        return Panel(
            content,
            title="[bold]Collaborative Session[/bold]",
            border_style="cyan",
            box=box.ROUNDED
        )

    def create_agent_status_panel(self) -> Panel:
        """Create agent status panel"""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Agent", style="bold")
        table.add_column("Status")

        for role in AgentRole:
            status = self.agent_status.get(role.role, "idle")
            status_icon = "*" if status == "working" else "+" if status == "done" else "o"
            table.add_row(
                f"{role.icon} {role.role.capitalize()}",
                f"[{role.color}]{status_icon} {status}[/{role.color}]"
            )

        return Panel(
            table,
            title="[bold]Agent Status[/bold]",
            border_style="blue",
            box=box.ROUNDED
        )

    def create_debate_log_panel(self) -> Panel:
        """Create debate log panel"""
        log_text = "\n".join(self.messages[-30:]) if self.messages else "[dim]Waiting for agents...[/dim]"

        return Panel(
            log_text,
            title="[bold]Live Debate[/bold]",
            border_style="green",
            box=box.ROUNDED
        )

    def create_synthesis_panel(self) -> Panel:
        """Create synthesis panel"""
        if not self.synthesis_results:
            content = "[dim]No synthesis yet...[/dim]"
        else:
            content = self.synthesis_results[-1]

        return Panel(
            content,
            title="[bold]Latest Synthesis[/bold]",
            border_style="magenta",
            box=box.ROUNDED
        )

    async def stream_debate(self, task: str, orchestrator: CollaborativeOrchestrator):
        """Stream a collaborative debate session"""
        self.start_time = datetime.now()

        # Create layout
        self.layout.split_column(
            Layout(name="header", size=5),
            Layout(name="body", ratio=1)
        )

        self.layout["body"].split_row(
            Layout(name="debate", ratio=3),
            Layout(name="sidebar", ratio=1)
        )

        self.layout["sidebar"].split_column(
            Layout(name="status", ratio=1),
            Layout(name="synthesis", ratio=1)
        )

        with Live(self.layout, console=console, refresh_per_second=10):
            # Initialize display
            self.layout["header"].update(self.create_header(task))
            self.layout["status"].update(self.create_agent_status_panel())
            self.layout["debate"].update(self.create_debate_log_panel())
            self.layout["synthesis"].update(self.create_synthesis_panel())

            # Stream the debate
            async for event in stream_collaborative_debate(task, orchestrator):
                # Update based on event type
                if event.type == "agent_thinking":
                    self.agent_status[event.agent] = "thinking"
                    self.add_message(
                        f"{self.get_elapsed_time()} {event.agent_icon} {event.agent.capitalize()}: {event.content}",
                        style=f"dim {event.agent_color}"
                    )

                elif event.type == "agent_output":
                    self.agent_status[event.agent] = "working"
                    self.add_message(
                        f"{self.get_elapsed_time()} > {event.agent.capitalize()}: {event.content[:100]}...",
                        style=event.agent_color
                    )

                elif event.type == "agent_complete":
                    self.agent_status[event.agent] = "done"
                    self.add_message(
                        f"{self.get_elapsed_time()} [OK] {event.agent.capitalize()} completed",
                        style=f"bold {event.agent_color}"
                    )

                elif event.type == "synthesis":
                    self.synthesis_results.append(event.content)
                    self.add_message(
                        f"{self.get_elapsed_time()} [REFRESH] Synthesis: {event.title}",
                        style="bold magenta"
                    )

                elif event.type == "chunk_started":
                    self.add_message(
                        f"{self.get_elapsed_time()} [PACKAGE] {event.title}",
                        style="bold cyan"
                    )

                # Update all panels
                self.layout["header"].update(self.create_header(task))
                self.layout["status"].update(self.create_agent_status_panel())
                self.layout["debate"].update(self.create_debate_log_panel())
                self.layout["synthesis"].update(self.create_synthesis_panel())

                await asyncio.sleep(0.05)  # Smooth rendering

        # Final summary
        console.print("\n")
        console.print(Panel(
            self.synthesis_results[-1] if self.synthesis_results else "[red]No synthesis generated[/red]",
            title="[bold green]Final Result[/bold green]",
            border_style="green"
        ))


async def stream_collaborative_debate(
    task: str,
    orchestrator: CollaborativeOrchestrator
) -> AsyncGenerator[DebateEvent, None]:
    """
    Generator that yields debate events in real-time

    This creates pseudo-streaming by running the sequential orchestrator
    and yielding events as each stage progresses
    """

    # Map stage names to agent roles
    agent_map = {
        "architect": AgentRole.ARCHITECT,
        "coder": AgentRole.CODER,
        "reviewer": AgentRole.REVIEWER,
        "refiner": AgentRole.REFINER,
        "documenter": AgentRole.DOCUMENTER,
    }

    yield DebateEvent(
        type="chunk_started",
        title="Starting Collaborative Session",
        timestamp=get_timestamp()
    )

    # Start the collaboration (this will run the full sequential workflow)
    # We'll simulate streaming by breaking it into stages

    # Stage 1: Architect
    agent_role = agent_map.get("architect")
    yield DebateEvent(
        type="agent_thinking",
        agent="architect",
        content="Analyzing requirements and designing solution architecture...",
        agent_icon=agent_role.icon,
        agent_color=agent_role.color,
        timestamp=get_timestamp()
    )

    # Simulate streaming tokens for visual effect
    await asyncio.sleep(0.5)

    # Execute architect stage (we'll integrate with actual orchestrator)
    if orchestrator.sequential_orchestrator:
        # Get the actual result from orchestrator
        result = await orchestrator.collaborate(task)

        # Extract stage outputs
        stages = []
        if hasattr(result, 'individual_outputs'):
            stages = list(result.individual_outputs.items())

        # Stream each stage
        for stage_name, output in stages:
            agent_role = agent_map.get(stage_name)
            if not agent_role:
                continue

            yield DebateEvent(
                type="agent_output",
                agent=stage_name,
                content=output[:200],  # First 200 chars
                agent_icon=agent_role.icon,
                agent_color=agent_role.color,
                timestamp=get_timestamp()
            )

            # Simulate progressive output
            await asyncio.sleep(0.3)

            yield DebateEvent(
                type="agent_complete",
                agent=stage_name,
                agent_icon=agent_role.icon,
                agent_color=agent_role.color,
                timestamp=get_timestamp()
            )

            await asyncio.sleep(0.2)

        # Final synthesis
        yield DebateEvent(
            type="synthesis",
            title="Collaborative Result",
            content=result.final_output,
            timestamp=get_timestamp()
        )


def get_timestamp() -> str:
    """Get current timestamp"""
    return datetime.now().strftime("%H:%M:%S")


async def demo_streaming_debate():
    """Demo the streaming debate interface"""
    console.print("\n[bold cyan]Facilitair Streaming Debate Interface[/bold cyan]\n")

    # Load config
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)

    # Initialize orchestrator
    orchestrator = CollaborativeOrchestrator(config, use_sequential=True)

    # Create interface
    interface = CLIDebateInterface()

    # Example task
    task = "Create a REST API endpoint for user authentication with JWT tokens and rate limiting"

    # Stream the debate
    await interface.stream_debate(task, orchestrator)


if __name__ == "__main__":
    asyncio.run(demo_streaming_debate())
