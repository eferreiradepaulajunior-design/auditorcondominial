"""
Entrypoint para Vercel Serverless Functions.
Vercel espera encontrar uma aplicação ASGI em api/app.py
"""

import sys
from pathlib import Path

# Adicionar raiz do projeto ao path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Importar a aplicação FastAPI
from web.app import app

# Vercel requisita a exportação como 'app'
__all__ = ["app"]
