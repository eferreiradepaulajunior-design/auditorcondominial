from openai import OpenAI
from providers.base_provider import BaseProvider, LLMResponse


class OpenAIProvider(BaseProvider):
    """
    Adaptador para a API da OpenAI.
    Documentação: https://platform.openai.com/docs

    Modelos disponíveis:
    - gpt-4o: poderoso, suporte a visão e análise de documentos
    - gpt-4o-mini: mais barato, bom para tarefas simples
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        super().__init__(api_key, model)
        self.client = OpenAI(api_key=api_key)

    def complete(self, system_prompt, user_message, temperature=0.1, max_tokens=4096):
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            provider="openai",
            model=self.model,
            tokens_input=response.usage.prompt_tokens,
            tokens_output=response.usage.completion_tokens
        )
