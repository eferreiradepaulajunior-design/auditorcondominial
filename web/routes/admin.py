"""
Rotas do painel administrativo.
Gerencia chaves de API, configuração de agentes e condomínios.
"""

import json
import shutil
import re
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates

from web.database import (
    get_all_settings, set_setting, get_setting
)
from web.agent_profiles import AGENT_PROFILES

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

CONDOMINIOS_PATH = Path(__file__).resolve().parent.parent.parent / "condominios"

# Tipos de documentos aceitos
ALLOWED_EXTENSIONS = {
    ".pdf", ".xlsx", ".xls", ".csv", ".xml", ".doc", ".docx",
    ".jpg", ".jpeg", ".png", ".txt", ".json", ".odt", ".ods",
}

# Categorias de documentos
DOC_CATEGORIES = {
    "balancetes": "📊 Balancetes e Prestações de Contas",
    "contratos": "📝 Contratos",
    "atas": "📋 Atas de Assembleias",
    "notas_fiscais": "🧾 Notas Fiscais",
    "extratos": "🏦 Extratos Bancários",
    "boletos": "💰 Boletos e Comprovantes",
    "orcamentos": "📑 Orçamentos",
    "correspondencias": "✉️ Correspondências e Notificações",
    "outros": "📁 Outros Documentos",
}


def _require_auth(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse("/login", status_code=302)
    return None


# ── Dashboard ────────────────────────────────────────────────────

@router.get("")
async def admin_dashboard(request: Request):
    redirect = _require_auth(request)
    if redirect:
        return redirect

    settings = get_all_settings()

    # Montar dados de chaves (mascarar)
    api_keys = {
        "GEMINI_API_KEY": _mask_key(settings.get("GEMINI_API_KEY", "")),
        "OPENAI_API_KEY": _mask_key(settings.get("OPENAI_API_KEY", "")),
        "GROQ_API_KEY": _mask_key(settings.get("GROQ_API_KEY", "")),
        "ANTHROPIC_API_KEY": _mask_key(settings.get("ANTHROPIC_API_KEY", "")),
    }

    # Montar config de agentes
    agents_config = {}
    for agent_id, profile in AGENT_PROFILES.items():
        agents_config[agent_id] = {
            "name": profile["name"],
            "role": profile["role"],
            "avatar": profile["avatar"],
            "provider": settings.get(f"agent_{agent_id}_provider", "gemini"),
            "model": settings.get(f"agent_{agent_id}_model", "gemini-2.5-flash-preview-05-20"),
        }

    return templates.TemplateResponse(request, "admin/dashboard.html", {
        "user": request.state.user,
        "api_keys": api_keys,
        "agents_config": agents_config,
        "condominios": _get_condominios_list(),
        "active_tab": request.query_params.get("tab", "keys"),
    })


# ── Salvar Chaves de API ─────────────────────────────────────────

@router.post("/keys")
async def save_api_keys(
    request: Request,
    gemini_key: str = Form(""),
    openai_key: str = Form(""),
    groq_key: str = Form(""),
    anthropic_key: str = Form(""),
):
    redirect = _require_auth(request)
    if redirect:
        return redirect

    # Só salva se o campo não está vazio e não é a máscara
    if gemini_key and not gemini_key.startswith("****"):
        set_setting("GEMINI_API_KEY", gemini_key)
    if openai_key and not openai_key.startswith("****"):
        set_setting("OPENAI_API_KEY", openai_key)
    if groq_key and not groq_key.startswith("****"):
        set_setting("GROQ_API_KEY", groq_key)
    if anthropic_key and not anthropic_key.startswith("****"):
        set_setting("ANTHROPIC_API_KEY", anthropic_key)

    return RedirectResponse("/admin?tab=keys&saved=1", status_code=302)


# ── Salvar Config de Agentes ─────────────────────────────────────

@router.post("/agents")
async def save_agents_config(request: Request):
    redirect = _require_auth(request)
    if redirect:
        return redirect

    form = await request.form()

    for agent_id in AGENT_PROFILES:
        provider = form.get(f"{agent_id}_provider", "")
        model = form.get(f"{agent_id}_model", "")
        if provider:
            set_setting(f"agent_{agent_id}_provider", provider)
        if model:
            set_setting(f"agent_{agent_id}_model", model)

    return RedirectResponse("/admin?tab=agents&saved=1", status_code=302)


# ── API para listar condominios ──────────────────────────────────

@router.get("/api/condominios")
async def list_condominios(request: Request):
    redirect = _require_auth(request)
    if redirect:
        return redirect

    return _get_condominios_list()


def _get_condominios_list() -> list:
    condominios = []
    if CONDOMINIOS_PATH.exists():
        for d in sorted(CONDOMINIOS_PATH.iterdir()):
            if d.is_dir():
                config_file = d / "config.json"
                doc_count = _count_documents(d / "documentos")
                if config_file.exists():
                    config = json.loads(config_file.read_text(encoding="utf-8"))
                    condominios.append({
                        "id": d.name,
                        "nome": config.get("nome", d.name),
                        "cnpj": config.get("cnpj", ""),
                        "endereco": config.get("endereco", ""),
                        "unidades": config.get("unidades", "N/A"),
                        "sindico_atual": config.get("sindico_atual", ""),
                        "administradora": config.get("administradora", ""),
                        "doc_count": doc_count,
                    })
                else:
                    condominios.append({
                        "id": d.name, "nome": d.name, "cnpj": "",
                        "endereco": "", "unidades": "N/A",
                        "sindico_atual": "", "administradora": "",
                        "doc_count": doc_count,
                    })
    return condominios


def _count_documents(docs_path: Path) -> int:
    if not docs_path.exists():
        return 0
    count = 0
    for f in docs_path.rglob("*"):
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS:
            count += 1
    return count


# ── Criar novo condomínio ────────────────────────────────────────

@router.post("/condominios/novo")
async def create_condominio(
    request: Request,
    nome: str = Form(...),
    cnpj: str = Form(""),
    endereco: str = Form(""),
    unidades: int = Form(0),
    sindico: str = Form(""),
    administradora: str = Form(""),
):
    redirect = _require_auth(request)
    if redirect:
        return redirect

    # Gerar ID a partir do nome (slug)
    slug = re.sub(r'[^a-z0-9]+', '_', nome.lower().strip())
    slug = slug.strip('_')
    if not slug:
        slug = "condominio"

    cond_path = CONDOMINIOS_PATH / slug
    if cond_path.exists():
        # Adicionar sufixo numérico
        i = 2
        while (CONDOMINIOS_PATH / f"{slug}_{i}").exists():
            i += 1
        slug = f"{slug}_{i}"
        cond_path = CONDOMINIOS_PATH / slug

    # Criar estrutura de diretórios
    cond_path.mkdir(parents=True, exist_ok=True)
    (cond_path / "documentos").mkdir(exist_ok=True)
    (cond_path / "memoria").mkdir(exist_ok=True)
    (cond_path / "relatorios").mkdir(exist_ok=True)

    for cat in DOC_CATEGORIES:
        (cond_path / "documentos" / cat).mkdir(exist_ok=True)

    # Criar config.json
    config = {
        "nome": nome,
        "cnpj": cnpj,
        "endereco": endereco,
        "unidades": unidades,
        "sindico_atual": sindico,
        "administradora": administradora,
        "criado_em": datetime.now().isoformat(),
        "limites_aprovacao": {
            "pix_sem_contrato_alerta": 500.00,
            "exige_3_orcamentos": 1500.00,
            "exige_aprovacao_assembleia": 6000.00,
        },
        "agentes": {
            "context_agent":     {"provider": "gemini", "model": "gemini-2.5-flash-preview-05-20"},
            "financial_agent":   {"provider": "gemini", "model": "gemini-2.5-flash-preview-05-20"},
            "contracts_agent":   {"provider": "gemini", "model": "gemini-2.5-flash-preview-05-20"},
            "maintenance_agent": {"provider": "gemini", "model": "gemini-2.5-flash-preview-05-20"},
            "investment_agent":  {"provider": "gemini", "model": "gemini-2.5-flash-preview-05-20"},
            "compliance_agent":  {"provider": "gemini", "model": "gemini-2.5-flash-preview-05-20"},
        },
    }
    (cond_path / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    return RedirectResponse(f"/admin?tab=condominios&saved=1", status_code=302)


# ── Detalhes de um condomínio ────────────────────────────────────

@router.get("/condominios/{cond_id}")
async def condominio_detail(cond_id: str, request: Request):
    redirect = _require_auth(request)
    if redirect:
        return redirect

    cond_path = CONDOMINIOS_PATH / cond_id
    if not cond_path.exists():
        return RedirectResponse("/admin?tab=condominios", status_code=302)

    config_file = cond_path / "config.json"
    config = {}
    if config_file.exists():
        config = json.loads(config_file.read_text(encoding="utf-8"))

    # Listar documentos por categoria
    docs_by_category = {}
    docs_path = cond_path / "documentos"
    for cat_id, cat_name in DOC_CATEGORIES.items():
        cat_path = docs_path / cat_id
        files = []
        if cat_path.exists():
            for f in sorted(cat_path.iterdir()):
                if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS:
                    stat = f.stat()
                    files.append({
                        "name": f.name,
                        "size": _format_size(stat.st_size),
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
                        "ext": f.suffix.lower(),
                        "category": cat_id,
                    })
        docs_by_category[cat_id] = {"label": cat_name, "files": files}

    # Arquivos soltos em /documentos (sem subpasta)
    loose_files = []
    if docs_path.exists():
        for f in sorted(docs_path.iterdir()):
            if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS:
                stat = f.stat()
                loose_files.append({
                    "name": f.name,
                    "size": _format_size(stat.st_size),
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
                    "ext": f.suffix.lower(),
                    "category": "_root",
                })
    if loose_files:
        docs_by_category["_root"] = {"label": "📄 Documentos (raiz)", "files": loose_files}

    total_docs = sum(len(cat["files"]) for cat in docs_by_category.values())

    return templates.TemplateResponse(request, "admin/condominio_detail.html", {
        "user": request.state.user,
        "cond_id": cond_id,
        "config": config,
        "docs_by_category": docs_by_category,
        "doc_categories": DOC_CATEGORIES,
        "total_docs": total_docs,
    })


# ── Upload de documentos ─────────────────────────────────────────

@router.post("/condominios/{cond_id}/upload")
async def upload_documents(
    cond_id: str,
    request: Request,
    category: str = Form("outros"),
    files: list[UploadFile] = File(...),
):
    redirect = _require_auth(request)
    if redirect:
        return redirect

    cond_path = CONDOMINIOS_PATH / cond_id
    if not cond_path.exists():
        return JSONResponse({"error": "Condomínio não encontrado"}, status_code=404)

    if category not in DOC_CATEGORIES:
        category = "outros"

    target_dir = cond_path / "documentos" / category
    target_dir.mkdir(parents=True, exist_ok=True)

    uploaded = []
    errors = []
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append(f"{file.filename}: tipo não permitido ({ext})")
            continue

        # Sanitizar nome do arquivo
        safe_name = re.sub(r'[^\w\-.]', '_', file.filename)
        dest = target_dir / safe_name

        # Se já existe, adicionar sufixo
        if dest.exists():
            stem = dest.stem
            i = 2
            while (target_dir / f"{stem}_{i}{ext}").exists():
                i += 1
            dest = target_dir / f"{stem}_{i}{ext}"

        content = await file.read()
        dest.write_bytes(content)
        uploaded.append(safe_name)

    return JSONResponse({
        "uploaded": uploaded,
        "errors": errors,
        "count": len(uploaded),
    })


# ── Excluir documento ────────────────────────────────────────────

@router.post("/condominios/{cond_id}/delete-doc")
async def delete_document(
    cond_id: str,
    request: Request,
    category: str = Form(...),
    filename: str = Form(...),
):
    redirect = _require_auth(request)
    if redirect:
        return redirect

    cond_path = CONDOMINIOS_PATH / cond_id
    if not cond_path.exists():
        return JSONResponse({"error": "Condomínio não encontrado"}, status_code=404)

    # Prevenir path traversal
    safe_category = Path(category).name
    safe_filename = Path(filename).name

    if safe_category == "_root":
        file_path = cond_path / "documentos" / safe_filename
    else:
        file_path = cond_path / "documentos" / safe_category / safe_filename

    if file_path.exists() and file_path.is_file():
        file_path.unlink()
        return JSONResponse({"ok": True})

    return JSONResponse({"error": "Arquivo não encontrado"}, status_code=404)


# ── Download de documento ────────────────────────────────────────

@router.get("/condominios/{cond_id}/download/{category}/{filename}")
async def download_document(cond_id: str, category: str, filename: str, request: Request):
    redirect = _require_auth(request)
    if redirect:
        return redirect

    # Prevenir path traversal
    safe_category = Path(category).name
    safe_filename = Path(filename).name

    cond_path = CONDOMINIOS_PATH / cond_id
    if safe_category == "_root":
        file_path = cond_path / "documentos" / safe_filename
    else:
        file_path = cond_path / "documentos" / safe_category / safe_filename

    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path, filename=safe_filename)

    return JSONResponse({"error": "Arquivo não encontrado"}, status_code=404)


# ── Editar config do condomínio ──────────────────────────────────

@router.post("/condominios/{cond_id}/editar")
async def edit_condominio(
    cond_id: str,
    request: Request,
    nome: str = Form(...),
    cnpj: str = Form(""),
    endereco: str = Form(""),
    unidades: int = Form(0),
    sindico: str = Form(""),
    administradora: str = Form(""),
):
    redirect = _require_auth(request)
    if redirect:
        return redirect

    cond_path = CONDOMINIOS_PATH / cond_id
    config_file = cond_path / "config.json"
    if not cond_path.exists():
        return RedirectResponse("/admin?tab=condominios", status_code=302)

    config = {}
    if config_file.exists():
        config = json.loads(config_file.read_text(encoding="utf-8"))

    config.update({
        "nome": nome,
        "cnpj": cnpj,
        "endereco": endereco,
        "unidades": unidades,
        "sindico_atual": sindico,
        "administradora": administradora,
        "atualizado_em": datetime.now().isoformat(),
    })

    config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    return RedirectResponse(f"/admin/condominios/{cond_id}?saved=1", status_code=302)


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _mask_key(key: str) -> str:
    """Mascara uma chave de API para exibição."""
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]
