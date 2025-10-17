#!/usr/bin/env python3
"""
Live CLI dashboard for monitoring Facilitair test progress.
Reads from log files written by test scripts and displays real-time progress.

Usage:
    python3 monitor.py fe6e5e 8c42af d9ac2f

Creates a beautiful live-updating dashboard showing:
- Test progress (current task / total tasks)
- Active agent (architect, coder, reviewer, etc.)
- Sequential vs Baseline results
- Completion status

Press Ctrl+C to exit.
"""

import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


@dataclass
class TestProgress:
    """Tracks progress of a single test"""
    bash_id: str
    strategy: str = "UNKNOWN"
    current_task: int = 0
    total_tasks: int = 10
    current_agent: str = "..."
    status: str = "running"  # running, completed, error
    sequential_pass: Optional[int] = None
    sequential_total: Optional[int] = None
    baseline_pass: Optional[int] = None
    baseline_total: Optional[int] = None
    last_line: str = ""
    last_update: datetime = field(default_factory=datetime.now)


class TestDashboard:
    """Live dashboard for monitoring test progress"""

    def __init__(self, bash_ids: list[str]):
        self.bash_ids = bash_ids
        self.tests: Dict[str, TestProgress] = {}
        self.log_dir = "/tmp/facilitair_logs"

        # Initialize test tracking
        for bash_id in bash_ids:
            self.tests[bash_id] = TestProgress(bash_id=bash_id)

        # Ensure log directory exists
        os.makedirs(self.log_dir, exist_ok=True)

    def read_test_output(self, bash_id: str) -> str:
        """Read latest output for a test from its log file"""
        log_file = os.path.join(self.log_dir, f"test_{bash_id}.log")

        if not os.path.exists(log_file):
            return ""

        try:
            with open(log_file, 'r') as f:
                return f.read()
        except Exception:
            return ""

    def parse_output(self, bash_id: str, output: str):
        """Parse test output and update progress"""
        test = self.tests[bash_id]
        test.last_update = datetime.now()

        if not output:
            return

        # Extract strategy
        if match := re.search(r'Model selection strategy: (\w+)', output):
            test.strategy = match.group(1)

        # Extract current task
        task_matches = re.findall(r'Task (\d+):', output)
        if task_matches:
            test.current_task = int(task_matches[-1])

        # Extract current agent
        agent_matches = re.findall(r'\[LLM\] (\w+) using', output)
        if agent_matches:
            test.current_agent = agent_matches[-1]

        # Check for results
        if 'SEQUENTIAL RESULTS' in output:
            if match := re.search(r'Pass rate: (\d+)/(\d+)', output):
                test.sequential_pass = int(match.group(1))
                test.sequential_total = int(match.group(2))

        if 'BASELINE RESULTS' in output:
            results_section = output.split('BASELINE RESULTS')[1]
            if match := re.search(r'Pass rate: (\d+)/(\d+)', results_section):
                test.baseline_pass = int(match.group(1))
                test.baseline_total = int(match.group(2))

                # Mark as completed if we have both results
                if test.sequential_pass is not None:
                    test.status = "completed"

        # Check for errors
        error_lines = [l for l in output.split('\n') if 'ERROR' in l or 'FAILED' in l]
        if error_lines:
            test.last_line = error_lines[-1][:80]

        # Get last meaningful line
        lines = [l.strip() for l in output.split('\n') if l.strip()]
        if lines:
            test.last_line = lines[-1][:80]

    def create_table(self) -> Table:
        """Create the main progress table"""
        table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
            border_style="bright_blue",
            expand=True
        )

        table.add_column("Test", style="cyan", width=8)
        table.add_column("Strategy", style="yellow", width=10)
        table.add_column("Progress", style="green", width=28)
        table.add_column("Agent", style="magenta", width=12)
        table.add_column("Sequential", style="bright_magenta", width=13)
        table.add_column("Baseline", style="bright_green", width=13)
        table.add_column("Status", style="blue", width=12)

        for bash_id in self.bash_ids:
            test = self.tests[bash_id]

            # Progress bar
            pct = (test.current_task / test.total_tasks * 100) if test.total_tasks > 0 else 0
            filled = int(20 * pct / 100)
            bar = "" * filled + "" * (20 - filled)

            if pct >= 90:
                bar_color = "green"
            elif pct >= 50:
                bar_color = "yellow"
            else:
                bar_color = "blue"

            progress = f"[{bar_color}]{bar}[/{bar_color}] {test.current_task}/{test.total_tasks}"

            # Agent
            agent_text = f"[italic]{test.current_agent}[/italic]"

            # Results
            if test.sequential_pass is not None and test.sequential_total is not None:
                seq_pct = (test.sequential_pass / test.sequential_total * 100)
                seq_color = "green" if seq_pct >= 70 else "yellow" if seq_pct >= 40 else "red"
                seq_text = f"[{seq_color}]{test.sequential_pass}/{test.sequential_total}[/{seq_color}] ({seq_pct:.0f}%)"
            else:
                seq_text = "[dim]Pending...[/dim]"

            if test.baseline_pass is not None and test.baseline_total is not None:
                base_pct = (test.baseline_pass / test.baseline_total * 100)
                base_color = "green" if base_pct >= 70 else "yellow" if base_pct >= 40 else "red"
                base_text = f"[{base_color}]{test.baseline_pass}/{test.baseline_total}[/{base_color}] ({base_pct:.0f}%)"
            else:
                base_text = "[dim]Pending...[/dim]"

            # Status
            time_ago = (datetime.now() - test.last_update).total_seconds()
            if time_ago < 60:
                time_str = f"{int(time_ago)}s"
            else:
                time_str = f"{int(time_ago/60)}m"

            status_emoji = {"running": "[RUNNING]", "completed": "[OK]", "error": "[FAIL]"}.get(test.status, "")
            status_text = f"{status_emoji} {test.status.upper()}\n[dim]({time_str} ago)[/dim]"

            table.add_row(
                bash_id[:6],
                test.strategy,
                progress,
                agent_text,
                seq_text,
                base_text,
                status_text
            )

        return table

    def create_layout(self) -> Panel:
        """Create the full dashboard layout"""
        table = self.create_table()

        # Add footer legend
        footer = Text()
        footer.append("\n Legend: ", style="bold")
        footer.append("[RUNNING] Running  ", style="green")
        footer.append("[OK] Completed  ", style="blue")
        footer.append("[FAIL] Error", style="red")
        footer.append("\n\n Press Ctrl+C to exit", style="dim italic")

        # Combine
        content = Text.from_markup(str(table)) + footer

        return Panel(
            table,
            title="[bold cyan][START] Facilitair Test Monitor Dashboard[/bold cyan]",
            subtitle=f"[dim]{datetime.now().strftime('%H:%M:%S')} | Monitoring {len(self.bash_ids)} test(s)[/dim]",
            border_style="cyan",
            padding=(1, 2)
        )

    def run(self, refresh_interval: float = 2.0):
        """Run the live dashboard"""
        console.print("[bold cyan][START] Facilitair Test Monitor[/bold cyan]")
        console.print(f"[dim]Monitoring: {', '.join(self.bash_ids)}[/dim]\n")

        with Live(self.create_layout(), refresh_per_second=0.5, console=console) as live:
            try:
                while True:
                    # Update all tests
                    for bash_id in self.bash_ids:
                        output = self.read_test_output(bash_id)
                        self.parse_output(bash_id, output)

                    # Update display
                    live.update(self.create_layout())

                    # Check if all done
                    if all(t.status == "completed" for t in self.tests.values()):
                        break

                    time.sleep(refresh_interval)

            except KeyboardInterrupt:
                console.print("\n[yellow][WARNING]  Monitor stopped by user[/yellow]")
                return

        # Print final summary
        console.print("\n[bold green][OK] All tests completed![/bold green]\n")
        self.print_summary()

    def print_summary(self):
        """Print final results summary"""
        console.print("[bold]Final Results:[/bold]\n")

        for bash_id in self.bash_ids:
            test = self.tests[bash_id]
            console.print(f"[cyan]{bash_id[:6]}[/cyan] ({test.strategy}):")

            if test.sequential_pass is not None:
                seq_pct = (test.sequential_pass / test.sequential_total * 100)
                console.print(f"  Sequential: {test.sequential_pass}/{test.sequential_total} ({seq_pct:.1f}%)")

            if test.baseline_pass is not None:
                base_pct = (test.baseline_pass / test.baseline_total * 100)
                console.print(f"  Baseline:   {test.baseline_pass}/{test.baseline_total} ({base_pct:.1f}%)")

            console.print()


def main():
    if len(sys.argv) < 2:
        console.print("[yellow]Usage: python3 monitor.py <bash_id1> [bash_id2] [bash_id3][/yellow]")
        console.print("[dim]Example: python3 monitor.py fe6e5e 8c42af d9ac2f[/dim]")
        sys.exit(1)

    bash_ids = sys.argv[1:]

    dashboard = TestDashboard(bash_ids)
    dashboard.run()


if __name__ == "__main__":
    main()
