"""
Meta-Agente — cria novos agentes e skills dinamicamente.
Capaz de gerar código Python para novos agentes com base em uma descrição.
"""

import json
from pathlib import Path
from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent
from core.tools import Tools
from config import SKILLS_PATH, CONDOMINIOS_PATH


class MetaAgent(BaseAgent):
    AGENT_NAME = "meta_agent"
    SKILL_FOLDER = "meta"

    def analisar(self, dados: dict) -> dict:
        """Cria um novo agente com base na necessidade descrita."""
        return self.create_agent(dados.get("necessidade", ""))

    def create_agent(self, necessidade: str) -> dict:
        """
        Gera um novo agente especializado a partir de uma descrição.

        Args:
            necessidade: Descrição em linguagem natural do que o agente deve fazer.

        Returns:
            Dicionário com caminhos dos arquivos criados e status.
        """
        logger.info(f"Meta-Agente criando novo agente: {necessidade[:80]}...")

        # Pedir ao LLM para gerar o agente
        context = (
            f"## Agentes existentes\n"
            f"- context_agent: lê e indexa documentos PDF\n"
            f"- financial_agent: analisa receitas, despesas e saldos\n"
            f"- contracts_agent: valida pagamentos contra contratos\n"
            f"- maintenance_agent: verifica irregularidades em manutenções\n"
            f"- investment_agent: analisa fundo de reserva e investimentos\n"
            f"- compliance_agent: verifica conformidade legal\n\n"
            f"## Estrutura base de um agente\n"
            f"Todo agente herda de BaseAgent e implementa o método analisar(dados: dict) -> dict.\n"
            f"Usa self.ask(question, context) para consultar o LLM.\n"
            f"Retorna self._formatar_resultado(achados, alertas_criticos, alertas_atencao, recomendacoes).\n"
        )

        question = (
            f"Necessidade do usuário: {necessidade}\n\n"
            f"Gere em JSON:\n"
            f'{{\n'
            f'  "agent_name": "nome_do_agente (snake_case, sem _agent no final)",\n'
            f'  "class_name": "NomeDoAgenteAgent (PascalCase)",\n'
            f'  "skill_folder": "nome da pasta da skill",\n'
            f'  "description": "descrição curta do agente",\n'
            f'  "agent_code": "código Python completo do agente",\n'
            f'  "skill_content": "conteúdo do SKILL.md com instruções detalhadas para o agente",\n'
            f'  "provider": "provedor recomendado (gemini/openai/groq/anthropic)",\n'
            f'  "model": "modelo recomendado"\n'
            f'}}'
        )

        response = self.ask(question=question, context=context)
        spec = self._extrair_json(response.content)

        if "agent_name" not in spec:
            logger.error("Meta-Agente não conseguiu gerar especificação válida")
            return {"erro": "Especificação inválida", "resposta_raw": response.content}

        # Criar arquivos
        arquivos_criados = []

        # 1. Código do agente
        agent_filename = f"{spec['agent_name']}_agent.py"
        agent_path = Path("agents") / agent_filename
        agent_path.write_text(spec.get("agent_code", ""), encoding="utf-8")
        arquivos_criados.append(str(agent_path))
        logger.info(f"Agente criado: {agent_path}")

        # 2. Skill
        skill_folder = spec.get("skill_folder", spec["agent_name"])
        skill_dir = Path(SKILLS_PATH) / skill_folder
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text(spec.get("skill_content", ""), encoding="utf-8")
        arquivos_criados.append(str(skill_path))
        logger.info(f"Skill criada: {skill_path}")

        # 3. Atualizar registry.json
        registry_path = Path(SKILLS_PATH) / "registry.json"
        registry = {}
        if registry_path.exists():
            registry = Tools.carregar_json(str(registry_path))

        if "skills" not in registry:
            registry["skills"] = []

        registry["skills"].append({
            "name": spec["agent_name"],
            "folder": skill_folder,
            "description": spec.get("description", ""),
            "created_at": datetime.now().isoformat(),
            "created_by": "meta_agent"
        })
        Tools.salvar_json(str(registry_path), registry)
        arquivos_criados.append(str(registry_path))

        # 4. Atualizar config.json do condomínio
        config_path = self.condominio_path / "config.json"
        config = Tools.carregar_json(str(config_path))
        agent_key = f"{spec['agent_name']}_agent"
        config["agentes"][agent_key] = {
            "provider": spec.get("provider", "groq"),
            "model": spec.get("model", "llama-3.3-70b-versatile")
        }
        Tools.salvar_json(str(config_path), config)

        logger.info(f"Novo agente '{spec['agent_name']}' criado com sucesso!")

        return {
            "status": "sucesso",
            "agent_name": spec["agent_name"],
            "class_name": spec.get("class_name", ""),
            "description": spec.get("description", ""),
            "arquivos_criados": arquivos_criados,
            "provider": spec.get("provider", ""),
            "model": spec.get("model", ""),
        }

    def _extrair_json(self, texto: str) -> dict:
        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            pass
        inicio = texto.find("{")
        fim = texto.rfind("}") + 1
        if inicio != -1 and fim > inicio:
            try:
                return json.loads(texto[inicio:fim])
            except json.JSONDecodeError:
                pass
        logger.warning("Meta-Agente: não foi possível extrair JSON da resposta")
        return {}
