"""
Agente Financeiro — analisa receitas, despesas, saldos e detecta anomalias.
Identifica inconsistências nos balancetes condominiais.
"""

import json
from loguru import logger
from agents.base_agent import BaseAgent


class FinancialAgent(BaseAgent):
    AGENT_NAME = "financial_agent"
    SKILL_FOLDER = "financial"

    def analisar(self, dados: dict) -> dict:
        """
        Analisa dados financeiros extraídos de um balancete.

        Args:
            dados: {
                "balancete": dados extraídos pelo ContextAgent,
                "balancetes_anteriores": [dados de meses anteriores] (opcional),
                "limites": limites de aprovação do condomínio (opcional)
            }
        """
        balancete = dados.get("balancete", {})
        anteriores = dados.get("balancetes_anteriores", [])
        limites = dados.get("limites", self.condominio_config.get("limites_aprovacao", {}))

        # Monta contexto com dados financeiros
        context = f"## Balancete atual\n{json.dumps(balancete, ensure_ascii=False, indent=2)}"

        if anteriores:
            context += f"\n\n## Balancetes anteriores\n{json.dumps(anteriores, ensure_ascii=False, indent=2)}"

        context += f"\n\n## Limites de aprovação do condomínio\n{json.dumps(limites, ensure_ascii=False, indent=2)}"

        # Informações do condomínio
        context += f"\n\n## Dados do condomínio\n"
        context += f"- Nome: {self.condominio_config.get('nome', 'N/A')}\n"
        context += f"- Unidades: {self.condominio_config.get('unidades', 'N/A')}\n"
        context += f"- Administradora: {self.condominio_config.get('administradora', 'N/A')}\n"

        # Memória — achados anteriores
        achados_anteriores = self.memory.get_achados_por_agente(self.AGENT_NAME)
        if achados_anteriores:
            context += f"\n\n## Achados anteriores deste agente\n{json.dumps(achados_anteriores[-5:], ensure_ascii=False, indent=2)}"

        question = (
            "Realize uma análise financeira completa do balancete condominial. Identifique:\n\n"
            "1. **Saldo**: O saldo é positivo ou negativo? Comparar com meses anteriores.\n"
            "2. **Receitas**: Taxa condominial está cobrindo as despesas? Inadimplência?\n"
            "3. **Despesas suspeitas**: Pagamentos acima dos limites sem aprovação em assembleia.\n"
            "4. **PIX avulsos**: Pagamentos via PIX a pessoas físicas sem contrato vinculado.\n"
            "5. **Duplicidades**: Pagamentos duplicados ou parcelas pagas no mesmo mês.\n"
            "6. **Variações atípicas**: Despesas que variaram mais de 30% em relação ao mês anterior.\n"
            "7. **Contas inativas**: Contas ou fornecedores que não deveriam mais receber.\n\n"
            "Para cada achado, classifique como:\n"
            "- **critico**: Irregularidade que exige ação imediata\n"
            "- **atencao**: Ponto que merece investigação\n"
            "- **info**: Observação informativa\n\n"
            "Retorne em JSON com a estrutura:\n"
            "{\n"
            '  "resumo": "texto resumo",\n'
            '  "achados": [{"tipo": "...", "descricao": "...", "severidade": "...", "valor": 0.0}],\n'
            '  "alertas_criticos": ["texto do alerta"],\n'
            '  "alertas_atencao": ["texto do alerta"],\n'
            '  "recomendacoes": ["texto da recomendação"]\n'
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

    def _extrair_json(self, texto: str) -> dict:
        """Tenta extrair JSON da resposta do LLM."""
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

        logger.warning("Não foi possível extrair JSON da análise financeira")
        return {
            "resumo": texto[:500],
            "achados": [],
            "alertas_criticos": [],
            "alertas_atencao": [],
            "recomendacoes": []
        }
