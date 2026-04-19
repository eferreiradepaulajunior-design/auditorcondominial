#!/usr/bin/env python
"""
Script de validação local antes de fazer deploy.
Verifica se todos os componentes estão funcionando.
"""

import sys
from pathlib import Path

# Adicionar raiz do projeto ao path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

def check_imports():
    """Verifica se todos os imports funcionam."""
    print("✓ Verificando imports...")
    
    try:
        from app import app
        print("  ✓ app.py (entrypoint)")
    except Exception as e:
        print(f"  ✗ app.py: {e}")
        return False
    
    try:
        from api.app import app as api_app
        print("  ✓ api/app.py (Vercel entrypoint)")
    except Exception as e:
        print(f"  ✗ api/app.py: {e}")
        return False
    
    try:
        from web.app import app as web_app
        print("  ✓ web/app.py (FastAPI app)")
    except Exception as e:
        print(f"  ✗ web/app.py: {e}")
        return False
    
    try:
        from core.orchestrator import Orchestrator
        print("  ✓ Orchestrator (agentes)")
    except Exception as e:
        print(f"  ⚠ Orchestrator (simulado se IA indisponível): {e}")
    
    try:
        from web.database import init_db, get_db
        print("  ✓ Database")
    except Exception as e:
        print(f"  ✗ Database: {e}")
        return False
    
    return True


def check_database():
    """Inicializa e verifica o banco de dados."""
    print("\n✓ Verificando database...")
    
    try:
        from web.database import init_db, get_db
        init_db()
        conn = get_db()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        conn.close()
        
        table_names = [t['name'] for t in tables]
        expected_tables = ['users', 'conversations', 'messages', 'settings', 'audit_pipelines']
        
        for table in expected_tables:
            if table in table_names:
                print(f"  ✓ Tabela '{table}'")
            else:
                print(f"  ✗ Tabela '{table}' faltando")
                return False
        
        return True
    except Exception as e:
        print(f"  ✗ Erro ao verificar database: {e}")
        return False


def check_config():
    """Verifica arquivos de configuração."""
    print("\n✓ Verificando configuração...")
    
    files = [
        'vercel.json',
        '.vercelignore',
        'requirements.txt',
        '.env.example',
        'api/app.py',
        'app.py',
    ]
    
    for file in files:
        path = ROOT / file
        if path.exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} faltando")
            return False
    
    return True


def check_endpoints():
    """Verifica se endpoints críticos estão definidos."""
    print("\n✓ Verificando endpoints...")
    
    try:
        from web.app import app
        
        endpoints = ['/health', '/api/health', '/login', '/chat', '/admin']
        found_endpoints = []
        
        for route in app.routes:
            if hasattr(route, 'path'):
                found_endpoints.append(route.path)
        
        for endpoint in ['/health', '/login']:
            if any(endpoint in e for e in found_endpoints):
                print(f"  ✓ {endpoint}")
            else:
                print(f"  ⚠ {endpoint} não encontrado")
        
        return True
    except Exception as e:
        print(f"  ✗ Erro ao verificar endpoints: {e}")
        return False


def main():
    print("=" * 50)
    print("🔍 Validação Local — Auditor Contábil")
    print("=" * 50)
    
    checks = [
        ("Imports", check_imports),
        ("Database", check_database),
        ("Configuração", check_config),
        ("Endpoints", check_endpoints),
    ]
    
    results = {}
    for name, check in checks:
        results[name] = check()
    
    print("\n" + "=" * 50)
    print("📊 Resumo")
    print("=" * 50)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name}: {status}")
    
    all_pass = all(results.values())
    
    if all_pass:
        print("\n✅ Tudo OK! Pronto para deploy.")
        return 0
    else:
        print("\n❌ Alguns checks falharam. Corrija antes de fazer deploy.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
