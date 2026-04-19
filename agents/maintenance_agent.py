"""
Agente de Manutenções — verifica irregularidades em serviços de manutenção.
Valida orçamentos, identifica sobrepreço e pagamentos sem comprovação.
"""

import json
from loguru import logger
from agents.base_agent import BaseAgent


class MaintenanceAgent(BaseAgent):
    AGENT_NAME = "maintenance_agent"
    SKILL_FOLDER = "maintenance"

    def analisar(self, dados: dict) -> dict:
        """
        Analisa despesas de manutenção do condomínio.

        Args:
            dados: {
                "despesas_manutencao": lista de despesas de manutenção,
                "orcamentos": orçamentos apresentados (opcional),
                "historico_manutencoes": histórico de serviços (opcional)
            }
        """
        despesas = dados.get("despesas_manutencao", [])
        orcamentos = dados.get("orcamentos", [])
        historico = dados.get("historico_manutencoes", [])
        limites = self.condominio_config.get("limites_aprovacao", {})

        context = (
            f"## Despesas de manutenção\n{json.dumps(despesas, ensure_ascii=False, indent=2)}\n\n"
            f"## Orçamentos apresentados\n{json.dumps(orcamentos, ensure_ascii=False, indent=2)}\n\n"
            f"## Histórico de manutenções\n{json.dumps(historico, ensure_ascii=False, indent=2)}\n\n"
            f"## Limites de aprovação\n{json.dumps(limites, ensure_ascii=False, indent=2)}\n\n"
            f"## Regras do condomínio\n"
            f"- Acima de {self.tools.formatar_moeda(limites.get('exige_3_orcamentos', 1500))} exige 3 orçamentos\n"
            f"- Acima de {self.tools.formatar_moeda(limites.get('exige_aprovacao_assembleia', 6000))} exige aprovação em assembleia\n"
            f"- PIX avulso acima de {self.tools.formatar_moeda(limites.get('pix_sem_contrato_alerta', 500))} gera alerta\n"
        )

        question = (
            "Analise as despesas de manutenção do condomínio:\n\n"
            "1. **Orçamentos**: Serviços acima do limite possuem 3 orçamentos? Foram apresentados à administração?\n"
            "2. **Sobrepreço**: Os valores são compatíveis com o mercado para o tipo de serviço?\n"
            "3. **Recorrência**: Há serviços similares sendo pagos repetidamente em curto período?\n"
            "4. **Urgência falsa**: Serviços apresentados como 'emergência' para evitar orçamento?\n"
            "5. **Comprovação**: Há nota fiscal ou recibo para cada pagamento?\n"
            "6. **Segurança**: Problemas de segurança relatados (elétrica, hidráulica, estrutural).\n"
            "   Atenção: fuga de energia, acidentes, riscos a moradores.\n\n"
            "Retorne em JSON:\n"
            "{\n"
            '  "resumo": "texto",\n'
            '  "achados": [{"tipo": "...", "descricao": "...", "severidade": "...", "servico": "...", "valor": 0.0}],\n'
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
        logger.warning("Não foi possível extrair JSON da análise de manutenção")
        return {"resumo": texto[:500], "achados": [], "alertas_criticos": [], "alertas_atencao": [], "recomendacoes": []}
