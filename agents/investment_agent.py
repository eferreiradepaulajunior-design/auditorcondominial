"""
Agente de Investimentos — analisa fundo de reserva, investimentos e ROI.
Avalia empréstimos, financiamentos e retorno de investimentos do condomínio.
"""

import json
from loguru import logger
from agents.base_agent import BaseAgent


class InvestmentAgent(BaseAgent):
    AGENT_NAME = "investment_agent"
    SKILL_FOLDER = "financial"

    def analisar(self, dados: dict) -> dict:
        """
        Analisa investimentos e fundo de reserva do condomínio.

        Args:
            dados: {
                "fundo_reserva": dados do fundo de reserva,
                "investimentos": investimentos ativos,
                "emprestimos": empréstimos/financiamentos em andamento,
                "receitas_extras": receitas além da taxa condominial
            }
        """
        fundo = dados.get("fundo_reserva", {})
        investimentos = dados.get("investimentos", [])
        emprestimos = dados.get("emprestimos", [])
        receitas_extras = dados.get("receitas_extras", [])

        context = (
            f"## Fundo de reserva\n{json.dumps(fundo, ensure_ascii=False, indent=2)}\n\n"
            f"## Investimentos ativos\n{json.dumps(investimentos, ensure_ascii=False, indent=2)}\n\n"
            f"## Empréstimos/Financiamentos\n{json.dumps(emprestimos, ensure_ascii=False, indent=2)}\n\n"
            f"## Receitas extras\n{json.dumps(receitas_extras, ensure_ascii=False, indent=2)}\n\n"
            f"## Dados do condomínio\n"
            f"- Unidades: {self.condominio_config.get('unidades', 'N/A')}\n"
        )

        question = (
            "Analise a situação financeira de investimentos e reservas:\n\n"
            "1. **Fundo de reserva**: O fundo está adequado? O percentual arrecadado é compatível?\n"
            "2. **Investimentos**: Há aplicações financeiras? Rendimento está sendo demonstrado?\n"
            "3. **Empréstimos**: Para cada empréstimo ativo:\n"
            "   - Qual o saldo devedor?\n"
            "   - Taxa de juros é competitiva?\n"
            "   - Existe demonstrativo de retorno sobre o investimento (ROI)?\n"
            "   - Ex: Painéis solares — qual a economia gerada vs parcela paga?\n"
            "4. **Contas inativas**: Existem contas bancárias com saldo parado sem justificativa?\n"
            "5. **Saúde financeira**: O condomínio consegue honrar compromissos sem saldo negativo?\n\n"
            "Retorne em JSON:\n"
            "{\n"
            '  "resumo": "texto",\n'
            '  "achados": [{"tipo": "...", "descricao": "...", "severidade": "...", "valor": 0.0}],\n'
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
        logger.warning("Não foi possível extrair JSON da análise de investimentos")
        return {"resumo": texto[:500], "achados": [], "alertas_criticos": [], "alertas_atencao": [], "recomendacoes": []}
