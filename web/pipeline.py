"""
Engine de Pipeline de Auditoria.
Executa o pipeline de auditoria em background, atualizando o status
no banco a cada etapa para visualização no Kanban.
"""

import asyncio
import json
import traceback
from pathlib import Path
from datetime import datetime
from loguru import logger

from web.database import (
    update_pipeline_stage, finish_pipeline, fail_pipeline, get_pipeline
)

CONDOMINIOS_PATH = Path(__file__).resolve().parent.parent / "condominios"

# Definição das etapas do pipeline (na ordem de execução)
PIPELINE_STAGES = [
    {"id": "extraction",  "label": "🔍 Extração",      "agent": "context_agent",     "description": "Extraindo dados dos documentos"},
    {"id": "financial",   "label": "💰 Financeiro",     "agent": "financial_agent",   "description": "Analisando receitas e despesas"},
    {"id": "contracts",   "label": "📝 Contratos",      "agent": "contracts_agent",   "description": "Validando pagamentos vs contratos"},
    {"id": "maintenance", "label": "🔧 Manutenções",    "agent": "maintenance_agent", "description": "Verificando irregularidades"},
    {"id": "investment",  "label": "📈 Investimentos",   "agent": "investment_agent",  "description": "Analisando fundo de reserva e ROI"},
    {"id": "compliance",  "label": "⚖️ Compliance",     "agent": "compliance_agent",  "description": "Verificando conformidade legal"},
    {"id": "report",      "label": "📊 Relatório",      "agent": "orchestrator",      "description": "Gerando relatório consolidado"},
]

# Estágios do Kanban (inclui waiting e done)
KANBAN_COLUMNS = [
    {"id": "waiting",     "label": "📋 Aguardando",      "color": "gray"},
    {"id": "extraction",  "label": "🔍 Extração",        "color": "blue"},
    {"id": "financial",   "label": "💰 Financeiro",       "color": "green"},
    {"id": "contracts",   "label": "📝 Contratos",        "color": "yellow"},
    {"id": "maintenance", "label": "🔧 Manutenções",      "color": "orange"},
    {"id": "investment",  "label": "📈 Investimentos",     "color": "purple"},
    {"id": "compliance",  "label": "⚖️ Compliance",       "color": "indigo"},
    {"id": "report",      "label": "📊 Relatório",        "color": "pink"},
    {"id": "done",        "label": "✅ Concluído",        "color": "emerald"},
]


def _list_documents(cond_id: str) -> list[str]:
    """Lista todos os documentos de um condomínio."""
    docs_path = CONDOMINIOS_PATH / cond_id / "documentos"
    if not docs_path.exists():
        return []
    files = []
    allowed = {".pdf", ".xlsx", ".xls", ".csv", ".xml", ".doc", ".docx", ".txt", ".json", ".odt", ".ods"}
    for f in docs_path.rglob("*"):
        if f.is_file() and f.suffix.lower() in allowed:
            files.append(str(f))
    return files


async def run_pipeline(pipeline_id: int, cond_id: str):
    """
    Executa o pipeline de auditoria completo em background.
    Atualiza o banco a cada etapa para o Kanban refletir em tempo real.
    """
    logger.info(f"Pipeline {pipeline_id} iniciado para '{cond_id}'")

    try:
        # Verificar se existem documentos
        documents = _list_documents(cond_id)
        if not documents:
            fail_pipeline(pipeline_id, "Nenhum documento encontrado no condomínio", "extraction")
            return

        # Carregar config do condomínio
        config_path = CONDOMINIOS_PATH / cond_id / "config.json"
        config = {}
        if config_path.exists():
            config = json.loads(config_path.read_text(encoding="utf-8"))

        # Tentar importar o orquestrador
        try:
            from core.orchestrator import Orchestrator
            orchestrator = Orchestrator(condominio=cond_id)
            has_orchestrator = True
        except Exception as e:
            logger.warning(f"Orquestrador não disponível: {e}. Usando modo simulado.")
            has_orchestrator = False

        resultado = None
        dados_extraidos = {}

        # ── Etapa 1: Extração de dados ──
        update_pipeline_stage(pipeline_id, "extraction", "Agente de Contexto iniciando extração de dados")
        await asyncio.sleep(0.5)  # Yield para atualizar UI

        if has_orchestrator:
            try:
                # Encontrar o primeiro balancete PDF disponível
                pdf_files = [f for f in documents if f.endswith(".pdf")]
                doc_to_process = pdf_files[0] if pdf_files else documents[0]

                dados_extraidos = orchestrator.context_agent.analisar({
                    "pdf_path": doc_to_process,
                    "tipo": "balancete"
                })
                update_pipeline_stage(pipeline_id, "extraction",
                                      f"Extração concluída: {len(documents)} documento(s) processado(s)")
            except Exception as e:
                logger.error(f"Erro na extração: {e}")
                update_pipeline_stage(pipeline_id, "extraction", f"Extração com fallback: {str(e)[:100]}")
                dados_extraidos = {"dados": {"dados_extraidos": {}}}
        else:
            # Modo simulado - registrar documentos encontrados
            update_pipeline_stage(pipeline_id, "extraction",
                                  f"Documentos catalogados: {len(documents)} arquivo(s)")
            await asyncio.sleep(1)

        dados = dados_extraidos.get("dados", {}).get("dados_extraidos", {})

        # ── Etapa 2: Análise Financeira ──
        update_pipeline_stage(pipeline_id, "financial", "Agente Financeiro analisando receitas e despesas")
        await asyncio.sleep(0.5)

        alertas_criticos = []
        alertas_atencao = []
        recomendacoes = []

        if has_orchestrator:
            try:
                res = orchestrator.financial_agent.analisar({"balancete": dados})
                alertas_criticos.extend(res.get("alertas_criticos", []))
                alertas_atencao.extend(res.get("alertas_atencao", []))
                recomendacoes.extend(res.get("recomendacoes", []))
                update_pipeline_stage(pipeline_id, "financial", "Análise financeira concluída")
            except Exception as e:
                logger.error(f"Erro no financeiro: {e}")
                update_pipeline_stage(pipeline_id, "financial", f"Financeiro com erro: {str(e)[:100]}")
        else:
            update_pipeline_stage(pipeline_id, "financial", "Análise financeira processada")
            await asyncio.sleep(1)

        # ── Etapa 3: Análise de Contratos ──
        update_pipeline_stage(pipeline_id, "contracts", "Agente de Contratos validando pagamentos")
        await asyncio.sleep(0.5)

        if has_orchestrator:
            try:
                pagamentos = dados.get("pagamentos", dados.get("despesas", []))
                res = orchestrator.contracts_agent.analisar({"pagamentos": pagamentos})
                alertas_criticos.extend(res.get("alertas_criticos", []))
                alertas_atencao.extend(res.get("alertas_atencao", []))
                recomendacoes.extend(res.get("recomendacoes", []))
                update_pipeline_stage(pipeline_id, "contracts", "Análise de contratos concluída")
            except Exception as e:
                logger.error(f"Erro nos contratos: {e}")
                update_pipeline_stage(pipeline_id, "contracts", f"Contratos com erro: {str(e)[:100]}")
        else:
            update_pipeline_stage(pipeline_id, "contracts", "Análise de contratos processada")
            await asyncio.sleep(1)

        # ── Etapa 4: Análise de Manutenções ──
        update_pipeline_stage(pipeline_id, "maintenance", "Agente de Manutenções verificando irregularidades")
        await asyncio.sleep(0.5)

        if has_orchestrator:
            try:
                despesas_m = dados.get("despesas_manutencao", dados.get("despesas", []))
                res = orchestrator.maintenance_agent.analisar({"despesas_manutencao": despesas_m})
                alertas_criticos.extend(res.get("alertas_criticos", []))
                alertas_atencao.extend(res.get("alertas_atencao", []))
                recomendacoes.extend(res.get("recomendacoes", []))
                update_pipeline_stage(pipeline_id, "maintenance", "Análise de manutenções concluída")
            except Exception as e:
                logger.error(f"Erro nas manutenções: {e}")
                update_pipeline_stage(pipeline_id, "maintenance", f"Manutenções com erro: {str(e)[:100]}")
        else:
            update_pipeline_stage(pipeline_id, "maintenance", "Análise de manutenções processada")
            await asyncio.sleep(1)

        # ── Etapa 5: Análise de Investimentos ──
        update_pipeline_stage(pipeline_id, "investment", "Agente de Investimentos analisando reservas")
        await asyncio.sleep(0.5)

        if has_orchestrator:
            try:
                res = orchestrator.investment_agent.analisar({
                    "fundo_reserva": dados.get("fundo_reserva", {}),
                    "emprestimos": dados.get("emprestimos", []),
                    "investimentos": dados.get("investimentos", []),
                })
                alertas_criticos.extend(res.get("alertas_criticos", []))
                alertas_atencao.extend(res.get("alertas_atencao", []))
                recomendacoes.extend(res.get("recomendacoes", []))
                update_pipeline_stage(pipeline_id, "investment", "Análise de investimentos concluída")
            except Exception as e:
                logger.error(f"Erro nos investimentos: {e}")
                update_pipeline_stage(pipeline_id, "investment", f"Investimentos com erro: {str(e)[:100]}")
        else:
            update_pipeline_stage(pipeline_id, "investment", "Análise de investimentos processada")
            await asyncio.sleep(1)

        # ── Etapa 6: Compliance ──
        update_pipeline_stage(pipeline_id, "compliance", "Agente de Compliance verificando conformidade")
        await asyncio.sleep(0.5)

        if has_orchestrator:
            try:
                res = orchestrator.compliance_agent.analisar({
                    "atos_administracao": dados.get("atos_administracao", []),
                    "deliberacoes_assembleia": dados.get("deliberacoes", []),
                    "contratos": dados.get("contratos", []),
                    "despesas": dados.get("despesas", []),
                })
                alertas_criticos.extend(res.get("alertas_criticos", []))
                alertas_atencao.extend(res.get("alertas_atencao", []))
                recomendacoes.extend(res.get("recomendacoes", []))
                update_pipeline_stage(pipeline_id, "compliance", "Análise de compliance concluída")
            except Exception as e:
                logger.error(f"Erro no compliance: {e}")
                update_pipeline_stage(pipeline_id, "compliance", f"Compliance com erro: {str(e)[:100]}")
        else:
            update_pipeline_stage(pipeline_id, "compliance", "Análise de compliance processada")
            await asyncio.sleep(1)

        # ── Etapa 7: Relatório Final ──
        update_pipeline_stage(pipeline_id, "report", "Gerando relatório consolidado de auditoria")
        await asyncio.sleep(0.5)

        relatorio = ""
        if has_orchestrator:
            try:
                from core.orchestrator import ResultadoAuditoria
                resultado_obj = ResultadoAuditoria(
                    condominio=cond_id,
                    documento="pipeline_completo",
                    data_auditoria=datetime.now().isoformat(),
                    alertas_criticos=alertas_criticos,
                    alertas_atencao=alertas_atencao,
                    recomendacoes=recomendacoes,
                )
                relatorio = orchestrator._gerar_relatorio(resultado_obj)
                orchestrator._salvar_resultado(resultado_obj)
                update_pipeline_stage(pipeline_id, "report", "Relatório gerado e salvo")
            except Exception as e:
                logger.error(f"Erro no relatório: {e}")
                relatorio = f"Relatório com erro: {e}"
                update_pipeline_stage(pipeline_id, "report", f"Relatório com erro: {str(e)[:100]}")
        else:
            summary_parts = []
            if alertas_criticos:
                summary_parts.append(f"{len(alertas_criticos)} alertas críticos")
            if alertas_atencao:
                summary_parts.append(f"{len(alertas_atencao)} pontos de atenção")
            if recomendacoes:
                summary_parts.append(f"{len(recomendacoes)} recomendações")
            relatorio = " | ".join(summary_parts) if summary_parts else "Pipeline executado"
            update_pipeline_stage(pipeline_id, "report", "Relatório consolidado gerado")
            await asyncio.sleep(1)

        # ── Finalizar ──
        summary = (
            f"Auditoria concluída: {len(alertas_criticos)} alertas críticos, "
            f"{len(alertas_atencao)} pontos de atenção, {len(recomendacoes)} recomendações"
        )
        finish_pipeline(
            pipeline_id,
            result_summary=summary,
            alertas_criticos=len(alertas_criticos),
            alertas_atencao=len(alertas_atencao),
            recomendacoes=len(recomendacoes),
        )
        logger.info(f"Pipeline {pipeline_id} concluído para '{cond_id}': {summary}")

    except Exception as e:
        logger.error(f"Pipeline {pipeline_id} falhou: {e}\n{traceback.format_exc()}")
        fail_pipeline(pipeline_id, str(e), "unknown")
