from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Literal
from pydantic import BaseModel, Field


class MigrationState(str, Enum):
    IMPORTED = "IMPORTED"
    ANALYZED = "ANALYZED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    PLAN_APPROVED = "PLAN_APPROVED"
    GENERATED = "GENERATED"
    VALIDATED = "VALIDATED"
    SHADOW_TESTING = "SHADOW_TESTING"
    PRODUCTION_APPROVED = "PRODUCTION_APPROVED"
    DEPLOYED = "DEPLOYED"


class Classification(str, Enum):
    KEEP = "KEEP"
    TOOLIFY = "TOOLIFY"
    REASON = "REASON"
    HUMANIZE = "HUMANIZE"
    RETIRE = "RETIRE"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SourceRef(BaseModel):
    workflow: str
    activity_id: str | None = None
    display_name: str | None = None
    source_path: str | None = None


class Activity(BaseModel):
    id: str
    type: str
    display_name: str
    workflow: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    children: list[str] = Field(default_factory=list)
    source_ref: SourceRef


class Workflow(BaseModel):
    name: str
    path: str
    entry_point: bool = False
    activities: list[Activity] = Field(default_factory=list)
    invokes: list[str] = Field(default_factory=list)


class SourceProject(BaseModel):
    name: str
    root: str
    project_json: dict[str, Any] = Field(default_factory=dict)
    workflows: list[Workflow] = Field(default_factory=list)
    dependencies: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ProcessNode(BaseModel):
    id: str
    name: str
    intent: str
    source_refs: list[SourceRef] = Field(default_factory=list)
    classification: Classification
    agentization_score: int = Field(ge=0, le=100)
    risk: RiskLevel
    confidence: float = Field(ge=0, le=1)
    rationale: str
    target_type: str
    model_profile: str | None = None
    tool_name: str | None = None
    requires_approval: bool = False
    user_override: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProcessEdge(BaseModel):
    source: str
    target: str
    condition: str | None = None


class MigrationPlan(BaseModel):
    project_name: str
    strategy: Literal["conservative", "balanced", "aggressive", "custom"] = "balanced"
    nodes: list[ProcessNode]
    edges: list[ProcessEdge]
    warnings: list[str] = Field(default_factory=list)
    unsupported: list[str] = Field(default_factory=list)
    migration_confidence: int = Field(ge=0, le=100)
    approval_required: bool = True
    approved: bool = False
    approved_by: str | None = None


class APIRNode(BaseModel):
    id: str
    type: Literal[
        "deterministic", "agent", "tool", "human", "decision", "router",
        "subprocess", "memory", "event", "timer", "queue", "policy",
        "guardrail", "validation", "retrieval", "computer", "browser", "api", "mcp"
    ]
    name: str
    intent: str
    source_refs: list[SourceRef] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)


class APIRDocument(BaseModel):
    apiVersion: str = "rpa2apa.io/v1"
    kind: str = "AgenticProcess"
    metadata: dict[str, Any]
    spec: dict[str, Any]


class ModelProfile(BaseModel):
    id: str
    provider: str
    model: str
    capabilities: set[str] = Field(default_factory=set)
    data_classes: set[str] = Field(default_factory=lambda: {"PUBLIC", "INTERNAL"})
    relative_cost: float = 1.0
    relative_latency: float = 1.0
    quality_score: float = 0.7
    enabled: bool = True
    base_url: str | None = None


class ModelTask(BaseModel):
    task_type: str
    required_capabilities: set[str] = Field(default_factory=set)
    data_classification: str = "INTERNAL"
    max_relative_cost: float | None = None
    prefer_local: bool = False


class ApprovalDecision(BaseModel):
    reviewer: str
    role: str = "developer"
    approved: bool
    comment: str | None = None


class ToolPolicy(BaseModel):
    tool_name: str
    permissions: set[str] = Field(default_factory=set)
    approval_if: dict[str, Any] = Field(default_factory=dict)
    max_amount: float | None = None
    risk: RiskLevel = RiskLevel.LOW


class EvaluationResult(BaseModel):
    cases: int
    passed: int
    failed: int
    behavioral_equivalence: float
    agent_accuracy: float
    tool_accuracy: float
    warnings: list[str] = Field(default_factory=list)
