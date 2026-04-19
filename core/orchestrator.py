"""
Agente Orquestrador — coordena todos os agentes especializados.
Recebe um documento, distribui análises e consolida o relatório final.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent
from agents.context_agent import ContextAgent
from agents.financial_agent import FinancialAgent
from agents.contracts_agent import ContractsAgent
from agents.maintenance_agent import MaintenanceAgent
from agents.investment_agent import InvestmentAgent
from agents.compliance_agent import ComplianceAgent
from core.tools import Tools
from config import OUTPUTS_PATH


@dataclass
class ResultadoAuditoria:
    """Resultado consolidado da auditoria."""
    condominio: str
    documento: str
    data_auditoria: str
    relatorio: str = ""
    alertas_criticos: list = field(default_factory=list)
    alertas_atencao: list = field(default_factory=list)
    recomendacoes: list = field(default_factory=list)
    resultados_agentes: dict = field(default_factory=dict)
    tokens_total: dict = field(default_factory=dict)


class Orchestrator(BaseAgent):
    """
    Coordena a execução de todos os agentes de auditoria.

    Fluxo:
    1. ContextAgent lê o documento e extrai dados estruturados
    2. Agentes especializados analisam os dados em paralelo (conceitual)
    3. Orquestrador consolida resultados e gera relatório final
    """

    AGENT_NAME = "orchestrator"
    SKILL_FOLDER = ""

    def __init__(self, condominio: str, agent_config: dict = None):
        super().__init__(condominio, agent_config)

        # Inicializa agentes especializados
        self.context_agent = ContextAgent(condominio)
        self.financial_agent = FinancialAgent(condominio)
        self.contracts_agent = ContractsAgent(condominio)
        self.maintenance_agent = MaintenanceAgent(condominio)
        self.investment_agent = InvestmentAgent(condominio)
        self.compliance_agent = ComplianceAgent(condominio)

        logger.info(f"Orquestrador inicializado com 6 agentes para '{condominio}'")

    def processar_documento(self, path: str, tipo: str = "balancete") -> ResultadoAuditoria:
        """
        Processa um documento completo de auditoria.

        Args:
            path: Caminho do arquivo PDF
            tipo: Tipo do documento ("balancete", "ata", "contrato")

        Returns:
            ResultadoAuditoria com todos os achados consolidados
        """
        logger.info(f"Iniciando auditoria: {path} (tipo: {tipo})")
        resultado = ResultadoAuditoria(
            condominio=self.condominio,
            documento=path,
            data_auditoria=datetime.now().isoformat()
        )

        # Etapa 1: Extrair dados do documento
        logger.info("Etapa 1/4: Extração de dados")
        dados_extraidos = self.context_agent.analisar({
            "pdf_path": path,
            "tipo": tipo
        })
        resultado.resultados_agentes["context"] = dados_extraidos

        dados = dados_extraidos.get("dados", {}).get("dados_extraidos", {})

        # Etapa 2: Análises especializadas
        logger.info("Etapa 2/4: Análises especializadas")

        # Financeiro
        try:
            res_financeiro = self.financial_agent.analisar({
                "balancete": dados,
            })
            resultado.resultados_agentes["financial"] = res_financeiro
            resultado.alertas_criticos.extend(res_financeiro.get("alertas_criticos", []))
            resultado.alertas_atencao.extend(res_financeiro.get("alertas_atencao", []))
            resultado.recomendacoes.extend(res_financeiro.get("recomendacoes", []))
        except Exception as e:
            logger.error(f"Erro no agente financeiro: {e}")

        # Contratos
        try:
            pagamentos = dados.get("pagamentos", dados.get("despesas", []))
            res_contratos = self.contracts_agent.analisar({
                "pagamentos": pagamentos,
            })
            resultado.resultados_agentes["contracts"] = res_contratos
            resultado.alertas_criticos.extend(res_contratos.get("alertas_criticos", []))
            resultado.alertas_atencao.extend(res_contratos.get("alertas_atencao", []))
            resultado.recomendacoes.extend(res_contratos.get("recomendacoes", []))
        except Exception as e:
            logger.error(f"Erro no agente de contratos: {e}")

        # Manutenções
        try:
            despesas_manutencao = dados.get("despesas_manutencao", dados.get("despesas", []))
            res_manutencao = self.maintenance_agent.analisar({
                "despesas_manutencao": despesas_manutencao,
            })
            resultado.resultados_agentes["maintenance"] = res_manutencao
            resultado.alertas_criticos.extend(res_manutencao.get("alertas_criticos", []))
            resultado.alertas_atencao.extend(res_manutencao.get("alertas_atencao", []))
            resultado.recomendacoes.extend(res_manutencao.get("recomendacoes", []))
        except Exception as e:
            logger.error(f"Erro no agente de manutenção: {e}")

        # Investimentos
        try:
            res_investimento = self.investment_agent.analisar({
                "fundo_reserva": dados.get("fundo_reserva", {}),
                "emprestimos": dados.get("emprestimos", []),
                "investimentos": dados.get("investimentos", []),
            })
            resultado.resultados_agentes["investment"] = res_investimento
            resultado.alertas_criticos.extend(res_investimento.get("alertas_criticos", []))
            resultado.alertas_atencao.extend(res_investimento.get("alertas_atencao", []))
            resultado.recomendacoes.extend(res_investimento.get("recomendacoes", []))
        except Exception as e:
            logger.error(f"Erro no agente de investimentos: {e}")

        # Compliance
        try:
            res_compliance = self.compliance_agent.analisar({
                "atos_administracao": dados.get("atos_administracao", []),
                "deliberacoes_assembleia": dados.get("deliberacoes", []),
                "contratos": dados.get("contratos", []),
                "despesas": dados.get("despesas", []),
            })
            resultado.resultados_agentes["compliance"] = res_compliance
            resultado.alertas_criticos.extend(res_compliance.get("alertas_criticos", []))
            resultado.alertas_atencao.extend(res_compliance.get("alertas_atencao", []))
            resultado.recomendacoes.extend(res_compliance.get("recomendacoes", []))
        except Exception as e:
            logger.error(f"Erro no agente de compliance: {e}")

        # Etapa 3: Gerar relatório consolidado
        logger.info("Etapa 3/4: Gerando relatório consolidado")
        resultado.relatorio = self._gerar_relatorio(resultado)

        # Etapa 4: Salvar resultados
        logger.info("Etapa 4/4: Salvando resultados")
        self._salvar_resultado(resultado)

        logger.info(
            f"Auditoria concluída | "
            f"Alertas críticos: {len(resultado.alertas_criticos)} | "
            f"Alertas atenção: {len(resultado.alertas_atencao)} | "
            f"Recomendações: {len(resultado.recomendacoes)}"
        )

        return resultado

    def _gerar_relatorio(self, resultado: ResultadoAuditoria) -> str:
        """Usa o LLM do orquestrador para consolidar o relatório final."""
        resumos = {}
        for nome, res in resultado.resultados_agentes.items():
            resumos[nome] = res.get("dados", {}).get("resumo", "Sem resumo")

        context = (
            f"## Resumos dos agentes\n{json.dumps(resumos, ensure_ascii=False, indent=2)}\n\n"
            f"## Alertas críticos\n{json.dumps(resultado.alertas_criticos, ensure_ascii=False, indent=2)}\n\n"
            f"## Alertas de atenção\n{json.dumps(resultado.alertas_atencao, ensure_ascii=False, indent=2)}\n\n"
            f"## Recomendações\n{json.dumps(resultado.recomendacoes, ensure_ascii=False, indent=2)}\n\n"
            f"## Dados do condomínio\n"
            f"- Nome: {self.condominio_config.get('nome', 'N/A')}\n"
            f"- Unidades: {self.condominio_config.get('unidades', 'N/A')}\n"
            f"- Síndico: {self.condominio_config.get('sindico_atual', 'N/A')}\n"
            f"- Administradora: {self.condominio_config.get('administradora', 'N/A')}\n"
        )

        question = (
            "Gere um relatório de auditoria condominial profissional em Markdown.\n\n"
            "Estrutura obrigatória:\n"
            "1. **Cabeçalho**: Nome do condomínio, período, data da auditoria\n"
            "2. **Resumo executivo**: Visão geral da situação (2-3 parágrafos)\n"
            "3. **Alertas críticos**: Lista de irregularidades graves\n"
            "4. **Pontos de atenção**: Itens que precisam de acompanhamento\n"
            "5. **Análise financeira**: Resumo de receitas, despesas e saldo\n"
            "6. **Contratos e fornecedores**: Situação dos contratos\n"
            "7. **Manutenções**: Serviços realizados e pendências\n"
            "8. **Investimentos e reservas**: Situação do fundo e empréstimos\n"
            "9. **Conformidade legal**: Pontos de compliance\n"
            "10. **Recomendações**: Ações prioritárias\n"
            "11. **Conclusão**\n\n"
            "Linguagem: formal, objetiva, com valores em R$ e referências legais."
        )

        response = self.ask(question=question, context=context)
        return response.content

    def _salvar_resultado(self, resultado: ResultadoAuditoria):
        """Salva o relatório e os dados brutos."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_base = Path(resultado.documento).stem

        # Salva relatório em Markdown
        relatorio_path = Path(OUTPUTS_PATH) / "relatorios" / f"{nome_base}_{timestamp}.md"
        relatorio_path.parent.mkdir(parents=True, exist_ok=True)
        relatorio_path.write_text(resultado.relatorio, encoding="utf-8")
        logger.info(f"Relatório salvo: {relatorio_path}")

        # Salva alertas em JSON
        alertas_path = Path(OUTPUTS_PATH) / "alertas" / f"{nome_base}_{timestamp}.json"
        alertas_path.parent.mkdir(parents=True, exist_ok=True)
        Tools.salvar_json(str(alertas_path), {
            "condominio": resultado.condominio,
            "documento": resultado.documento,
            "data_auditoria": resultado.data_auditoria,
            "alertas_criticos": resultado.alertas_criticos,
            "alertas_atencao": resultado.alertas_atencao,
            "recomendacoes": resultado.recomendacoes,
        })
        logger.info(f"Alertas salvos: {alertas_path}")

        # Salva cópia no condomínio
        cond_relatorio = self.condominio_path / "relatorios" / f"{nome_base}_{timestamp}.md"
        cond_relatorio.parent.mkdir(parents=True, exist_ok=True)
        cond_relatorio.write_text(resultado.relatorio, encoding="utf-8")

    def analisar(self, dados: dict) -> dict:
        """Implementação do método abstrato — redireciona para processar_documento."""
        return self.processar_documento(
            path=dados.get("pdf_path", ""),
            tipo=dados.get("tipo", "balancete")
        )
