"""
Classe base que todos os agentes herdam.
Define a interface comum e o fluxo de execução padrão.
"""

import json
from pathlib import Path
from loguru import logger

from core.llm_router import LLMRouter
from core.memory import Memory
from core.tools import Tools
from providers.base_provider import BaseProvider, LLMResponse
from config import CONDOMINIOS_PATH, SKILLS_PATH


class BaseAgent:
    """
    Classe base para agentes de auditoria.

    Cada agente:
    - Recebe um condomínio alvo
    - Carrega sua configuração de provider do config.json do condomínio
    - Carrega seu SKILL.md como system prompt
    - Tem acesso à memória compartilhada e às ferramentas
    """

    # Subclasses devem definir estes atributos
    AGENT_NAME: str = "base"
    SKILL_FOLDER: str = ""

    def __init__(self, condominio: str, agent_config: dict = None):
        """
        Args:
            condominio: Slug do condomínio (ex: "parque_colibri")
            agent_config: Override opcional do provider/model.
                          Ex: {"provider": "openai", "model": "gpt-4o"}
        """
        self.condominio = condominio
        self.condominio_path = Path(CONDOMINIOS_PATH) / condominio
        self.tools = Tools()
        self.router = LLMRouter()

        # Carrega config do condomínio
        config_path = self.condominio_path / "config.json"
        if not config_path.exists():
            raise FileNotFoundError(
                f"Config não encontrado: {config_path}. "
                f"Crie o arquivo config.json para o condomínio '{condominio}'"
            )
        self.condominio_config = self.tools.carregar_json(str(config_path))

        # Resolve provider: override > config.json
        if agent_config:
            self._agent_config = agent_config
        else:
            agentes_config = self.condominio_config.get("agentes", {})
            self._agent_config = agentes_config.get(self.AGENT_NAME, {
                "provider": "gemini",
                "model": "gemini-3-flash-preview"
            })

        # Inicializa provider
        self.llm: BaseProvider = self.router.get_from_config(self._agent_config)

        # Inicializa memória do condomínio
        self.memory = Memory(self.condominio_path)

        # Carrega skill (system prompt)
        self.system_prompt = self._load_skill()

        logger.info(
            f"Agente '{self.AGENT_NAME}' inicializado | "
            f"Provider: {self._agent_config['provider']} | "
            f"Model: {self._agent_config['model']} | "
            f"Condomínio: {condominio}"
        )

    def _load_skill(self) -> str:
        """Carrega o SKILL.md do agente como system prompt."""
        if not self.SKILL_FOLDER:
            return ""

        skill_path = Path(SKILLS_PATH) / self.SKILL_FOLDER / "SKILL.md"
        content = self.tools.carregar_skill(str(skill_path))

        if not content:
            logger.warning(
                f"Skill não encontrada para agente '{self.AGENT_NAME}': {skill_path}"
            )

        return content

    def ask(self, question: str, context: str = "") -> LLMResponse:
        """
        Envia uma pergunta ao LLM do agente com o system prompt da skill.

        Args:
            question: Pergunta ou tarefa para o agente
            context: Contexto adicional (dados extraídos, memória, etc.)

        Returns:
            LLMResponse com a resposta do modelo
        """
        user_message = question
        if context:
            user_message = f"## Contexto\n{context}\n\n## Tarefa\n{question}"

        response = self.llm.complete(
            system_prompt=self.system_prompt,
            user_message=user_message
        )

        logger.debug(
            f"[{self.AGENT_NAME}] Tokens: {response.tokens_input} in / "
            f"{response.tokens_output} out"
        )

        return response

    def analisar(self, dados: dict) -> dict:
        """
        Método principal de análise. Subclasses devem sobrescrever.

        Args:
            dados: Dados estruturados para análise

        Returns:
            Resultado da análise com achados e alertas
        """
        raise NotImplementedError(
            f"Agente '{self.AGENT_NAME}' deve implementar o método analisar()"
        )

    def _formatar_resultado(
        self,
        achados: list,
        alertas_criticos: list = None,
        alertas_atencao: list = None,
        recomendacoes: list = None,
        dados_extras: dict = None
    ) -> dict:
        """
        Formata o resultado da análise em estrutura padronizada.
        Registra achados na memória do condomínio.
        """
        resultado = {
            "agente": self.AGENT_NAME,
            "provider": self._agent_config["provider"],
            "model": self._agent_config["model"],
            "condominio": self.condominio,
            "achados": achados,
            "alertas_criticos": alertas_criticos or [],
            "alertas_atencao": alertas_atencao or [],
            "recomendacoes": recomendacoes or [],
        }

        if dados_extras:
            resultado["dados"] = dados_extras

        # Registra achados na memória
        for achado in achados:
            self.memory.add_achado({
                "agente": self.AGENT_NAME,
                "tipo": achado.get("tipo", "geral"),
                "descricao": achado.get("descricao", ""),
                "severidade": achado.get("severidade", "info"),
            })

        return resultado
