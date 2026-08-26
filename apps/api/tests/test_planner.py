from pathlib import Path
from rpa2apa_api.parser import UiPathProjectParser
from rpa2apa_api.planner import MigrationPlanner
from rpa2apa_api.domain import Classification


def test_plan_contains_reviewable_classifications():
    root = Path(__file__).parents[3] / "examples" / "uipath-invoice"
    source = UiPathProjectParser().parse(root)
    plan = MigrationPlanner().build(source)
    assert 0 <= plan.migration_confidence <= 100
    assert any(n.classification == Classification.TOOLIFY for n in plan.nodes)
    assert any(n.classification == Classification.REASON for n in plan.nodes)
