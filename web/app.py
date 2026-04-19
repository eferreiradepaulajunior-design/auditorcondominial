"""
Aplicação FastAPI principal.
Serve o frontend web com chat, painel admin e WebSocket.
"""

import sys
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

# Adicionar raiz do projeto ao path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.database import init_db, get_user_by_username, create_user, user_count, get_user_by_id
from web.auth import hash_password, verify_password, create_session_token, validate_session_token
from web.routes.admin import router as admin_router
from web.routes.chat import router as chat_router
from web.routes.pipeline import router as pipeline_router

# ── Logging ──────────────────────────────────────────────────────
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level:<7} | {message}")
logger.add(str(ROOT / "logs" / "web_{time:YYYYMMDD}.log"), rotation="1 day", level="DEBUG")

# ── App ──────────────────────────────────────────────────────────
app = FastAPI(title="Auditor Contábil", docs_url=None, redoc_url=None)

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"

TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ── Middleware de sessão ─────────────────────────────────────────

class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user = None
        session_token = request.cookies.get("session")
        if session_token:
            session_data = validate_session_token(session_token)
            if session_data:
                user = get_user_by_id(session_data["user_id"])
                if user:
                    request.state.user = {
                        "id": user["id"],
                        "username": user["username"],
                        "display_name": user["display_name"],
                        "role": user["role"],
                    }
        response = await call_next(request)
        return response


app.add_middleware(SessionMiddleware)

# ── Rotas ────────────────────────────────────────────────────────
app.include_router(admin_router)
app.include_router(chat_router)
app.include_router(pipeline_router)


# ── Página inicial ───────────────────────────────────────────────

@app.get("/")
async def index(request: Request):
    if request.state.user:
        return RedirectResponse("/chat", status_code=302)
    return RedirectResponse("/login", status_code=302)


# ── Login ────────────────────────────────────────────────────────

@app.get("/login")
async def login_page(request: Request):
    if request.state.user:
        return RedirectResponse("/chat", status_code=302)

    is_setup = user_count() == 0
    return templates.TemplateResponse(request, "login.html", {
        "is_setup": is_setup,
        "error": request.query_params.get("error", ""),
    })


@app.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    display_name: str = Form(""),
):
    is_setup = user_count() == 0

    if is_setup:
        # Primeiro acesso: criar conta admin
        if len(username) < 3 or len(password) < 4:
            return templates.TemplateResponse(request, "login.html", {
                "is_setup": True,
                "error": "Usuário mínimo 3 caracteres, senha mínimo 4.",
            })
        create_user(username, hash_password(password), display_name or username, "admin")
        user = get_user_by_username(username)
    else:
        # Login normal
        user = get_user_by_username(username)
        if not user or not verify_password(password, user["password_hash"]):
            return templates.TemplateResponse(request, "login.html", {
                "is_setup": False,
                "error": "Usuário ou senha incorretos.",
            })

    token = create_session_token(user["id"])
    response = RedirectResponse("/chat", status_code=302)
    response.set_cookie(
        "session", token,
        max_age=60 * 60 * 24 * 7,
        httponly=True,
        samesite="lax",
    )
    return response


# ── Logout ───────────────────────────────────────────────────────

@app.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("session")
    return response


# ── Startup ──────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    init_db()
    (ROOT / "logs").mkdir(exist_ok=True)
    logger.info("🏢 Auditor Contábil Web iniciado")
    logger.info(f"   Acesse: http://localhost:8000")


# ── Para rodar diretamente ───────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.app:app", host="0.0.0.0", port=8000, reload=True)
