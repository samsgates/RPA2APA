# Implementation Status

This repository is a functioning RPA2APA foundation with an end-to-end UiPath-to-APA migration path.

## Implemented

- UiPath `project.json` and XAML discovery/parsing
- deterministic source graph extraction
- KTRHR migration classification
- agentization/risk/confidence scoring
- Process Archaeology baseline
- APIR v1 schema and generator
- human review overrides and approval enforcement
- secure ZIP project upload/extraction
- model registry and policy routing
- OpenAI-compatible, Anthropic, Gemini, Ollama, and mock provider adapters
- multi-model fallback and critic execution
- deterministic high-risk tool policy engine
- prompt version registry
- Python APA compiler
- LangGraph target adapter
- source-to-target traceability
- generated tool/agent/policy/runtime skeletons
- behavioral evaluator and shadow comparator
- FastAPI control plane
- Next.js Review Studio source
- CLI
- Docker Compose, Kubernetes starter deployment, CI
- sample UiPath project and generated APA output
- automated backend tests

## Extension seams intentionally left explicit

Production SAP, Salesforce, ServiceNow, email, payment, and other enterprise side effects require organization-specific credentials and APIs. Generated tools therefore contain explicit implementation seams instead of fabricated integrations. SSO/SAML, enterprise secret managers, SIEM wiring, full estate-scale persistence, and vendor-specific activity catalogs are extension layers documented in the roadmap.
