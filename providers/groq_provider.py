from groq import Groq
from providers.base_provider import BaseProvider, LLMResponse


class GroqProvider(BaseProvider):
    """
    Adaptador para a API da Groq.
    Documentação: https://console.groq.com/docs

    Destaque: extremamente rápida (hardware LPU), ideal para tarefas de alto volume.

    Modelos disponíveis:
    - llama-3.3-70b-versatile: poderoso e rápido
    - mixtral-8x7b-32768: contexto longo (32k tokens)
    - llama-3.1-8b-instant: ultra rápido para tarefas simples
    """

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        super().__init__(api_key, model)
        self.client = Groq(api_key=api_key)

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
            provider="groq",
            model=self.model,
            tokens_input=response.usage.prompt_tokens,
            tokens_output=response.usage.completion_tokens
        )
