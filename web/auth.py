"""
Autenticação e sessão para o frontend web.
Usa cookies assinados (itsdangerous) para gerenciamento de sessão.
"""

import os
import bcrypt as _bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

SECRET_KEY = os.getenv("SECRET_KEY", "auditor-contabil-secret-change-me-in-production")
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 dias

_serializer = URLSafeTimedSerializer(SECRET_KEY)


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return _bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_session_token(user_id: int) -> str:
    return _serializer.dumps({"user_id": user_id})


def validate_session_token(token: str) -> dict | None:
    try:
        data = _serializer.loads(token, max_age=SESSION_MAX_AGE)
        return data
    except (BadSignature, SignatureExpired):
        return None
