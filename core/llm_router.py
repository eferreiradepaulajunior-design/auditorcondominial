import os
from importlib import import_module
from providers.base_provider import BaseProvider


class LLMRouter:
    """
    Roteador central de provedores de IA.

    Recebe o nome do provedor e modelo, e retorna a instância correta.
    Permite trocar o provedor de qualquer agente sem alterar o código do agente.

    Uso:
        router = LLMRouter()
        llm = router.get("gemini", "gemini-3-flash-preview")
        resposta = llm.complete(system_prompt, user_message)
    """

    # Lazy loading: (module_path, class_name, env_key)
    PROVIDERS = {
        "gemini":    ("providers.gemini_provider",    "GeminiProvider",    "GEMINI_API_KEY"),
        "openai":    ("providers.openai_provider",    "OpenAIProvider",    "OPENAI_API_KEY"),
        "groq":      ("providers.groq_provider",      "GroqProvider",      "GROQ_API_KEY"),
        "anthropic": ("providers.anthropic_provider",  "AnthropicProvider", "ANTHROPIC_API_KEY"),
    }

    def get(self, provider: str, model: str) -> BaseProvider:
        """
        Retorna a instância do provedor configurado.

        Args:
            provider: Nome do provedor ("gemini", "openai", "groq", "anthropic")
            model: Nome do modelo a usar

        Returns:
            Instância do provedor pronta para uso

        Raises:
            ValueError: Se o provedor não for suportado
            EnvironmentError: Se a chave de API não estiver configurada
        """
        if provider not in self.PROVIDERS:
            provedores = list(self.PROVIDERS.keys())
            raise ValueError(f"Provedor '{provider}' não suportado. Use: {provedores}")

        module_path, class_name, env_key = self.PROVIDERS[provider]
        api_key = os.getenv(env_key)

        if not api_key:
            raise EnvironmentError(
                f"Chave de API não encontrada para '{provider}'. "
                f"Configure a variável de ambiente {env_key} no arquivo .env"
            )

        # Import lazy do provider
        module = import_module(module_path)
        ProviderClass = getattr(module, class_name)
        return ProviderClass(api_key=api_key, model=model)

    def get_from_config(self, agent_config: dict) -> BaseProvider:
        """
        Atalho: recebe o dicionário de config do agente e retorna o provedor.

        Args:
            agent_config: Ex: {"provider": "gemini", "model": "gemini-3-flash-preview"}
        """
        return self.get(agent_config["provider"], agent_config["model"])
