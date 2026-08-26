# Security Model

RPA2APA follows explicit deterministic control boundaries.

## Required production controls

- OIDC/SAML SSO and RBAC
- external secret manager
- TLS everywhere
- immutable audit trail
- per-tool least privilege
- data classification and provider allowlists
- prompt injection defenses for untrusted documents/web/email
- egress controls for model providers
- cost and step budgets
- human gates for high-risk side effects
- signed build artifacts and SBOM

## Threats addressed by design

- prompt injection attempting tool misuse
- model hallucination causing side effects
- accidental data exfiltration to cloud models
- unreviewed migration changes
- silent unsupported UiPath activity loss
- brittle selectors
- infinite agent loops

The included code is a platform foundation. Organizations must integrate their IAM, SIEM, KMS, secret manager, and deployment security posture before production use.
