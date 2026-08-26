# Architecture

RPA2APA uses a compiler architecture:

```text
UiPath source -> deterministic parser -> normalized source graph
-> Process Archaeology -> migration plan -> Human Review
-> APIR -> target compiler -> sandbox/evaluation -> shadow -> deploy
```

## Trust boundaries

- LLMs never parse raw source as the only parser.
- LLMs never enforce financial/security policy.
- Agent actions use typed tools.
- High-risk tools require deterministic policy and optional human approval.
- Every target node keeps source references.

## Multi-model runtime

`ModelPolicyEngine` selects a model based on capabilities, data classification, cost, quality, locality, and availability. Providers are adapters, not business logic dependencies.

## APIR

APIR prevents lock-in to LangGraph or any individual agent framework. Compilers can consume the same reviewed plan and emit Python, LangGraph, OpenAI Agents, Temporal, or future runtimes.
