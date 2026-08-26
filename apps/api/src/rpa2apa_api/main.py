from __future__ import annotations

import tempfile
import shutil
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import get_settings
from .domain import ApprovalDecision, Classification, ModelTask
from .models import ModelPolicyEngine
from .service import MigrationService
from .uploads import extract_project_zip

settings = get_settings()
service = MigrationService(require_review=settings.require_review)
model_policy = ModelPolicyEngine()

app = FastAPI(title="RPA2APA API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.allowed_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ImportRequest(BaseModel):
    path: str


class AnalyzeRequest(BaseModel):
    strategy: str = "balanced"


class OverrideRequest(BaseModel):
    node_id: str
    classification: Classification | None = None
    target_type: str | None = None
    model_profile: str | None = None
    requires_approval: bool | None = None


class CompileRequest(BaseModel):
    output: str | None = None
    target: str = "python"


@app.get("/health")
def health():
    return {"ok": True, "service": "rpa2apa", "version": "0.1.0"}


@app.post("/projects/upload")
async def upload_project(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".zip"):
        raise HTTPException(415, "Upload a ZIP containing the UiPath project")
    tmp = Path(tempfile.mkdtemp(prefix="rpa2apa-incoming-")) / "project.zip"
    try:
        with tmp.open("wb") as fh:
            while chunk := await file.read(1024 * 1024):
                fh.write(chunk)
        root = extract_project_zip(tmp)
        pid, source = service.import_project(str(root))
        return {"project_id": pid, "source": source}
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/projects/import")
def import_project(req: ImportRequest):
    try:
        pid, source = service.import_project(req.path)
        return {"project_id": pid, "source": source}
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/projects/{pid}/analyze")
def analyze(pid: str, req: AnalyzeRequest):
    try:
        plan = service.analyze(pid, req.strategy)
        return {"plan": plan, "metrics": service.planner.metrics(plan)}
    except KeyError as exc:
        raise HTTPException(404, "Project not found") from exc


@app.get("/projects/{pid}/plan")
def plan(pid: str):
    try:
        return service.store.plans[pid]
    except KeyError as exc:
        raise HTTPException(404, "Plan not found") from exc


@app.patch("/projects/{pid}/plan")
def override(pid: str, req: OverrideRequest):
    try:
        return service.override(pid, req.node_id, classification=req.classification, target_type=req.target_type, model_profile=req.model_profile, requires_approval=req.requires_approval)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.post("/projects/{pid}/approve")
def approve(pid: str, decision: ApprovalDecision):
    try:
        return service.approve(pid, decision)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post("/projects/{pid}/compile")
def compile_project(pid: str, req: CompileRequest):
    try:
        output = req.output or str(Path(tempfile.gettempdir()) / f"rpa2apa-{pid}")
        return {"output": service.compile(pid, output, target=req.target)}
    except Exception as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post("/models/select")
def select_model(task: ModelTask):
    try:
        return model_policy.select(task)
    except RuntimeError as exc:
        raise HTTPException(422, str(exc)) from exc
