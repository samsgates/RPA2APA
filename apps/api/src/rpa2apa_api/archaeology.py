from __future__ import annotations

from collections import Counter
from .domain import ProcessEdge, ProcessNode, SourceProject
from .classifier import AgentizationClassifier


class ProcessArchaeologyEngine:
    """Recover a normalized process from technical activities.

    v0.1 groups adjacent low-level activities into reviewable nodes conservatively.
    The architecture intentionally leaves a pluggable semantic-enricher seam for LLMs.
    """

    def __init__(self, classifier: AgentizationClassifier | None = None):
        self.classifier = classifier or AgentizationClassifier()

    def reconstruct(self, source: SourceProject) -> tuple[list[ProcessNode], list[ProcessEdge], list[str]]:
        nodes: list[ProcessNode] = []
        edges: list[ProcessEdge] = []
        warnings = list(source.warnings)

        previous: str | None = None
        for wf in source.workflows:
            for activity in wf.activities:
                node = self.classifier.classify(activity)
                nodes.append(node)
                if previous:
                    edges.append(ProcessEdge(source=previous, target=node.id))
                previous = node.id

        if not nodes:
            warnings.append("Process Archaeology found no executable nodes")
        return nodes, edges, warnings

    def summary(self, source: SourceProject) -> dict:
        types = Counter(a.type for wf in source.workflows for a in wf.activities)
        return {
            "project": source.name,
            "workflows": len(source.workflows),
            "activities": sum(len(w.activities) for w in source.workflows),
            "top_activity_types": types.most_common(10),
            "dependencies": len(source.dependencies),
        }
