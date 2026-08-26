import pytest
from rpa2apa_api.domain import ModelProfile, ModelTask
from rpa2apa_api.models import ModelPolicyEngine, MultiModelExecutor, ProviderRegistry, MockProvider


@pytest.mark.asyncio
async def test_multimodel_fallback_executes_approved_profile():
    profiles = [
        ModelProfile(id="m", provider="mock", model="mock-model", capabilities={"reasoning"}, data_classes={"INTERNAL"})
    ]
    registry = ProviderRegistry()
    registry.register("mock", MockProvider())
    result = await MultiModelExecutor(ModelPolicyEngine(profiles), registry).fallback_generate(
        ModelTask(task_type="x", required_capabilities={"reasoning"}),
        system="s",
        prompt="p",
    )
    assert result.profile_id == "m"
    assert "mock-model" in result.output
