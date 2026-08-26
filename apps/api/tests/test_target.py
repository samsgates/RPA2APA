from pathlib import Path
from rpa2apa_api.parser import UiPathProjectParser
from rpa2apa_api.planner import MigrationPlanner
from rpa2apa_api.review import ReviewEngine
from rpa2apa_api.targets import TargetCompiler
from rpa2apa_api.domain import ApprovalDecision, Classification


def test_langgraph_target_generates_graph(tmp_path):
    root = Path(__file__).parents[3] / "examples" / "uipath-invoice"
    plan = MigrationPlanner().build(UiPathProjectParser().parse(root), require_review=True)
    review = ReviewEngine()
    for node in plan.nodes:
        if node.classification == Classification.MANUAL_REVIEW:
            review.apply_override(plan, node.id, classification=Classification.KEEP, target_type="deterministic")
    review.approve(plan, ApprovalDecision(reviewer="test", role="admin", approved=True))
    out = TargetCompiler(require_review=True).compile(plan, tmp_path / "out", target="langgraph")
    assert (out / "runtime" / "graph.py").exists()
    assert "langgraph" in (out / "pyproject.toml").read_text()
