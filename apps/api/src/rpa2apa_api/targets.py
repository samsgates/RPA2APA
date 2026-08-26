from __future__ import annotations

from pathlib import Path
from .compiler import PythonAPACompiler
from .domain import MigrationPlan


class TargetCompiler:
    """Dispatch reviewed APIR plans to target runtimes.

    The Python target is dependency-light. The LangGraph target adds a generated graph adapter while
    preserving exactly the same reviewed plan, tools, policies, and traceability files.
    """

    def __init__(self, require_review: bool = True):
        self.base = PythonAPACompiler(require_review=require_review)

    def compile(self, plan: MigrationPlan, output: str | Path, target: str = "python") -> Path:
        target = target.lower()
        if target not in {"python", "langgraph"}:
            raise ValueError(f"Unsupported target: {target}")
        out = self.base.compile(plan, output)
        if target == "langgraph":
            self._add_langgraph(plan, out)
        return out

    def _add_langgraph(self, plan: MigrationPlan, out: Path) -> None:
        nodes = [n for n in plan.nodes if n.classification.value != "RETIRE"]
        first = nodes[0].id if nodes else None
        edges = [(e.source, e.target) for e in plan.edges if any(n.id == e.source for n in nodes) and any(n.id == e.target for n in nodes)]
        node_ids = [n.id for n in nodes]
        safe = {n.id: f"step_{i}" for i, n in enumerate(nodes)}
        lines = [
            '"""Generated LangGraph adapter. Replace placeholder node bodies with reviewed tools/agents."""',
            "from typing import TypedDict, Any",
            "from langgraph.graph import StateGraph, START, END",
            "",
            "class State(TypedDict, total=False):",
            "    data: dict[str, Any]",
            "    audit: list[dict[str, Any]]",
            "",
        ]
        for n in nodes:
            fn = safe[n.id]
            lines += [
                f"def {fn}(state: State) -> State:",
                "    audit = list(state.get('audit', []))",
                f"    audit.append({{'event':'step.complete','source_id':{n.id!r},'name':{n.name!r}}})",
                "    return {**state, 'audit': audit}",
                "",
            ]
        lines += ["builder = StateGraph(State)"]
        for n in nodes:
            lines.append(f"builder.add_node({safe[n.id]!r}, {safe[n.id]})")
        if first:
            lines.append(f"builder.add_edge(START, {safe[first]!r})")
        for a,b in edges:
            lines.append(f"builder.add_edge({safe[a]!r}, {safe[b]!r})")
        targets = {a for a,_ in edges}
        for n in node_ids:
            if n not in targets:
                lines.append(f"builder.add_edge({safe[n]!r}, END)")
        if not nodes:
            lines += [
                "def empty(state: State) -> State: return state",
                "builder.add_node('empty', empty)",
                "builder.add_edge(START, 'empty')",
                "builder.add_edge('empty', END)",
            ]
        lines += ["graph = builder.compile()", ""]
        (out / "runtime" / "graph.py").write_text("\n".join(lines), encoding="utf-8")
        pyproject = (out / "pyproject.toml").read_text(encoding="utf-8")
        pyproject = pyproject.replace("dependencies=[]", 'dependencies=["langgraph>=1,<2"]')
        (out / "pyproject.toml").write_text(pyproject, encoding="utf-8")
