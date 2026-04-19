"""
Sistema de Auditoria Condominial com Equipe de Agentes de IA
Ponto de entrada principal.
"""

import sys
from pathlib import Path
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import LOG_LEVEL
from core.orchestrator import Orchestrator
from core.meta_agent import MetaAgent

# Configuração de logging
logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL, format="{time:HH:mm:ss} | {level:<7} | {message}")
logger.add("logs/auditoria_{time:YYYYMMDD}.log", rotation="1 day", level="DEBUG")

console = Console()


def auditar_balancete(condominio: str, pdf_path: str):
    """Executa auditoria completa de um balancete."""
    console.print(Panel(
        f"[bold]Auditoria Condominial[/bold]\n"
        f"Condomínio: {condominio}\n"
        f"Documento: {pdf_path}",
        title="Sistema de Auditoria com IA",
        border_style="blue"
    ))

    orq = Orchestrator(condominio=condominio)
    resultado = orq.processar_documento(path=pdf_path, tipo="balancete")

    # Exibe resumo
    console.print()
    console.print(Panel("[bold red]Alertas Críticos[/bold red]", border_style="red"))
    for alerta in resultado.alertas_criticos:
        console.print(f"  🔴 {alerta}")

    if not resultado.alertas_criticos:
        console.print("  Nenhum alerta crítico encontrado.")

    console.print()
    console.print(Panel("[bold yellow]Pontos de Atenção[/bold yellow]", border_style="yellow"))
    for alerta in resultado.alertas_atencao:
        console.print(f"  🟡 {alerta}")

    if not resultado.alertas_atencao:
        console.print("  Nenhum ponto de atenção encontrado.")

    console.print()
    console.print(Panel("[bold green]Recomendações[/bold green]", border_style="green"))
    for rec in resultado.recomendacoes:
        console.print(f"  ✅ {rec}")

    console.print()
    console.print(f"[dim]Relatório salvo em: outputs/relatorios/[/dim]")

    return resultado


def criar_agente(condominio: str, necessidade: str):
    """Cria um novo agente via Meta-Agente."""
    console.print(Panel(
        f"[bold]Criação de Novo Agente[/bold]\n"
        f"Necessidade: {necessidade[:100]}...",
        title="Meta-Agente",
        border_style="magenta"
    ))

    meta = MetaAgent(condominio=condominio)
    resultado = meta.create_agent(necessidade=necessidade)

    if resultado.get("status") == "sucesso":
        console.print(f"\n✅ Agente [bold]{resultado['agent_name']}[/bold] criado com sucesso!")
        console.print(f"   Classe: {resultado.get('class_name', 'N/A')}")
        console.print(f"   Provider: {resultado.get('provider', 'N/A')} / {resultado.get('model', 'N/A')}")
        console.print(f"   Arquivos: {resultado.get('arquivos_criados', [])}")
    else:
        console.print(f"\n❌ Erro ao criar agente: {resultado.get('erro', 'Desconhecido')}")

    return resultado


def main():
    """Ponto de entrada CLI."""
    if len(sys.argv) < 3:
        console.print(Panel(
            "[bold]Uso:[/bold]\n\n"
            "  Auditar balancete:\n"
            "    python main.py auditar <condominio> <caminho_pdf>\n\n"
            "  Criar novo agente:\n"
            "    python main.py criar-agente <condominio> \"<descrição>\"\n\n"
            "[bold]Exemplo:[/bold]\n"
            "    python main.py auditar parque_colibri condominios/parque_colibri/documentos/balancetes/marco_2026.pdf",
            title="Sistema de Auditoria Condominial",
            border_style="blue"
        ))
        return

    comando = sys.argv[1]

    if comando == "auditar":
        condominio = sys.argv[2]
        pdf_path = sys.argv[3] if len(sys.argv) > 3 else ""
        if not pdf_path:
            console.print("[red]Erro: caminho do PDF é obrigatório[/red]")
            return
        auditar_balancete(condominio, pdf_path)

    elif comando == "criar-agente":
        condominio = sys.argv[2]
        necessidade = sys.argv[3] if len(sys.argv) > 3 else ""
        if not necessidade:
            console.print("[red]Erro: descrição da necessidade é obrigatória[/red]")
            return
        criar_agente(condominio, necessidade)

    else:
        console.print(f"[red]Comando desconhecido: {comando}[/red]")
        console.print("Use: auditar, criar-agente")


if __name__ == "__main__":
    main()
