from __future__ import annotations

import json
from .domain import MigrationPlan, ModelTask
from .models import MultiModelExecutor


SYSTEM = """You are the RPA2APA semantic migration analyst. Analyze normalized RPA metadata, never invent missing source behavior, clearly mark uncertainty, prefer deterministic execution when possible, and never weaken an existing human or security control."""


class SemanticEnricher:
    """Optional LLM enrichment after deterministic parsing and rule-based classification.

    This component only suggests metadata. It does not silently mutate approved execution semantics.
    """

    def __init__(self, executor: MultiModelExecutor | None = None):
        self.executor = executor or MultiModelExecutor()

    async def review_node(self, node) -> dict:
        task = ModelTask(
            task_type="migration_semantic_review",
            required_capabilities={"reasoning", "structured_output"},
            data_classification=node.metadata.get("data_classification", "INTERNAL"),
        )
        prompt = json.dumps(
            {
                "name": node.name,
                "intent": node.intent,
                "classification": node.classification.value,
                "agentization_score": node.agentization_score,
                "risk": node.risk.value,
                "rationale": node.rationale,
                "source_refs": [r.model_dump() for r in node.source_refs],
            },
            indent=2,
        )
        execution = await self.executor.fallback_generate(task, system=SYSTEM, prompt=prompt)
        return {
            "provider": execution.provider,
            "model": execution.model,
            "profile": execution.profile_id,
            "analysis": execution.output,
        }

    async def critic_plan(self, plan: MigrationPlan) -> list[dict]:
        task = ModelTask(
            task_type="migration_critic",
            required_capabilities={"reasoning"},
            data_classification="INTERNAL",
        )
        prompt = plan.model_dump_json(indent=2)
        outputs = await self.executor.critic_generate(
            task,
            system=SYSTEM + " Review the migration plan for over-agentization, missing deterministic boundaries, risky side effects, and unsupported assumptions.",
            prompt=prompt,
        )
        return [x.__dict__ for x in outputs]
