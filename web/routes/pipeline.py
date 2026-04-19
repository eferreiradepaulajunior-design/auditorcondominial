"""
Rotas do Pipeline de Auditoria e Kanban.
Gerencia início, status e visualização do pipeline.
"""

import asyncio
import json
from pathlib import Path
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from web.database import (
    create_pipeline, get_pipeline, get_pipeline_by_condominio,
    get_all_pipelines
)
from web.pipeline import run_pipeline, KANBAN_COLUMNS, PIPELINE_STAGES

router = APIRouter(prefix="/admin/pipeline")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

CONDOMINIOS_PATH = Path(__file__).resolve().parent.parent.parent / "condominios"


def _require_auth(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse("/login", status_code=302)
    return None


# ── Kanban Board ─────────────────────────────────────────────────

@router.get("")
async def kanban_board(request: Request):
    redirect = _require_auth(request)
    if redirect:
        return redirect

    pipelines = get_all_pipelines()

    # Parsear JSON strings nos pipelines
    for p in pipelines:
        p["stages_done"] = json.loads(p.get("stages_done") or "[]")
        p["stages_errors"] = json.loads(p.get("stages_errors") or "{}")
        p["log"] = json.loads(p.get("log") or "[]")

    return templates.TemplateResponse(request, "admin/kanban.html", {
        "user": request.state.user,
        "pipelines": pipelines,
        "kanban_columns": KANBAN_COLUMNS,
        "pipeline_stages": PIPELINE_STAGES,
    })


# ── Iniciar Pipeline ─────────────────────────────────────────────

@router.post("/start/{cond_id}")
async def start_pipeline(cond_id: str, request: Request):
    redirect = _require_auth(request)
    if redirect:
        return redirect

    cond_path = CONDOMINIOS_PATH / cond_id
    if not cond_path.exists():
        return JSONResponse({"error": "Condomínio não encontrado"}, status_code=404)

    # Verificar se já existe pipeline em execução para este condomínio
    existing = get_pipeline_by_condominio(cond_id)
    if existing and existing["status"] == "running":
        return JSONResponse({
            "error": "Já existe uma auditoria em andamento para este condomínio",
            "pipeline_id": existing["id"]
        }, status_code=409)

    # Carregar nome do condomínio
    config_path = cond_path / "config.json"
    nome = cond_id
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        nome = config.get("nome", cond_id)

    # Criar pipeline no banco
    user = request.state.user
    triggered_by = user["display_name"] if user else "sistema"
    pipeline_id = create_pipeline(cond_id, nome, triggered_by)

    # Executar pipeline em background
    asyncio.create_task(run_pipeline(pipeline_id, cond_id))

    # Redirecionar para o Kanban
    referer = request.headers.get("referer", "")
    if "condominios" in referer and cond_id in referer:
        return RedirectResponse(f"/admin/condominios/{cond_id}?audit_started=1", status_code=302)

    return RedirectResponse(f"/admin/pipeline?started={cond_id}", status_code=302)


# ── API: Status de um pipeline ───────────────────────────────────

@router.get("/api/status/{pipeline_id}")
async def pipeline_status(pipeline_id: int, request: Request):
    redirect = _require_auth(request)
    if redirect:
        return redirect

    p = get_pipeline(pipeline_id)
    if not p:
        return JSONResponse({"error": "Pipeline não encontrado"}, status_code=404)

    p["stages_done"] = json.loads(p.get("stages_done") or "[]")
    p["stages_errors"] = json.loads(p.get("stages_errors") or "{}")
    p["log"] = json.loads(p.get("log") or "[]")

    return JSONResponse(p)


# ── API: Todos os pipelines (para polling do Kanban) ─────────────

@router.get("/api/all")
async def all_pipelines(request: Request):
    redirect = _require_auth(request)
    if redirect:
        return redirect

    pipelines = get_all_pipelines()
    for p in pipelines:
        p["stages_done"] = json.loads(p.get("stages_done") or "[]")
        p["stages_errors"] = json.loads(p.get("stages_errors") or "{}")
        p["log"] = json.loads(p.get("log") or "[]")

    return JSONResponse(pipelines)


# ── API: Status de condomínio específico ─────────────────────────

@router.get("/api/condominio/{cond_id}")
async def condominio_pipeline_status(cond_id: str, request: Request):
    redirect = _require_auth(request)
    if redirect:
        return redirect

    p = get_pipeline_by_condominio(cond_id)
    if not p:
        return JSONResponse({"status": "none"})

    p["stages_done"] = json.loads(p.get("stages_done") or "[]")
    p["stages_errors"] = json.loads(p.get("stages_errors") or "{}")
    p["log"] = json.loads(p.get("log") or "[]")

    return JSONResponse(p)
