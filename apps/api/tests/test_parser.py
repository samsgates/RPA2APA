from pathlib import Path
from rpa2apa_api.parser import UiPathProjectParser


def fixture_root():
    return Path(__file__).parents[3] / "examples" / "uipath-invoice"


def test_parses_project():
    p = UiPathProjectParser().parse(fixture_root())
    assert p.name == "InvoiceProcessor"
    assert p.workflows
    assert any(w.entry_point for w in p.workflows)
    assert sum(len(w.activities) for w in p.workflows) > 0
