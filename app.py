"""
Entrypoint FastAPI para o Auditor Contábil.
Importa a aplicação de web.app para facilitar descoberta automática.
"""

from web.app import app

__all__ = ["app"]
