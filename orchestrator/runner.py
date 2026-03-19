from __future__ import annotations
import time
from pathlib import Path
import typer

from dotenv import load_dotenv
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from orchestrator.graph import compile_graph
from orchestrator.state import AIROState, ComputeBudget, TaskType

load_dotenv()  

app = typer.Typer(
    name="airo",
    help="AIRO — AI Research Orchestrator. Automate your ML experiments end-to-end.",
    add_completion=False,
)
console = Console()


def _print_banner() -> None:
    console.print(Panel.fit(
        "[bold blue]AIRO[/] — [dim]AI Research Orchestrator[/]\n"
        "[dim]Multi-Agent ML Automation · 2026[/]",
        border_style="blue",
    ))


def _print_summary(state: dict) -> None:
    """Print pipeline summary. state is a dict returned by LangGraph."""
    table = Table(title="Pipeline Summary", show_header=True, header_style="bold blue")
    table.add_column("Agent", style="cyan")
    table.add_column("Time (s)", justify="right")
    table.add_column("Status", justify="center")

    agent_timings = state.get("agent_timings", {})
    errors = state.get("errors", [])

    agents = ["data", "config", "train", "critic", "evaluate", "report"]
    for agent in agents:
        t = agent_timings.get(agent, 0)
        agent_errors = [e for e in errors if e.startswith(f"[{agent}]")]
        status = "❌" if agent_errors else "✅"
        table.add_row(agent.capitalize(), f"{t:.1f}", status)

    console.print(table)

    best_run_id = state.get("best_run_id", "")
    if best_run_id:
        task_type = state.get("task_type", "classification")
        metric_name = "f1_macro" if task_type == "classification" else "rmse"
        console.print(Panel(
            f"[bold green]Best model:[/] {state.get('best_model_type', 'N/A')}\n"
            f"[bold green]{metric_name.upper()}:[/] "
            f"{state.get('improvement_over_baseline_pct', 0):+.1f}% vs baseline\n"
            f"[bold green]Report:[/] {state.get('report_pdf_path', state.get('report_md_path', 'N/A'))}",
            title="[bold]EXPERIMENT COMPLETE[/]",
            border_style="green",
        ))

    if errors:
        console.print("[bold red]Errors encountered:[/]")
        for err in errors:
            console.print(f"  [red]•[/] {err}")


@app.command()
def run(
    dataset: Path = typer.Option(..., "--dataset", "-d", help="Path to raw dataset (CSV/parquet/JSON)"),
    task: TaskType = typer.Option(TaskType.CLASSIFICATION, "--task", "-t", help="ML task type"),
    target: str = typer.Option("target", "--target", help="Target column name"),
    budget: ComputeBudget = typer.Option(ComputeBudget.STANDARD, "--budget", "-b", help="Compute budget"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Run the full AIRO multi-agent ML pipeline."""

    _print_banner()

    if not dataset.exists():
        console.print(f"[red]Dataset not found:[/] {dataset}")
        raise typer.Exit(1)

    initial_state = AIROState(
        dataset_path=str(dataset),
        task_type=task,
        target_column=target,
        compute_budget=budget,
    )

    console.print(f"\n[bold]Experiment[/] [cyan]{initial_state.experiment_id}[/]")
    console.print(f"Dataset: [dim]{dataset}[/]  Task: [dim]{task}[/]  Budget: [dim]{budget}[/]\n")

    graph = compile_graph()

    start = time.perf_counter()
    config = {"recursion_limit": 50}

    if verbose:
        final_state = {}
        for step in graph.stream(initial_state, config=config):
            node, data = next(iter(step.items()))
            elapsed = time.perf_counter() - start
            logger.info(f"[{node}] completed in {elapsed:.1f}s")
            final_state = data if isinstance(data, dict) else step
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task_id = progress.add_task("Running AIRO pipeline...", total=None)
            final_state = graph.invoke(initial_state, config=config)
            progress.update(task_id, description="Pipeline complete")

    console.print()
    _print_summary(final_state)


if __name__ == "__main__":
    app()
    