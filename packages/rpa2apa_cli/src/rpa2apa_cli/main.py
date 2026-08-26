from __future__ import annotations

import json
import sys
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

# Developer-friendly source-tree import when running from monorepo.
repo = Path(__file__).resolve().parents[4]
api_src = repo / "apps" / "api" / "src"
if api_src.exists():
    sys.path.insert(0, str(api_src))

from rpa2apa_api.parser import UiPathProjectParser
from rpa2apa_api.planner import MigrationPlanner
from rpa2apa_api.targets import TargetCompiler
from rpa2apa_api.review import ReviewEngine
from rpa2apa_api.domain import ApprovalDecision, Classification
from rpa2apa_api.apir import APIRBuilder

app = typer.Typer(help="Migrate UiPath RPA projects into governed Agentic Process Automation.")
console = Console()


def build_plan(path: Path, strategy: str = "balanced"):
    src = UiPathProjectParser().parse(path)
    return src, MigrationPlanner().build(src, strategy=strategy, require_review=True)


@app.command()
def analyze(path: Path, strategy: str = "balanced"):
    src, plan = build_plan(path, strategy)
    metrics = MigrationPlanner().metrics(plan)
    console.print(f"[bold]RPA2APA Analysis: {src.name}[/bold]")
    console.print(f"Workflows: {len(src.workflows)}  Activities: {sum(len(w.activities) for w in src.workflows)}")
    table = Table("Classification", "Count")
    for k,v in sorted(metrics["counts"].items()): table.add_row(k, str(v))
    console.print(table)
    console.print(f"Migration confidence: [bold]{plan.migration_confidence}%[/bold]")
    console.print(f"Agentization opportunity: {metrics['agentization_opportunity']}")


@app.command()
def plan(path: Path, output: Path = Path("./rpa2apa-plan"), strategy: str = "balanced"):
    _, migration = build_plan(path, strategy)
    output.mkdir(parents=True, exist_ok=True)
    (output/"migration-plan.json").write_text(migration.model_dump_json(indent=2))
    apir = APIRBuilder().from_plan(migration)
    (output/"apir-preview.json").write_text(apir.model_dump_json(indent=2))
    console.print(f"Plan written to {output.resolve()}")
    console.print("Review and approve the plan before agentic conversion.")


@app.command()
def convert(path: Path, output: Path = Path("./generated-apa"), target: str = "python", approve: bool = typer.Option(False, help="Explicitly approve all mapped nodes for local developer conversion.")):
    if target not in {"python", "langgraph"}:
        raise typer.BadParameter("Supported targets in v0.1: python, langgraph")
    _, migration = build_plan(path)
    if approve:
        review = ReviewEngine()
        for node in migration.nodes:
            if node.classification == Classification.MANUAL_REVIEW:
                review.apply_override(migration, node.id, classification=Classification.KEEP, target_type="deterministic")
        review.approve(migration, ApprovalDecision(reviewer="cli-user", role="admin", approved=True, comment="Explicit --approve"))
    compiler = TargetCompiler(require_review=True)
    try:
        out = compiler.compile(migration, output, target=target)
    except Exception as exc:
        console.print(f"[red]Conversion blocked:[/red] {exc}")
        console.print("Run `rpa2apa plan`, review the decisions, then use Review Studio or explicit --approve for a developer-only local conversion.")
        raise typer.Exit(2)
    console.print(f"Generated APA: {out}")


@app.command()
def review(path: Path):
    console.print("Review Studio is the web application in apps/web.")
    console.print("Start the API and web app, import the project, review each node, and approve the plan before compilation.")


if __name__ == "__main__":
    app()
