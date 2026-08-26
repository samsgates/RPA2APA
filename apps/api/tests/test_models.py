from rpa2apa_api.domain import ModelProfile, ModelTask
from rpa2apa_api.models import ModelPolicyEngine


def test_privacy_routing_prefers_allowed_local_model():
    engine = ModelPolicyEngine([
        ModelProfile(id="cloud", provider="openai", model="x", capabilities={"reasoning"}, data_classes={"PUBLIC"}, quality_score=.99),
        ModelProfile(id="local", provider="ollama", model="y", capabilities={"reasoning"}, data_classes={"RESTRICTED"}, quality_score=.8),
    ])
    selected = engine.select(ModelTask(task_type="case", required_capabilities={"reasoning"}, data_classification="RESTRICTED"))
    assert selected.id == "local"
