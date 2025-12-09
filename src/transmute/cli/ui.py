"""
CLI UI helpers.

Progress bars, colors, formatting for beautiful terminal output.
"""

from typing import Optional, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich import box

console = Console()


def print_success(message: str):
    """Print success message."""
    console.print(f"✓ {message}", style="bold green")


def print_error(message: str):
    """Print error message."""
    console.print(f"✗ {message}", style="bold red")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"⚠ {message}", style="bold yellow")


def print_info(message: str):
    """Print info message."""
    console.print(f"ℹ {message}", style="bold blue")


def print_header(title: str):
    """Print section header."""
    console.print()
    console.print(Panel(title, style="bold cyan", box=box.DOUBLE))
    console.print()


def create_progress():
    """Create progress bar."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    )


def create_table(title: str, columns: list) -> Table:
    """Create formatted table."""
    table = Table(title=title, box=box.ROUNDED)
    
    for column in columns:
        table.add_column(column, style="cyan")
    
    return table


def print_results_summary(
    total: int,
    completed: int,
    failed: int,
    success_rate: float
):
    """Print translation results summary."""
    table = Table(title="Translation Results", box=box.DOUBLE)
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Files", str(total))
    table.add_row("Completed", str(completed))
    table.add_row("Failed", str(failed))
    table.add_row("Success Rate", f"{success_rate:.1f}%")
    
    console.print()
    console.print(table)
    console.print()


def confirm(message: str, default: bool = False) -> bool:
    """Ask for confirmation."""
    return console.input(f"{message} [y/N]: ").lower().startswith('y')