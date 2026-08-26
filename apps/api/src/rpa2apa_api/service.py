from __future__ import annotations

from pathlib import Path
from uuid import uuid4
from .parser import UiPathProjectParser
from .planner import MigrationPlanner
from .review import ReviewEngine
from .targets import TargetCompiler
from .domain import ApprovalDecision, Classification, MigrationPlan, SourceProject


class InMemoryStore:
    def __init__(self):
        self.sources: dict[str, SourceProject] = {}
        self.plans: dict[str, MigrationPlan] = {}


class MigrationService:
    def __init__(self, require_review: bool = True):
        self.parser = UiPathProjectParser()
        self.planner = MigrationPlanner()
        self.review = ReviewEngine()
        self.compiler = TargetCompiler(require_review=require_review)
        self.store = InMemoryStore()

    def import_project(self, path: str) -> tuple[str, SourceProject]:
        source = self.parser.parse(path)
        pid = uuid4().hex
        self.store.sources[pid] = source
        return pid, source

    def analyze(self, pid: str, strategy: str = "balanced") -> MigrationPlan:
        source = self.store.sources[pid]
        plan = self.planner.build(source, strategy=strategy, require_review=self.compiler.require_review)
        self.store.plans[pid] = plan
        return plan

    def override(self, pid: str, node_id: str, **kwargs) -> MigrationPlan:
        plan = self.store.plans[pid]
        return self.review.apply_override(plan, node_id, **kwargs)

    def approve(self, pid: str, decision: ApprovalDecision) -> MigrationPlan:
        return self.review.approve(self.store.plans[pid], decision)

    def compile(self, pid: str, output: str, target: str = "python") -> str:
        return str(self.compiler.compile(self.store.plans[pid], output, target=target))
