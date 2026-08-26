from pathlib import Path
import pytest
from rpa2apa_api.parser import UiPathProjectParser
from rpa2apa_api.planner import MigrationPlanner
from rpa2apa_api.review import ReviewEngine
from rpa2apa_api.compiler import PythonAPACompiler, CompilationBlocked
from rpa2apa_api.domain import ApprovalDecision, Classification


def source():
    return UiPathProjectParser().parse(Path(__file__).parents[3] / "examples" / "uipath-invoice")


def test_review_gate_blocks_compile(tmp_path):
    plan = MigrationPlanner().build(source(), require_review=True)
    with pytest.raises(CompilationBlocked):
        PythonAPACompiler(require_review=True).compile(plan, tmp_path/"out")


def test_approved_plan_compiles(tmp_path):
    plan = MigrationPlanner().build(source(), require_review=True)
    # Resolve unknown activities conservatively.
    review = ReviewEngine()
    for node in plan.nodes:
        if node.classification == Classification.MANUAL_REVIEW:
            review.apply_override(plan, node.id, classification=Classification.KEEP, target_type="deterministic")
    review.approve(plan, ApprovalDecision(reviewer="test", role="admin", approved=True))
    out = PythonAPACompiler(require_review=True).compile(plan, tmp_path/"out")
    assert (out/"apir.yaml").exists()
    assert (out/"runtime"/"process.py").exists()
