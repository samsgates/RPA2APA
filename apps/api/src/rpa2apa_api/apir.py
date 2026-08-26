from __future__ import annotations

from .domain import APIRDocument, MigrationPlan, Classification


TYPE_MAP = {
    Classification.KEEP: "deterministic",
    Classification.TOOLIFY: "tool",
    Classification.REASON: "agent",
    Classification.HUMANIZE: "human",
    Classification.RETIRE: "validation",
    Classification.MANUAL_REVIEW: "human",
}


class APIRBuilder:
    def from_plan(self, plan: MigrationPlan) -> APIRDocument:
        nodes = []
        for n in plan.nodes:
            if n.classification == Classification.RETIRE:
                continue
            node_type = TYPE_MAP[n.classification]
            if n.target_type in {"browser", "api", "mcp", "human", "decision"}:
                node_type = n.target_type if n.target_type != "decision" or n.classification == Classification.KEEP else node_type
            nodes.append({
                "id": n.id,
                "type": node_type,
                "name": n.name,
                "intent": n.intent,
                "source_refs": [r.model_dump() for r in n.source_refs],
                "config": {
                    "classification": n.classification.value,
                    "agentization_score": n.agentization_score,
                    "risk": n.risk.value,
                    "confidence": n.confidence,
                    "model_profile": n.model_profile,
                    "tool_name": n.tool_name,
                    "requires_approval": n.requires_approval,
                },
            })
        return APIRDocument(
            metadata={"name": plan.project_name, "migrationConfidence": plan.migration_confidence},
            spec={
                "goal": f"Migrated agentic process for {plan.project_name}",
                "nodes": nodes,
                "edges": [e.model_dump() for e in plan.edges if any(x["id"] == e.source for x in nodes) and any(x["id"] == e.target for x in nodes)],
                "governance": {"reviewApproved": plan.approved, "strategy": plan.strategy},
            },
        )
