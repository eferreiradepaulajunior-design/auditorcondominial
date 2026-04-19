"""
Agente de Compliance — verifica conformidade legal com legislação condominial.
Analisa atos da administração contra Lei 4.591/64, Código Civil e normas ABNT.
"""

import json
from pathlib import Path
from loguru import logger
from agents.base_agent import BaseAgent
from config import KNOWLEDGE_PATH


class ComplianceAgent(BaseAgent):
    AGENT_NAME = "compliance_agent"
    SKILL_FOLDER = "compliance"

    def analisar(self, dados: dict) -> dict:
        """
        Verifica conformidade legal das operações do condomínio.

        Args:
            dados: {
                "atos_administracao": atos da administração a verificar,
                "deliberacoes_assembleia": deliberações de assembleia,
                "contratos": contratos em vigor,
                "despesas": despesas do período
            }
        """
        atos = dados.get("atos_administracao", [])
        deliberacoes = dados.get("deliberacoes_assembleia", [])
        contratos = dados.get("contratos", [])
        despesas = dados.get("despesas", [])

        # Carrega base de conhecimento legal
        legislacao = self._carregar_legislacao()

        context = (
            f"## Atos da administração\n{json.dumps(atos, ensure_ascii=False, indent=2)}\n\n"
            f"## Deliberações de assembleia\n{json.dumps(deliberacoes, ensure_ascii=False, indent=2)}\n\n"
            f"## Contratos em vigor\n{json.dumps(contratos, ensure_ascii=False, indent=2)}\n\n"
            f"## Despesas do período\n{json.dumps(despesas, ensure_ascii=False, indent=2)}\n\n"
            f"## Base legal\n{legislacao}\n\n"
            f"## Dados do condomínio\n"
            f"- Nome: {self.condominio_config.get('nome', 'N/A')}\n"
            f"- Síndico: {self.condominio_config.get('sindico_atual', 'N/A')}\n"
            f"- Administradora: {self.condominio_config.get('administradora', 'N/A')}\n"
        )

        question = (
            "Verifique a conformidade legal dos atos da administração condominial:\n\n"
            "1. **Prestação de contas**: A administração está prestando contas conforme Art. 1.348 CC?\n"
            "2. **Aprovação de despesas**: Despesas extraordinárias foram aprovadas em assembleia (Art. 1.341 CC)?\n"
            "3. **Convocação de assembleia**: Assembleias estão sendo convocadas corretamente?\n"
            "4. **Contratações**: Contratos seguem as regras de aprovação do condomínio?\n"
            "5. **Fundo de reserva**: Está sendo constituído e utilizado conforme a convenção?\n"
            "6. **Transparência**: Documentos estão disponíveis aos condôminos?\n"
            "7. **Segurança**: Normas de segurança (NR, ABNT) estão sendo cumpridas?\n"
            "8. **Cobrança**: Política de cobrança de inadimplentes é legal?\n\n"
            "Para cada não conformidade, cite o artigo de lei ou norma violada.\n\n"
            "Retorne em JSON:\n"
            "{\n"
            '  "resumo": "texto",\n'
            '  "achados": [{"tipo": "...", "descricao": "...", "severidade": "...", "base_legal": "..."}],\n'
            '  "alertas_criticos": ["..."],\n'
            '  "alertas_atencao": ["..."],\n'
            '  "recomendacoes": ["..."]\n'
            "}"
        )

        response = self.ask(question=question, context=context)
        resultado_llm = self._extrair_json(response.content)

        return self._formatar_resultado(
            achados=resultado_llm.get("achados", []),
            alertas_criticos=resultado_llm.get("alertas_criticos", []),
            alertas_atencao=resultado_llm.get("alertas_atencao", []),
            recomendacoes=resultado_llm.get("recomendacoes", []),
            dados_extras={"resumo": resultado_llm.get("resumo", "")}
        )

    def _carregar_legislacao(self) -> str:
        """Carrega resumos da legislação do knowledge base."""
        legislacao_path = Path(KNOWLEDGE_PATH) / "legislacao"
        textos = []

        if legislacao_path.exists():
            for arquivo in sorted(legislacao_path.glob("*.md")):
                conteudo = arquivo.read_text(encoding="utf-8")
                textos.append(f"### {arquivo.stem}\n{conteudo}")

        return "\n\n".join(textos) if textos else "Base legal não carregada."

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
        logger.warning("Não foi possível extrair JSON da análise de compliance")
        return {"resumo": texto[:500], "achados": [], "alertas_criticos": [], "alertas_atencao": [], "recomendacoes": []}
