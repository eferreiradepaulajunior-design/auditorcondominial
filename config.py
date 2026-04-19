"""
Configurações globais do sistema de auditoria condominial.
Carrega variáveis de ambiente e define constantes do sistema.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Diretório raiz do projeto
BASE_DIR = Path(__file__).resolve().parent

# Caminhos do sistema
CONDOMINIOS_PATH = Path(os.getenv("CONDOMINIOS_PATH", "./condominios"))
OUTPUTS_PATH = Path(os.getenv("OUTPUTS_PATH", "./outputs"))
SKILLS_PATH = Path(os.getenv("SKILLS_PATH", "./skills"))
KNOWLEDGE_PATH = Path(os.getenv("KNOWLEDGE_PATH", "./knowledge"))

# Configurações de LLM
MAX_TOKENS_PER_AGENT = int(os.getenv("MAX_TOKENS_PER_AGENT", 4096))
TEMPERATURA_AGENTES = float(os.getenv("TEMPERATURA_AGENTES", 0.1))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# APIs externas
RECEITA_FEDERAL_API = os.getenv("RECEITA_FEDERAL_API", "https://www.receitaws.com.br/v1/cnpj")
VIACEP_API = os.getenv("VIACEP_API", "https://viacep.com.br/ws")
