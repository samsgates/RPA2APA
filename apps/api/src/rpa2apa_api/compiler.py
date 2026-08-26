from __future__ import annotations

import json
import re
from pathlib import Path
import yaml

from .apir import APIRBuilder
from .domain import MigrationPlan


def safe_name(value: str) -> str:
    v = re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()
    return v or "step"


class CompilationBlocked(RuntimeError):
    pass


class PythonAPACompiler:
    def __init__(self, require_review: bool = True):
        self.require_review = require_review
        self.apir_builder = APIRBuilder()

    def compile(self, plan: MigrationPlan, output: str | Path) -> Path:
        if self.require_review and plan.approval_required and not plan.approved:
            raise CompilationBlocked("Migration plan requires review and approval before agentic compilation")
        out = Path(output).resolve()
        out.mkdir(parents=True, exist_ok=True)
        for d in ["agents", "tools", "deterministic", "policies", "prompts", "tests", "migration", "runtime"]:
            (out / d).mkdir(exist_ok=True)

        apir = self.apir_builder.from_plan(plan)
        (out / "apir.yaml").write_text(
            yaml.safe_dump(apir.model_dump(mode="json"), sort_keys=False), encoding="utf-8"
        )
        (out / "migration" / "source-map.json").write_text(
            json.dumps({n.id: [r.model_dump() for r in n.source_refs] for n in plan.nodes}, indent=2),
            encoding="utf-8",
        )
        (out / "migration" / "plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")

        tool_nodes = [n for n in plan.nodes if n.classification.value == "TOOLIFY"]
        agent_nodes = [n for n in plan.nodes if n.classification.value == "REASON"]
        deterministic_nodes = [n for n in plan.nodes if n.classification.value == "KEEP"]

        (out / "tools" / "generated.py").write_text(self._tools(tool_nodes), encoding="utf-8")
        (out / "agents" / "generated.py").write_text(self._agents(agent_nodes), encoding="utf-8")
        (out / "deterministic" / "generated.py").write_text(self._deterministic(deterministic_nodes), encoding="utf-8")
        (out / "runtime" / "process.py").write_text(self._runtime(plan), encoding="utf-8")
        (out / "policies" / "tool-policy.yaml").write_text(self._policies(plan), encoding="utf-8")
        (out / "README.md").write_text(self._readme(plan), encoding="utf-8")
        (out / "pyproject.toml").write_text(self._pyproject(plan), encoding="utf-8")
        (out / "Dockerfile").write_text(
            'FROM python:3.12-slim\nWORKDIR /app\nCOPY . .\nRUN pip install .\nCMD ["python", "-m", "runtime.process"]\n',
            encoding="utf-8",
        )
        for pkg in ["agents", "tools", "deterministic", "runtime"]:
            (out / pkg / "__init__.py").write_text("", encoding="utf-8")
        return out

    def _tools(self, nodes):
        lines = [
            '"""Generated deterministic tool boundary. Implement integrations before production."""',
            "from typing import Any",
            "",
        ]
        if not nodes:
            lines += [
                "def no_generated_tools(**kwargs: Any) -> dict:",
                '    return {"ok": True, "note": "No toolified source nodes"}',
                "",
            ]
        for n in nodes:
            fn = safe_name(n.tool_name or n.name)
            source = n.source_refs[0].workflow if n.source_refs else "unknown"
            lines += [
                f"def {fn}(**kwargs: Any) -> dict:",
                f'    """Intent: {n.intent}. Source: {source}."""',
                "    # TODO: replace with API/MCP/SDK integration. Do not place secrets in source.",
                f'    return {{"ok": True, "tool": "{fn}", "input": kwargs}}',
                "",
            ]
        return "\n".join(lines)

    def _agents(self, nodes):
        lines = [
            '"""Generated bounded agent specifications."""',
            "from dataclasses import dataclass",
            "",
            "@dataclass",
            "class AgentSpec:",
            "    name: str",
            "    objective: str",
            "    model_profile: str",
            "    max_turns: int = 8",
            "",
            "AGENTS = [",
        ]
        for n in nodes:
            lines.append(
                f"    AgentSpec(name={n.name!r}, objective={n.intent!r}, model_profile={(n.model_profile or 'reasoning-default')!r}),"
            )
        lines.append("]")
        return "\n".join(lines) + "\n"

    def _deterministic(self, nodes):
        lines = [
            '"""Generated deterministic steps. Review TODO semantics against source traceability."""',
            "from typing import Any",
            "",
        ]
        for n in nodes:
            fn = safe_name(n.name)
            lines += [
                f"def {fn}(state: dict[str, Any]) -> dict[str, Any]:",
                f'    """{n.intent}"""',
                "    return state",
                "",
            ]
        if not nodes:
            lines += [
                "def passthrough(state: dict[str, Any]) -> dict[str, Any]:",
                "    return state",
                "",
            ]
        return "\n".join(lines)

    def _runtime(self, plan):
        steps = [n for n in plan.nodes if n.classification.value != "RETIRE"]
        process_json = json.dumps(
            [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.target_type,
                    "requires_approval": n.requires_approval,
                    "risk": n.risk.value,
                }
                for n in steps
            ],
            indent=2,
        )
        return (
            '"""RPA2APA generated reference runtime.\n\n'
            "This file is intentionally framework-light. Replace the execution seam with a "
            'LangGraph/OpenAI Agents adapter when desired.\n"""\n'
            "from __future__ import annotations\n"
            "from dataclasses import dataclass, field\n"
            "from typing import Any\n\n"
            "@dataclass\n"
            "class RunState:\n"
            "    data: dict[str, Any] = field(default_factory=dict)\n"
            "    audit: list[dict[str, Any]] = field(default_factory=list)\n\n"
            "class ApprovalRequired(RuntimeError):\n"
            "    pass\n\n"
            f"PROCESS = {process_json}\n\n"
            "def run(initial: dict[str, Any] | None = None, approvals: set[str] | None = None) -> RunState:\n"
            "    state = RunState(data=initial or {})\n"
            "    approvals = approvals or set()\n"
            "    for step in PROCESS:\n"
            "        state.audit.append({'event': 'step.enter', 'step': step['id']})\n"
            "        if step['requires_approval'] and step['id'] not in approvals:\n"
            "            raise ApprovalRequired(f\"Approval required before {step['name']}\")\n"
            "        # Generated skeleton. Wire explicit deterministic tools or bounded agents here.\n"
            "        state.audit.append({'event': 'step.complete', 'step': step['id']})\n"
            "    return state\n\n"
            "if __name__ == '__main__':\n"
            "    print(run().audit)\n"
        )

    def _policies(self, plan):
        policies = []
        for n in plan.nodes:
            if n.classification.value == "TOOLIFY":
                policies.append(
                    {
                        "tool": n.tool_name or safe_name(n.name),
                        "risk": n.risk.value,
                        "requiresApproval": n.requires_approval,
                        "source": [r.model_dump() for r in n.source_refs],
                    }
                )
        return yaml.safe_dump({"version": "v1", "tools": policies}, sort_keys=False)

    def _readme(self, plan):
        return f"""# Generated APA: {plan.project_name}

Generated by RPA2APA. Migration confidence: **{plan.migration_confidence}%**.

## Safety

This output is a reviewed migration skeleton, not a guarantee that source and target are semantically equivalent. Run generated tests, sandbox evaluation, historical replay, and shadow execution before production.

## Traceability

See `migration/source-map.json` and `migration/plan.json`.
"""

    def _pyproject(self, plan):
        name = safe_name(plan.project_name).replace("_", "-")
        return f"""[build-system]
requires=["hatchling"]
build-backend="hatchling.build"

[project]
name="{name}-apa"
version="0.1.0"
requires-python=">=3.11"
dependencies=[]
"""
