from rpa2apa_api.domain import RiskLevel, ToolPolicy
from rpa2apa_api.policy import ToolPolicyEngine


def test_high_risk_requires_approval():
    p = ToolPolicy(tool_name="create_payment", risk=RiskLevel.HIGH)
    d = ToolPolicyEngine().evaluate(p, {"amount": 100})
    assert not d.allowed and d.requires_approval
    assert ToolPolicyEngine().evaluate(p, {"amount": 100}, approved=True).allowed
