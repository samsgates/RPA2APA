from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import uuid4

from .domain import Activity, SourceProject, SourceRef, Workflow


_DISPLAY = "DisplayName"


def local_name(tag: str) -> str:
    return tag.split("}")[-1].split(":")[-1]


class UiPathProjectParser:
    """Deterministic, best-effort UiPath project parser.

    This parser intentionally does not depend on an LLM. For production environments,
    the optional xaml-worker can replace/augment it with CoreWF-based parsing.
    """

    def parse(self, root: str | Path) -> SourceProject:
        root = Path(root).resolve()
        if not root.exists():
            raise FileNotFoundError(root)
        project_json_path = root / "project.json"
        project_json = {}
        warnings: list[str] = []
        if project_json_path.exists():
            try:
                project_json = json.loads(project_json_path.read_text(encoding="utf-8"))
            except Exception as exc:
                warnings.append(f"Cannot parse project.json: {exc}")
        else:
            warnings.append("project.json not found; treating directory as UiPath-style source")

        name = project_json.get("name") or root.name
        deps = project_json.get("dependencies") or {}
        entry = self._entry_point(project_json)
        workflows = []
        for xaml in sorted(root.rglob("*.xaml")):
            try:
                workflows.append(self._parse_xaml(xaml, root, entry))
            except Exception as exc:
                warnings.append(f"Failed to parse {xaml.relative_to(root)}: {exc}")

        if not workflows:
            warnings.append("No XAML workflows discovered")
        return SourceProject(
            name=name,
            root=str(root),
            project_json=project_json,
            workflows=workflows,
            dependencies=deps,
            warnings=warnings,
        )

    def _entry_point(self, pj: dict) -> str:
        main = pj.get("main") or pj.get("mainFile") or "Main.xaml"
        return str(main).replace("\\", "/")

    def _parse_xaml(self, path: Path, root: Path, entry: str) -> Workflow:
        tree = ET.parse(path)
        activity_list: list[Activity] = []
        invokes: list[str] = []
        rel = str(path.relative_to(root)).replace("\\", "/")

        for idx, elem in enumerate(tree.iter()):
            typ = local_name(elem.tag)
            if typ in {"Activity", "Members", "TextExpression.NamespacesForImplementation", "TextExpression.ReferencesForImplementation"} or "." in typ:
                continue
            attrs = {local_name(k): v for k, v in elem.attrib.items()}
            display = attrs.get(_DISPLAY) or attrs.get("Name") or typ
            aid = attrs.get("sap2010.WorkflowViewState.IdRef") or attrs.get("IdRef") or f"{path.stem}:{idx}:{typ}"
            ref = SourceRef(workflow=rel, activity_id=aid, display_name=display, source_path=rel)
            activity = Activity(
                id=aid,
                type=typ,
                display_name=display,
                workflow=rel,
                attributes=attrs,
                source_ref=ref,
            )
            activity_list.append(activity)
            if "InvokeWorkflowFile" in typ or typ == "InvokeWorkflowFile":
                target = attrs.get("WorkflowFileName") or attrs.get("FileName")
                if target:
                    invokes.append(target)
            if typ == "InvokeWorkflowFile" and not invokes:
                text = " ".join(str(v) for v in attrs.values())
                m = re.search(r'([\w ./\\-]+\.xaml)', text, re.I)
                if m:
                    invokes.append(m.group(1))

        return Workflow(
            name=path.stem,
            path=rel,
            entry_point=rel.lower() == entry.lower(),
            activities=activity_list,
            invokes=list(dict.fromkeys(invokes)),
        )
