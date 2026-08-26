from __future__ import annotations

from collections import Counter
from .archaeology import ProcessArchaeologyEngine
from .domain import Classification, MigrationPlan, SourceProject


class MigrationPlanner:
    def __init__(self, archaeology: ProcessArchaeologyEngine | None = None):
        self.archaeology = archaeology or ProcessArchaeologyEngine()

    def build(self, source: SourceProject, strategy: str = "balanced", require_review: bool = True) -> MigrationPlan:
        nodes, edges, warnings = self.archaeology.reconstruct(source)
        unsupported = [n.name for n in nodes if n.classification == Classification.MANUAL_REVIEW]
        coverage = 1.0 if not nodes else (len(nodes) - len(unsupported)) / len(nodes)
        avg_conf = sum(n.confidence for n in nodes) / max(1, len(nodes))
        risk_penalty = sum(1 for n in nodes if n.risk.value in {"HIGH", "CRITICAL"}) / max(1, len(nodes))
        confidence = int(max(0, min(100, (coverage * 0.55 + avg_conf * 0.4 + (1-risk_penalty)*0.05) * 100)))
        return MigrationPlan(
            project_name=source.name,
            strategy=strategy,
            nodes=nodes,
            edges=edges,
            warnings=warnings,
            unsupported=unsupported,
            migration_confidence=confidence,
            approval_required=require_review,
            approved=not require_review,
        )

    def metrics(self, plan: MigrationPlan) -> dict:
        counts = Counter(n.classification.value for n in plan.nodes)
        return {
            "counts": dict(counts),
            "agentization_opportunity": round(sum(n.agentization_score for n in plan.nodes) / max(1, len(plan.nodes)), 1),
            "migration_confidence": plan.migration_confidence,
            "requires_human_runtime_gates": sum(1 for n in plan.nodes if n.requires_approval),
        }
