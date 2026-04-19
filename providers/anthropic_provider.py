import anthropic
from providers.base_provider import BaseProvider, LLMResponse


class AnthropicProvider(BaseProvider):
    """
    Adaptador para a API da Anthropic (Claude).
    Documentação: https://docs.anthropic.com

    Modelos disponíveis:
    - claude-opus-4-5: mais poderoso, melhor para raciocínio complexo e compliance
    - claude-sonnet-4-5: equilíbrio entre custo e performance
    - claude-haiku-4-5: mais rápido e barato
    """

    def __init__(self, api_key: str, model: str = "claude-opus-4-5"):
        super().__init__(api_key, model)
        self.client = anthropic.Anthropic(api_key=api_key)

    def complete(self, system_prompt, user_message, temperature=0.1, max_tokens=4096):
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        return LLMResponse(
            content=response.content[0].text,
            provider="anthropic",
            model=self.model,
            tokens_input=response.usage.input_tokens,
            tokens_output=response.usage.output_tokens
        )
