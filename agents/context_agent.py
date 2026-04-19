"""
Agente de Contexto — lê e indexa documentos PDF (balancetes, atas, contratos).
Extrai dados estruturados e alimenta a memória compartilhada.
"""

import json
from pathlib import Path
from loguru import logger

from agents.base_agent import BaseAgent
from providers.gemini_provider import GeminiProvider


class ContextAgent(BaseAgent):
    AGENT_NAME = "context_agent"
    SKILL_FOLDER = "financial"

    def analisar(self, dados: dict) -> dict:
        """
        Processa um documento PDF e extrai informações estruturadas.

        Args:
            dados: {
                "pdf_path": caminho do PDF,
                "tipo": "balancete" | "ata" | "contrato"
            }
        """
        pdf_path = dados.get("pdf_path")
        tipo = dados.get("tipo", "balancete")

        if not pdf_path:
            raise ValueError("Campo 'pdf_path' é obrigatório")

        logger.info(f"Processando {tipo}: {pdf_path}")

        # Tenta usar o método nativo do Gemini para PDFs
        if isinstance(self.llm, GeminiProvider):
            return self._processar_com_gemini(pdf_path, tipo)

        # Fallback: extrai texto e envia para o LLM
        return self._processar_com_texto(pdf_path, tipo)

    def _processar_com_gemini(self, pdf_path: str, tipo: str) -> dict:
        """Usa o Gemini para ler o PDF diretamente (sem extrair texto)."""
        prompts = {
            "balancete": (
                "Analise este balancete condominial e extraia:\n"
                "1. Período de referência\n"
                "2. Receitas totais (taxa condominial, fundo reserva, outros)\n"
                "3. Despesas totais por categoria\n"
                "4. Saldo do período\n"
                "5. Inadimplência (se mencionada)\n"
                "6. Pagamentos a fornecedores (nome, valor, descrição)\n"
                "7. Qualquer item que pareça irregular ou fora do padrão\n\n"
                "Retorne os dados em formato JSON estruturado."
            ),
            "ata": (
                "Analise esta ata de assembleia condominial e extraia:\n"
                "1. Data da assembleia\n"
                "2. Tipo (ordinária/extraordinária)\n"
                "3. Quórum presente\n"
                "4. Deliberações e aprovações\n"
                "5. Valores aprovados\n"
                "6. Contratos mencionados\n"
                "7. Próximas ações definidas\n\n"
                "Retorne os dados em formato JSON estruturado."
            ),
            "contrato": (
                "Analise este contrato de prestação de serviços condominial e extraia:\n"
                "1. Fornecedor (nome, CNPJ/CPF)\n"
                "2. Objeto do contrato\n"
                "3. Valor total e forma de pagamento\n"
                "4. Vigência (início e fim)\n"
                "5. Cláusulas de reajuste\n"
                "6. Penalidades e multas\n"
                "7. Condições de rescisão\n\n"
                "Retorne os dados em formato JSON estruturado."
            ),
        }

        question = prompts.get(tipo, prompts["balancete"])

        response = self.llm.complete_with_pdf(
            system_prompt=self.system_prompt,
            pdf_path=pdf_path,
            question=question
        )

        # Tenta parsear JSON da resposta
        dados_extraidos = self._extrair_json(response.content)

        # Registra na memória conforme o tipo
        self._registrar_na_memoria(tipo, dados_extraidos)

        return self._formatar_resultado(
            achados=[{
                "tipo": f"extracao_{tipo}",
                "descricao": f"Dados extraídos de {tipo}: {Path(pdf_path).name}",
                "severidade": "info"
            }],
            dados_extras={
                "tipo_documento": tipo,
                "arquivo": str(pdf_path),
                "dados_extraidos": dados_extraidos,
                "texto_bruto": response.content
            }
        )

    def _processar_com_texto(self, pdf_path: str, tipo: str) -> dict:
        """Extrai texto do PDF e envia para o LLM genérico."""
        texto = self.tools.extrair_texto_pdf(pdf_path)
        tabelas = self.tools.extrair_tabelas_pdf(pdf_path)

        context = f"## Texto do documento\n{texto}"
        if tabelas:
            context += f"\n\n## Tabelas encontradas\n{json.dumps(tabelas, ensure_ascii=False)}"

        prompts = {
            "balancete": "Analise este balancete e extraia todos os dados financeiros em JSON.",
            "ata": "Analise esta ata e extraia deliberações e valores aprovados em JSON.",
            "contrato": "Analise este contrato e extraia termos e valores em JSON.",
        }

        response = self.ask(
            question=prompts.get(tipo, prompts["balancete"]),
            context=context
        )

        dados_extraidos = self._extrair_json(response.content)
        self._registrar_na_memoria(tipo, dados_extraidos)

        return self._formatar_resultado(
            achados=[{
                "tipo": f"extracao_{tipo}",
                "descricao": f"Dados extraídos de {tipo}: {Path(pdf_path).name}",
                "severidade": "info"
            }],
            dados_extras={
                "tipo_documento": tipo,
                "arquivo": str(pdf_path),
                "dados_extraidos": dados_extraidos,
                "texto_bruto": response.content
            }
        )

    def _extrair_json(self, texto: str) -> dict:
        """Tenta extrair JSON de uma resposta em texto."""
        # Tenta parsear diretamente
        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            pass

        # Tenta encontrar bloco JSON na resposta
        inicio = texto.find("{")
        fim = texto.rfind("}") + 1
        if inicio != -1 and fim > inicio:
            try:
                return json.loads(texto[inicio:fim])
            except json.JSONDecodeError:
                pass

        # Tenta encontrar array JSON
        inicio = texto.find("[")
        fim = texto.rfind("]") + 1
        if inicio != -1 and fim > inicio:
            try:
                return {"dados": json.loads(texto[inicio:fim])}
            except json.JSONDecodeError:
                pass

        logger.warning("Não foi possível extrair JSON da resposta do LLM")
        return {"texto_raw": texto}

    def _registrar_na_memoria(self, tipo: str, dados: dict):
        """Registra dados extraídos na memória do condomínio."""
        if tipo == "contrato":
            self.memory.add_contrato(dados)
        elif tipo == "ata":
            self.memory.add_ata(dados)
