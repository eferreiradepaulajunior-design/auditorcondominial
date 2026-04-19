"""
Banco de dados SQLite para o frontend web.
Armazena usuários, conversas, mensagens e configurações.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "auditoria.db"


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            role TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            agent_id TEXT NOT NULL,
            title TEXT,
            condominio TEXT DEFAULT 'parque_colibri',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_pipelines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condominio_id TEXT NOT NULL,
            condominio_nome TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'waiting',
            current_stage TEXT NOT NULL DEFAULT 'waiting',
            stages_done TEXT DEFAULT '[]',
            stages_errors TEXT DEFAULT '{}',
            started_at TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP,
            triggered_by TEXT DEFAULT '',
            result_summary TEXT DEFAULT '',
            alertas_criticos INTEGER DEFAULT 0,
            alertas_atencao INTEGER DEFAULT 0,
            recomendacoes INTEGER DEFAULT 0,
            log TEXT DEFAULT '[]'
        );

        CREATE INDEX IF NOT EXISTS idx_pipelines_cond ON audit_pipelines(condominio_id);
        CREATE INDEX IF NOT EXISTS idx_pipelines_status ON audit_pipelines(status);
        CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
        CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
    """)
    conn.commit()
    conn.close()


# ── Helpers de Settings ──────────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
        (key, value, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_all_settings() -> dict:
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}


# ── Helpers de Users ─────────────────────────────────────────────

def get_user_by_username(username: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def create_user(username: str, password_hash: str, display_name: str = "", role: str = "admin"):
    conn = get_db()
    conn.execute(
        "INSERT INTO users (username, password_hash, display_name, role) VALUES (?, ?, ?, ?)",
        (username, password_hash, display_name or username, role)
    )
    conn.commit()
    conn.close()


def user_count() -> int:
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return count


# ── Helpers de Conversations ─────────────────────────────────────

def get_or_create_conversation(user_id: int, agent_id: str, condominio: str = "parque_colibri") -> int:
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM conversations WHERE user_id = ? AND agent_id = ? AND condominio = ? "
        "ORDER BY updated_at DESC LIMIT 1",
        (user_id, agent_id, condominio)
    ).fetchone()

    if row:
        conv_id = row["id"]
    else:
        cursor = conn.execute(
            "INSERT INTO conversations (user_id, agent_id, condominio, title) VALUES (?, ?, ?, ?)",
            (user_id, agent_id, condominio, f"Conversa com {agent_id}")
        )
        conv_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return conv_id


def get_conversation_messages(conversation_id: int, limit: int = 50) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT role, content, created_at FROM messages "
        "WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ?",
        (conversation_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_message(conversation_id: int, role: str, content: str, metadata: dict = None):
    conn = get_db()
    conn.execute(
        "INSERT INTO messages (conversation_id, role, content, metadata) VALUES (?, ?, ?, ?)",
        (conversation_id, role, content, json.dumps(metadata) if metadata else None)
    )
    conn.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (datetime.now().isoformat(), conversation_id)
    )
    conn.commit()
    conn.close()


# ── Helpers de Pipeline ──────────────────────────────────────────

def create_pipeline(condominio_id: str, condominio_nome: str, triggered_by: str = "") -> int:
    conn = get_db()
    now = datetime.now().isoformat()
    cursor = conn.execute(
        "INSERT INTO audit_pipelines "
        "(condominio_id, condominio_nome, status, current_stage, started_at, updated_at, triggered_by, log) "
        "VALUES (?, ?, 'running', 'extraction', ?, ?, ?, ?)",
        (condominio_id, condominio_nome, now, now, triggered_by,
         json.dumps([{"time": now, "msg": "Pipeline iniciado"}]))
    )
    pipeline_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return pipeline_id


def get_pipeline(pipeline_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM audit_pipelines WHERE id = ?", (pipeline_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_pipeline_by_condominio(condominio_id: str):
    """Retorna o pipeline mais recente de um condomínio."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM audit_pipelines WHERE condominio_id = ? ORDER BY id DESC LIMIT 1",
        (condominio_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_pipelines() -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM audit_pipelines ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_pipeline_stage(pipeline_id: int, stage: str, log_msg: str = ""):
    conn = get_db()
    now = datetime.now().isoformat()

    # Buscar dados atuais
    row = conn.execute("SELECT stages_done, log FROM audit_pipelines WHERE id = ?", (pipeline_id,)).fetchone()
    if not row:
        conn.close()
        return

    stages_done = json.loads(row["stages_done"] or "[]")
    log = json.loads(row["log"] or "[]")

    # Marcar stage anterior como done
    current = conn.execute("SELECT current_stage FROM audit_pipelines WHERE id = ?", (pipeline_id,)).fetchone()
    if current and current["current_stage"] not in stages_done:
        stages_done.append(current["current_stage"])

    if log_msg:
        log.append({"time": now, "stage": stage, "msg": log_msg})

    conn.execute(
        "UPDATE audit_pipelines SET current_stage = ?, stages_done = ?, log = ?, updated_at = ? WHERE id = ?",
        (stage, json.dumps(stages_done), json.dumps(log, ensure_ascii=False), now, pipeline_id)
    )
    conn.commit()
    conn.close()


def finish_pipeline(pipeline_id: int, result_summary: str = "",
                    alertas_criticos: int = 0, alertas_atencao: int = 0, recomendacoes: int = 0):
    conn = get_db()
    now = datetime.now().isoformat()

    row = conn.execute("SELECT stages_done, log FROM audit_pipelines WHERE id = ?", (pipeline_id,)).fetchone()
    stages_done = json.loads(row["stages_done"] or "[]") if row else []
    log = json.loads(row["log"] or "[]") if row else []
    log.append({"time": now, "msg": "Pipeline concluído com sucesso"})

    conn.execute(
        "UPDATE audit_pipelines SET status = 'done', current_stage = 'done', "
        "stages_done = ?, finished_at = ?, updated_at = ?, result_summary = ?, "
        "alertas_criticos = ?, alertas_atencao = ?, recomendacoes = ?, log = ? WHERE id = ?",
        (json.dumps(stages_done), now, now, result_summary,
         alertas_criticos, alertas_atencao, recomendacoes,
         json.dumps(log, ensure_ascii=False), pipeline_id)
    )
    conn.commit()
    conn.close()


def fail_pipeline(pipeline_id: int, error_msg: str, stage: str = ""):
    conn = get_db()
    now = datetime.now().isoformat()

    row = conn.execute("SELECT stages_errors, log FROM audit_pipelines WHERE id = ?", (pipeline_id,)).fetchone()
    errors = json.loads(row["stages_errors"] or "{}") if row else {}
    log = json.loads(row["log"] or "[]") if row else []

    if stage:
        errors[stage] = error_msg
    log.append({"time": now, "stage": stage, "msg": f"ERRO: {error_msg}"})

    conn.execute(
        "UPDATE audit_pipelines SET status = 'error', stages_errors = ?, log = ?, updated_at = ? WHERE id = ?",
        (json.dumps(errors, ensure_ascii=False), json.dumps(log, ensure_ascii=False), now, pipeline_id)
    )
    conn.commit()
    conn.close()
