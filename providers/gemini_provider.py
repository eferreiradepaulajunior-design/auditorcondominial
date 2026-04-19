import google.generativeai as genai
from providers.base_provider import BaseProvider, LLMResponse


class GeminiProvider(BaseProvider):
    """
    Adaptador para a API do Google Gemini.
    Documentação: https://ai.google.dev/gemini-api/docs

    Modelos disponíveis:
    - gemini-3-flash-preview: rápido e barato, ideal para extração de dados
    - gemini-3.1-pro-preview: poderoso, ideal para análises complexas
    """

    def __init__(self, api_key: str, model: str = "gemini-3-flash-preview"):
        super().__init__(api_key, model)
        genai.configure(api_key=api_key)

    def complete(self, system_prompt, user_message, temperature=0.1, max_tokens=4096):
        model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=system_prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )
        response = model.generate_content(user_message)

        return LLMResponse(
            content=response.text,
            provider="gemini",
            model=self.model,
            tokens_input=response.usage_metadata.prompt_token_count,
            tokens_output=response.usage_metadata.candidates_token_count
        )

    def complete_with_pdf(self, system_prompt, pdf_path, question, temperature=0.1):
        """
        Método especial do Gemini: envia PDF diretamente para o modelo.
        O Gemini suporta leitura nativa de PDFs de até 1000 páginas.
        Ideal para o Agente de Contexto processar balancetes.

        Args:
            pdf_path: Caminho local do arquivo PDF
            question: Pergunta sobre o conteúdo do PDF
        """
        uploaded_file = genai.upload_file(pdf_path)
        model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=system_prompt
        )
        response = model.generate_content([uploaded_file, question])

        return LLMResponse(
            content=response.text,
            provider="gemini",
            model=self.model,
            tokens_input=response.usage_metadata.prompt_token_count,
            tokens_output=response.usage_metadata.candidates_token_count
        )
