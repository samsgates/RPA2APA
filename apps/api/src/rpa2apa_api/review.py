from __future__ import annotations

from .domain import ApprovalDecision, Classification, MigrationPlan, RiskLevel


class ReviewEngine:
    def apply_override(self, plan: MigrationPlan, node_id: str, *, classification: Classification | None = None, target_type: str | None = None, model_profile: str | None = None, requires_approval: bool | None = None) -> MigrationPlan:
        found = False
        for node in plan.nodes:
            if node.id != node_id:
                continue
            found = True
            if classification is not None:
                node.classification = classification
            if target_type is not None:
                node.target_type = target_type
            if model_profile is not None:
                node.model_profile = model_profile
            if requires_approval is not None:
                node.requires_approval = requires_approval
            node.user_override = True
        if not found:
            raise KeyError(node_id)
        plan.approved = False
        plan.approved_by = None
        return plan

    def approve(self, plan: MigrationPlan, decision: ApprovalDecision) -> MigrationPlan:
        if not decision.approved:
            plan.approved = False
            plan.approved_by = None
            return plan
        unresolved = [n for n in plan.nodes if n.classification == Classification.MANUAL_REVIEW and not n.user_override]
        if unresolved:
            raise ValueError(f"Cannot approve with {len(unresolved)} unresolved manual-review nodes")
        critical = [n for n in plan.nodes if n.risk == RiskLevel.CRITICAL]
        if critical and decision.role not in {"security", "ai_governance", "admin"}:
            raise PermissionError("Critical-risk migration requires security/governance approval")
        plan.approved = True
        plan.approved_by = decision.reviewer
        return plan
