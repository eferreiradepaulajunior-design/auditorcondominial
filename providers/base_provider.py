from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Resposta padronizada independente do provedor."""
    content: str
    provider: str
    model: str
    tokens_input: int
    tokens_output: int


class BaseProvider(ABC):
    """
    Classe base para todos os provedores de IA.
    Todo provedor deve implementar o método `complete`.
    """

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> LLMResponse:
        """
        Envia uma mensagem para o modelo e retorna a resposta padronizada.

        Args:
            system_prompt: Instruções do sistema (conteúdo do SKILL.md do agente)
            user_message: Mensagem do usuário (dados a analisar)
            temperature: Criatividade da resposta (0.1 para análises precisas)
            max_tokens: Limite de tokens na resposta

        Returns:
            LLMResponse com o conteúdo e metadados da resposta
        """
        pass
