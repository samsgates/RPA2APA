from __future__ import annotations

from dataclasses import dataclass
from .domain import RiskLevel, ToolPolicy


@dataclass
class PolicyDecision:
    allowed: bool
    requires_approval: bool = False
    reason: str = ""


class ToolPolicyEngine:
    """Deterministic side-effect boundary. Never delegate enforcement to prompts."""

    def evaluate(self, policy: ToolPolicy, arguments: dict, approved: bool = False) -> PolicyDecision:
        amount = arguments.get("amount")
        if policy.max_amount is not None and amount is not None and float(amount) > policy.max_amount:
            if approved:
                return PolicyDecision(True, False, "Human approval satisfied amount policy")
            return PolicyDecision(False, True, f"Amount {amount} exceeds automatic limit {policy.max_amount}")
        if policy.risk in {RiskLevel.HIGH, RiskLevel.CRITICAL} and not approved:
            return PolicyDecision(False, True, "High-risk tool requires explicit approval")
        return PolicyDecision(True, False, "Policy satisfied")
