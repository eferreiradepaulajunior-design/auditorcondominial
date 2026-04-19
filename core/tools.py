"""
Ferramentas compartilhadas entre os agentes.
Inclui leitura de PDFs, consultas a APIs externas e utilitários de formatação.
"""

import os
import json
import requests
import pdfplumber
from pathlib import Path
from loguru import logger
from config import RECEITA_FEDERAL_API, VIACEP_API


class Tools:
    """Ferramentas utilitárias disponíveis para todos os agentes."""

    # --- Leitura de PDFs ---

    @staticmethod
    def extrair_texto_pdf(pdf_path: str) -> str:
        """
        Extrai todo o texto de um arquivo PDF usando pdfplumber.
        Ideal para balancetes, atas e contratos.

        Args:
            pdf_path: Caminho do arquivo PDF

        Returns:
            Texto completo extraído do PDF
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

        texto_completo = []
        with pdfplumber.open(path) as pdf:
            for i, pagina in enumerate(pdf.pages):
                texto = pagina.extract_text()
                if texto:
                    texto_completo.append(f"--- Página {i + 1} ---\n{texto}")

        logger.info(f"PDF lido: {path.name} ({len(texto_completo)} páginas com texto)")
        return "\n\n".join(texto_completo)

    @staticmethod
    def extrair_tabelas_pdf(pdf_path: str) -> list[list[list[str]]]:
        """
        Extrai tabelas de um PDF. Retorna lista de tabelas, cada uma como lista de linhas.

        Args:
            pdf_path: Caminho do arquivo PDF

        Returns:
            Lista de tabelas extraídas
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

        todas_tabelas = []
        with pdfplumber.open(path) as pdf:
            for pagina in pdf.pages:
                tabelas = pagina.extract_tables()
                if tabelas:
                    todas_tabelas.extend(tabelas)

        logger.info(f"Tabelas extraídas de {path.name}: {len(todas_tabelas)}")
        return todas_tabelas

    # --- APIs Externas ---

    @staticmethod
    def consultar_cnpj(cnpj: str) -> dict:
        """
        Consulta dados de CNPJ na Receita Federal via API pública.

        Args:
            cnpj: CNPJ no formato numérico (apenas dígitos)

        Returns:
            Dados cadastrais da empresa
        """
        cnpj_limpo = "".join(c for c in cnpj if c.isdigit())
        if len(cnpj_limpo) != 14:
            raise ValueError(f"CNPJ inválido: {cnpj}")

        url = f"{RECEITA_FEDERAL_API}/{cnpj_limpo}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            dados = response.json()
            logger.info(f"CNPJ consultado: {cnpj_limpo} — {dados.get('nome', 'N/A')}")
            return dados
        except requests.RequestException as e:
            logger.error(f"Erro ao consultar CNPJ {cnpj_limpo}: {e}")
            return {"erro": str(e)}

    @staticmethod
    def consultar_cep(cep: str) -> dict:
        """
        Consulta endereço por CEP via ViaCEP.

        Args:
            cep: CEP no formato numérico

        Returns:
            Dados do endereço
        """
        cep_limpo = "".join(c for c in cep if c.isdigit())
        if len(cep_limpo) != 8:
            raise ValueError(f"CEP inválido: {cep}")

        url = f"{VIACEP_API}/{cep_limpo}/json/"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erro ao consultar CEP {cep_limpo}: {e}")
            return {"erro": str(e)}

    # --- Utilitários ---

    @staticmethod
    def carregar_json(filepath: str) -> dict:
        """Carrega e retorna conteúdo de um arquivo JSON."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def salvar_json(filepath: str, data: dict):
        """Salva dados em arquivo JSON com formatação."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def formatar_moeda(valor: float) -> str:
        """Formata valor numérico como moeda brasileira."""
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def listar_documentos(pasta: str, extensao: str = ".pdf") -> list[Path]:
        """Lista todos os documentos de um tipo em uma pasta."""
        path = Path(pasta)
        if not path.exists():
            return []
        return sorted(path.glob(f"*{extensao}"))

    @staticmethod
    def carregar_skill(skill_path: str) -> str:
        """
        Carrega o conteúdo de um SKILL.md para usar como system prompt do agente.

        Args:
            skill_path: Caminho do arquivo SKILL.md

        Returns:
            Conteúdo do arquivo como string
        """
        path = Path(skill_path)
        if not path.exists():
            logger.warning(f"Skill não encontrada: {skill_path}")
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
