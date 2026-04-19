"""
Agente de Contratos — valida pagamentos contra contratos registrados.
Identifica pagamentos sem contrato, cláusulas de reajuste e vencimentos.
"""

import json
from loguru import logger
from agents.base_agent import BaseAgent


class ContractsAgent(BaseAgent):
    AGENT_NAME = "contracts_agent"
    SKILL_FOLDER = "contracts"

    def analisar(self, dados: dict) -> dict:
        """
        Cruza pagamentos do balancete com contratos registrados na memória.

        Args:
            dados: {
                "pagamentos": lista de pagamentos extraídos do balancete,
                "contratos_novos": contratos extraídos recentemente (opcional)
            }
        """
        pagamentos = dados.get("pagamentos", [])
        contratos_novos = dados.get("contratos_novos", [])

        # Contratos da memória + novos
        contratos_memoria = self.memory.contratos
        todos_contratos = contratos_memoria + contratos_novos

        limites = self.condominio_config.get("limites_aprovacao", {})

        context = (
            f"## Pagamentos do balancete\n{json.dumps(pagamentos, ensure_ascii=False, indent=2)}\n\n"
            f"## Contratos registrados\n{json.dumps(todos_contratos, ensure_ascii=False, indent=2)}\n\n"
            f"## Limites de aprovação\n{json.dumps(limites, ensure_ascii=False, indent=2)}\n\n"
            f"## Dados do condomínio\n"
            f"- Nome: {self.condominio_config.get('nome', 'N/A')}\n"
            f"- Administradora: {self.condominio_config.get('administradora', 'N/A')}\n"
        )

        # Decisões de assembleia
        decisoes = self.memory.atas
        if decisoes:
            context += f"\n\n## Decisões de assembleias\n{json.dumps(decisoes[-5:], ensure_ascii=False, indent=2)}"

        question = (
            "Analise os pagamentos do balancete cruzando com os contratos. Para cada pagamento:\n\n"
            "1. **Vinculação**: O pagamento está vinculado a um contrato? Se não, é PIX avulso?\n"
            "2. **Valor**: O valor pago confere com o contrato? Há reajuste não previsto?\n"
            "3. **Parcelas**: As parcelas estão na sequência correta? Há parcela pulada ou duplicada?\n"
            "4. **Aprovação**: Pagamentos acima do limite exigem aprovação em assembleia. Foi aprovado?\n"
            "5. **Vigência**: O contrato ainda está vigente? Foi renovado formalmente?\n"
            "6. **CNPJ/CPF**: O beneficiário do pagamento coincide com o contrato?\n\n"
            "Atenção especial para:\n"
            "- PIX a pessoas físicas sem contrato vinculado\n"
            "- Contratos com pagamento de múltiplas parcelas no mesmo mês\n"
            "- Valores acima do limite sem registro de aprovação em ata\n\n"
            "Retorne em JSON:\n"
            "{\n"
            '  "resumo": "texto",\n'
            '  "achados": [{"tipo": "...", "descricao": "...", "severidade": "...", "fornecedor": "...", "valor": 0.0}],\n'
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
        logger.warning("Não foi possível extrair JSON da análise de contratos")
        return {"resumo": texto[:500], "achados": [], "alertas_criticos": [], "alertas_atencao": [], "recomendacoes": []}
