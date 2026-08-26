from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from .domain import Activity, Classification, ProcessNode, RiskLevel


@dataclass(frozen=True)
class Rule:
    pattern: re.Pattern
    classification: Classification
    target: str
    base_score: int
    risk: RiskLevel
    rationale: str


RULES = [
    Rule(re.compile(r"delay|wait", re.I), Classification.RETIRE, "retired", 0, RiskLevel.LOW, "Implementation timing mechanics should normally be replaced by explicit readiness checks."),
    Rule(re.compile(r"assign|addto|write line|log", re.I), Classification.KEEP, "deterministic", 2, RiskLevel.LOW, "Pure deterministic state or logging operation."),
    Rule(re.compile(r"http|rest|soap|sql|database|query|execute query", re.I), Classification.TOOLIFY, "api", 5, RiskLevel.MEDIUM, "Existing deterministic integration is best exposed as a typed tool."),
    Rule(re.compile(r"excel|read range|write range|workbook", re.I), Classification.TOOLIFY, "tool", 8, RiskLevel.LOW, "Structured data activity is better represented as a deterministic tool."),
    Rule(re.compile(r"mail|outlook|gmail|send smtp", re.I), Classification.TOOLIFY, "tool", 12, RiskLevel.MEDIUM, "Communication operation becomes an explicit audited tool."),
    Rule(re.compile(r"document|ocr|classif|extract", re.I), Classification.REASON, "agent", 72, RiskLevel.MEDIUM, "Unstructured document understanding benefits from bounded model reasoning."),
    Rule(re.compile(r"click|type into|browser|use application|navigate|select item|get text|uia", re.I), Classification.TOOLIFY, "browser", 35, RiskLevel.MEDIUM, "UI operations should be consolidated into semantic tools, preferably replaced by APIs."),
    Rule(re.compile(r"if|switch|flow decision|decision", re.I), Classification.KEEP, "decision", 25, RiskLevel.LOW, "Existing explicit business rules should remain deterministic unless semantic ambiguity is discovered."),
    Rule(re.compile(r"retry|trycatch|catch|throw", re.I), Classification.KEEP, "guardrail", 8, RiskLevel.LOW, "Failure behavior maps to deterministic retry/error policy."),
    Rule(re.compile(r"human|action center|approval", re.I), Classification.HUMANIZE, "human", 10, RiskLevel.HIGH, "Existing human interaction remains an explicit human-in-the-loop gate."),
    Rule(re.compile(r"sap|salesforce|servicenow|dynamics", re.I), Classification.TOOLIFY, "tool", 20, RiskLevel.MEDIUM, "Enterprise application steps should be promoted to reusable business tools."),
]

HIGH_RISK_WORDS = re.compile(r"payment|pay|delete|terminate|approve|transfer|refund|privilege|admin", re.I)
SEMANTIC_WORDS = re.compile(r"interpret|categor|reason|understand|review|assess|classif|exception|free.?text", re.I)


class AgentizationClassifier:
    def classify(self, activity: Activity) -> ProcessNode:
        hay = f"{activity.type} {activity.display_name} {' '.join(map(str, activity.attributes.values()))}"
        selected = next((r for r in RULES if r.pattern.search(hay)), None)
        if selected is None:
            selected = Rule(re.compile(".*"), Classification.MANUAL_REVIEW, "deterministic", 40, RiskLevel.MEDIUM, "Unknown activity requires explicit mapping or review.")

        score = selected.base_score
        classification = selected.classification
        rationale = selected.rationale
        risk = selected.risk
        target = selected.target

        if SEMANTIC_WORDS.search(hay) and classification not in {Classification.HUMANIZE, Classification.RETIRE}:
            score = max(score, 70)
            classification = Classification.REASON
            target = "agent"
            rationale += " Semantic/ambiguous intent signals raise the agentization opportunity."
        if HIGH_RISK_WORDS.search(hay):
            risk = RiskLevel.HIGH
            if classification == Classification.REASON:
                rationale += " High-impact side effects must remain behind deterministic policy and approval boundaries."

        if risk in {RiskLevel.HIGH, RiskLevel.CRITICAL} and target in {"agent", "tool", "api", "browser"}:
            requires_approval = True
        else:
            requires_approval = classification == Classification.HUMANIZE

        return ProcessNode(
            id=f"node:{activity.id}",
            name=activity.display_name,
            intent=self._intent(activity),
            source_refs=[activity.source_ref],
            classification=classification,
            agentization_score=min(100, score),
            risk=risk,
            confidence=0.82 if classification != Classification.MANUAL_REVIEW else 0.45,
            rationale=rationale,
            target_type=target,
            model_profile="reasoning-default" if target == "agent" else None,
            tool_name=self._tool_name(activity) if classification == Classification.TOOLIFY else None,
            requires_approval=requires_approval,
            metadata={"source_activity_type": activity.type},
        )

    def classify_all(self, activities: Iterable[Activity]) -> list[ProcessNode]:
        return [self.classify(a) for a in activities]

    def _intent(self, activity: Activity) -> str:
        name = re.sub(r"[_-]+", " ", activity.display_name).strip()
        return name if name else f"Execute {activity.type}"

    def _tool_name(self, activity: Activity) -> str:
        raw = re.sub(r"[^a-zA-Z0-9]+", "_", activity.display_name).strip("_").lower()
        return raw[:80] or "generated_tool"
