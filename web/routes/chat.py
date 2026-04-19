"""
Rotas de chat e WebSocket.
Interface de comunicação com os agentes via chat em tempo real.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from loguru import logger

from web.database import (
    get_or_create_conversation, get_conversation_messages, save_message
)
from web.agent_profiles import get_agents_for_sidebar, get_profile
from web.auth import validate_session_token
from web.chat_handler import process_chat_message

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


# ── Página do Chat ───────────────────────────────────────────────

@router.get("/chat")
async def chat_page(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse("/login", status_code=302)

    agents = get_agents_for_sidebar()

    return templates.TemplateResponse(request, "chat/index.html", {
        "user": user,
        "agents": agents,
    })


# ── API: Histórico de conversa ───────────────────────────────────

@router.get("/api/chat/history/{agent_id}")
async def get_chat_history(agent_id: str, request: Request):
    user = request.state.user
    if not user:
        return JSONResponse({"error": "Não autorizado"}, status_code=401)

    conv_id = get_or_create_conversation(user["id"], agent_id)
    messages = get_conversation_messages(conv_id)
    profile = get_profile(agent_id)

    return {
        "conversation_id": conv_id,
        "agent": {
            "name": profile["name"],
            "avatar": profile["avatar"],
            "role": profile["role"],
        },
        "messages": messages,
    }


# ── WebSocket: Chat em tempo real ────────────────────────────────

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    # Autenticar via cookie
    session_token = websocket.cookies.get("session")
    if not session_token:
        await websocket.send_json({"type": "error", "message": "Sessão expirada. Faça login novamente."})
        await websocket.close()
        return

    session_data = validate_session_token(session_token)
    if not session_data:
        await websocket.send_json({"type": "error", "message": "Sessão inválida."})
        await websocket.close()
        return

    user_id = session_data["user_id"]
    logger.info(f"WebSocket conectado: user_id={user_id}")

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "message":
                agent_id = data.get("agent_id", "gestor")
                message = data.get("content", "").strip()
                condominio = data.get("condominio", "parque_colibri")

                if not message:
                    continue

                # Indicador de "digitando"
                await websocket.send_json({
                    "type": "typing",
                    "agent_id": agent_id,
                })

                # Processar mensagem
                result = await process_chat_message(
                    user_id=user_id,
                    agent_id=agent_id,
                    message=message,
                    condominio=condominio,
                )

                # Enviar resposta
                await websocket.send_json({
                    "type": "message",
                    "agent_id": result["agent_id"],
                    "agent_name": result["agent_name"],
                    "avatar": result["avatar"],
                    "content": result["content"],
                    "conversation_id": result["conversation_id"],
                    "timestamp": datetime.now().strftime("%H:%M"),
                })

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket desconectado: user_id={user_id}")
    except Exception as e:
        logger.error(f"Erro WebSocket: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


# ── Upload de arquivos ───────────────────────────────────────────

@router.post("/api/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    condominio: str = Form("parque_colibri"),
):
    user = request.state.user
    if not user:
        return JSONResponse({"error": "Não autorizado"}, status_code=401)

    # Validar tipo de arquivo
    allowed_extensions = {".pdf", ".csv", ".xlsx", ".xls", ".txt", ".json"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        return JSONResponse(
            {"error": f"Tipo de arquivo não permitido: {file_ext}"},
            status_code=400
        )

    # Limitar tamanho (50MB)
    max_size = 50 * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        return JSONResponse({"error": "Arquivo muito grande (máximo 50MB)"}, status_code=400)

    # Salvar arquivo
    upload_dir = Path(__file__).resolve().parent.parent.parent / "condominios" / condominio / "documentos" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Sanitizar nome do arquivo
    safe_name = "".join(c for c in file.filename if c.isalnum() or c in "._- ")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_name = f"{timestamp}_{safe_name}"
    file_path = upload_dir / final_name

    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"Arquivo salvo: {file_path}")
    return {"filename": final_name, "path": str(file_path), "size": len(content)}
