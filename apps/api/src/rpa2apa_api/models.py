from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Protocol
import httpx

from .domain import ModelProfile, ModelTask


class LLMProvider(Protocol):
    async def generate(self, *, model: str, system: str, prompt: str) -> str: ...


class MockProvider:
    async def generate(self, *, model: str, system: str, prompt: str) -> str:
        return json.dumps({"model": model, "summary": prompt[:240], "confidence": 0.55})


class OpenAICompatibleProvider:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url.rstrip("/")

    async def generate(self, *, model: str, system: str, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not configured")
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]


class AnthropicProvider:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.anthropic.com/v1"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url.rstrip("/")

    async def generate(self, *, model: str, system: str, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 2048,
                    "system": system,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            r.raise_for_status()
            data = r.json()
            return "\n".join(x.get("text", "") for x in data.get("content", []) if x.get("type") == "text")


class GeminiProvider:
    def __init__(self, api_key: str | None = None, base_url: str = "https://generativelanguage.googleapis.com/v1beta"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.base_url = base_url.rstrip("/")

    async def generate(self, *, model: str, system: str, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY not configured")
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                url,
                json={
                    "systemInstruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                },
            )
            r.raise_for_status()
            candidates = r.json().get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            return "\n".join(p.get("text", "") for p in parts)


class OllamaProvider:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")

    async def generate(self, *, model: str, system: str, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            r.raise_for_status()
            return r.json()["message"]["content"]


class ProviderRegistry:
    def __init__(self):
        self._providers: dict[str, LLMProvider] = {
            "mock": MockProvider(),
            "openai": OpenAICompatibleProvider(),
            "anthropic": AnthropicProvider(),
            "gemini": GeminiProvider(),
            "ollama": OllamaProvider(),
        }

    def register(self, name: str, provider: LLMProvider) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> LLMProvider:
        if name not in self._providers:
            raise KeyError(f"Unknown LLM provider: {name}")
        return self._providers[name]


DEFAULT_MODELS = [
    ModelProfile(
        id="reasoning-default",
        provider="mock",
        model="deterministic-mock",
        capabilities={"reasoning", "structured_output", "tools"},
        data_classes={"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED", "PII"},
        relative_cost=0,
        relative_latency=0.1,
        quality_score=0.55,
    ),
    ModelProfile(
        id="local-private",
        provider="ollama",
        model="qwen3",
        capabilities={"reasoning", "structured_output", "tools"},
        data_classes={"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED", "PII"},
        relative_cost=0.1,
        relative_latency=1.4,
        quality_score=0.72,
        enabled=False,
    ),
    ModelProfile(
        id="cloud-reasoning",
        provider="openai",
        model="gpt-5",
        capabilities={"reasoning", "structured_output", "tools", "vision"},
        data_classes={"PUBLIC", "INTERNAL"},
        relative_cost=1.0,
        relative_latency=1.0,
        quality_score=0.95,
        enabled=False,
    ),
]


class ModelPolicyEngine:
    def __init__(self, profiles: list[ModelProfile] | None = None):
        self.profiles = profiles or DEFAULT_MODELS

    def select(self, task: ModelTask) -> ModelProfile:
        eligible = self._eligible(task)
        if not eligible and task.prefer_local:
            return self.select(task.model_copy(update={"prefer_local": False}))
        if not eligible:
            raise RuntimeError(f"No approved model matches task policy: {task.model_dump()}")
        return sorted(eligible, key=lambda p: (-p.quality_score, p.relative_cost, p.relative_latency))[0]

    def fallback_chain(self, task: ModelTask) -> list[ModelProfile]:
        return sorted(self._eligible(task), key=lambda p: (-p.quality_score, p.relative_cost, p.relative_latency))

    def _eligible(self, task: ModelTask) -> list[ModelProfile]:
        eligible: list[ModelProfile] = []
        for p in self.profiles:
            if not p.enabled:
                continue
            if not task.required_capabilities.issubset(p.capabilities):
                continue
            if task.data_classification not in p.data_classes:
                continue
            if task.max_relative_cost is not None and p.relative_cost > task.max_relative_cost:
                continue
            if task.prefer_local and p.provider not in {"ollama", "vllm", "local"}:
                continue
            eligible.append(p)
        return eligible


@dataclass
class ModelExecution:
    profile_id: str
    provider: str
    model: str
    output: str
    error: str | None = None


class MultiModelExecutor:
    """Execute approved model fallback or critic/ensemble runs.

    Business-side effects are never executed from this class. It only produces text/structured reasoning.
    """

    def __init__(self, policy: ModelPolicyEngine | None = None, providers: ProviderRegistry | None = None):
        self.policy = policy or ModelPolicyEngine()
        self.providers = providers or ProviderRegistry()

    async def fallback_generate(self, task: ModelTask, *, system: str, prompt: str) -> ModelExecution:
        errors: list[str] = []
        for profile in self.policy.fallback_chain(task):
            try:
                output = await self.providers.get(profile.provider).generate(
                    model=profile.model, system=system, prompt=prompt
                )
                return ModelExecution(profile.id, profile.provider, profile.model, output)
            except Exception as exc:
                errors.append(f"{profile.id}: {exc}")
        raise RuntimeError("All approved model providers failed: " + " | ".join(errors))

    async def critic_generate(self, task: ModelTask, *, system: str, prompt: str) -> list[ModelExecution]:
        results: list[ModelExecution] = []
        for profile in self.policy.fallback_chain(task)[:3]:
            try:
                output = await self.providers.get(profile.provider).generate(
                    model=profile.model, system=system, prompt=prompt
                )
                results.append(ModelExecution(profile.id, profile.provider, profile.model, output))
            except Exception as exc:
                results.append(ModelExecution(profile.id, profile.provider, profile.model, "", str(exc)))
        return results
