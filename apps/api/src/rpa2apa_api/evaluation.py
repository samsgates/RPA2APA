from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from .domain import EvaluationResult


@dataclass
class BehavioralCase:
    input: dict[str, Any]
    expected: dict[str, Any]


class BehavioralEvaluator:
    def evaluate(self, cases: list[BehavioralCase], target: Callable[[dict], dict]) -> EvaluationResult:
        passed = 0
        warnings: list[str] = []
        for i, case in enumerate(cases):
            try:
                output = target(case.input)
                if all(output.get(k) == v for k, v in case.expected.items()):
                    passed += 1
                else:
                    warnings.append(f"Case {i} mismatch")
            except Exception as exc:
                warnings.append(f"Case {i} failed: {exc}")
        total = len(cases)
        ratio = passed / total if total else 1.0
        return EvaluationResult(
            cases=total,
            passed=passed,
            failed=total-passed,
            behavioral_equivalence=ratio,
            agent_accuracy=ratio,
            tool_accuracy=ratio,
            warnings=warnings,
        )


class ShadowComparator:
    def compare(self, original: list[dict], candidate: list[dict]) -> dict:
        total = max(len(original), len(candidate))
        matches = sum(1 for a,b in zip(original,candidate) if a == b)
        return {
            "cases": total,
            "matches": matches,
            "differences": total-matches,
            "behavioral_equivalence": matches/total if total else 1.0,
        }
