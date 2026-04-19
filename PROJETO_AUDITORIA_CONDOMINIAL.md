# Sistema de Auditoria Condominial com Equipe de Agentes de IA

## Visão Geral

Este projeto implementa uma equipe de agentes de IA especializados para auditoria automatizada de balancetes condominiais. O sistema suporta múltiplos provedores de IA (Google Gemini, OpenAI, Groq e Anthropic), permitindo escolher qual modelo cada agente usa individualmente.

O sistema é capaz de ler documentos PDF (balancetes, atas, contratos), extrair informações relevantes, cruzar dados entre diferentes fontes e gerar relatórios de auditoria com alertas e recomendações.

Projetado para começar com uso individual e escalar para múltiplos condomínios e auditores, mantendo memória isolada por condomínio e skills ajustáveis por agente.

---

## Provedores de IA Suportados

Cada agente pode ser configurado independentemente para usar qualquer um dos provedores abaixo.

| Provedor | Modelos recomendados | Melhor uso | Documentação |
|---|---|---|---|
| **Google Gemini** | `gemini-3-flash-preview`, `gemini-3.1-pro-preview` | Leitura de PDFs, análise de documentos longos | https://ai.google.dev/gemini-api/docs |
| **OpenAI** | `gpt-4o`, `gpt-4o-mini` | Análise financeira, geração de relatórios | https://platform.openai.com/docs |
| **Groq** | `llama-3.3-70b-versatile`, `mixtral-8x7b-32768` | Tarefas rápidas, alto volume, baixo custo | https://console.groq.com/docs |
| **Anthropic** | `claude-opus-4-5`, `claude-sonnet-4-5` | Raciocínio complexo, compliance legal | https://docs.anthropic.com |

### Configuração recomendada por agente (custo x performance):

```json
{
  "context_agent":     { "provider": "gemini",    "model": "gemini-3-flash-preview" },
  "financial_agent":   { "provider": "gemini",    "model": "gemini-3.1-pro-preview" },
  "contracts_agent":   { "provider": "anthropic", "model": "claude-opus-4-5" },
  "maintenance_agent": { "provider": "groq",      "model": "llama-3.3-70b-versatile" },
  "investment_agent":  { "provider": "groq",      "model": "llama-3.3-70b-versatile" },
  "compliance_agent":  { "provider": "anthropic", "model": "claude-opus-4-5" },
  "orchestrator":      { "provider": "gemini",    "model": "gemini-3.1-pro-preview" },
  "meta_agent":        { "provider": "anthropic", "model": "claude-opus-4-5" }
}
```

> **Lógica da escolha:** Gemini Flash para tarefas de leitura e extração (barato e rápido), Gemini Pro e Claude Opus para análises complexas, Groq para tarefas simples de alta velocidade.

---

## Arquitetura do Sistema

```
sistema-auditoria/
├── main.py                          # Ponto de entrada do sistema
├── config.py                        # Configurações globais e variáveis de ambiente
├── requirements.txt                 # Dependências Python
├── .env                             # Chaves de API (não versionar)
├── .env.example                     # Exemplo de variáveis de ambiente
│
├── core/
│   ├── __init__.py
│   ├── orchestrator.py              # Agente Orquestrador — coordena todos os agentes
│   ├── memory.py                    # Sistema de memória compartilhada entre agentes
│   ├── meta_agent.py                # Meta-Agente — cria novos agentes e skills
│   ├── tools.py                     # Ferramentas compartilhadas (PDF, busca, APIs)
│   └── llm_router.py                # Roteador de provedores de IA
│
├── providers/                       # Adaptadores para cada provedor de IA
│   ├── __init__.py
│   ├── base_provider.py             # Classe base — interface comum para todos
│   ├── gemini_provider.py           # Adaptador Google Gemini
│   ├── openai_provider.py           # Adaptador OpenAI
│   ├── groq_provider.py             # Adaptador Groq
│   └── anthropic_provider.py        # Adaptador Anthropic
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py                # Classe base que todos os agentes herdam
│   ├── context_agent.py             # Agente de Contexto — lê e indexa documentos
│   ├── financial_agent.py           # Agente Financeiro — analisa receitas e despesas
│   ├── contracts_agent.py           # Agente de Contratos — valida pagamentos vs contratos
│   ├── maintenance_agent.py         # Agente de Manutenções — verifica irregularidades
│   ├── investment_agent.py          # Agente de Investimentos — fundo de reserva, ROI
│   └── compliance_agent.py          # Agente de Compliance — conformidade legal
│
├── skills/
│   ├── README.md                    # Como criar e registrar uma nova skill
│   ├── registry.json                # Registro de todas as skills disponíveis
│   ├── financial/
│   │   ├── SKILL.md
│   │   └── anomaly_detection.md
│   ├── contracts/
│   │   ├── SKILL.md
│   │   └── reajuste_indices.md
│   ├── maintenance/
│   │   ├── SKILL.md
│   │   └── orcamento_validation.md
│   ├── compliance/
│   │   ├── SKILL.md
│   │   └── lei_condominios.md
│   └── meta/
│       ├── SKILL.md
│       └── skill_creator.md
│
├── knowledge/
│   ├── README.md
│   ├── legislacao/
│   │   ├── lei_4591_64.md
│   │   ├── codigo_civil_1331.md
│   │   └── normas_abnt.md
│   └── templates/
│       ├── relatorio_auditoria.md
│       └── perguntas_assembleia.md
│
├── condominios/
│   └── parque_colibri/
│       ├── config.json              # Configuração do condomínio + provider por agente
│       ├── memoria/
│       │   ├── contratos.json
│       │   ├── atas.json
│       │   └── historico.json
│       ├── documentos/
│       │   ├── balancetes/
│       │   ├── atas/
│       │   └── contratos/
│       └── relatorios/
│
└── outputs/
    ├── relatorios/
    └── alertas/
```

---

## Camada de Provedores (`providers/`)

Esta é a peça central que permite trocar o modelo de cada agente sem alterar nenhum código dos agentes.

### `providers/base_provider.py` — Interface comum

```python
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
```

---

### `providers/gemini_provider.py` — Google Gemini

```python
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
```

---

### `providers/openai_provider.py` — OpenAI

```python
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
                {"role": "user",   "content": user_message}
            ]
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            provider="openai",
            model=self.model,
            tokens_input=response.usage.prompt_tokens,
            tokens_output=response.usage.completion_tokens
        )
```

---

### `providers/groq_provider.py` — Groq

```python
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
                {"role": "user",   "content": user_message}
            ]
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            provider="groq",
            model=self.model,
            tokens_input=response.usage.prompt_tokens,
            tokens_output=response.usage.completion_tokens
        )
```

---

### `providers/anthropic_provider.py` — Anthropic

```python
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
```

---

### `core/llm_router.py` — Roteador de Provedores

```python
from providers.gemini_provider import GeminiProvider
from providers.openai_provider import OpenAIProvider
from providers.groq_provider import GroqProvider
from providers.anthropic_provider import AnthropicProvider
from providers.base_provider import BaseProvider
import os

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

    PROVIDERS = {
        "gemini":    (GeminiProvider,    "GEMINI_API_KEY"),
        "openai":    (OpenAIProvider,    "OPENAI_API_KEY"),
        "groq":      (GroqProvider,      "GROQ_API_KEY"),
        "anthropic": (AnthropicProvider, "ANTHROPIC_API_KEY"),
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

        ProviderClass, env_key = self.PROVIDERS[provider]
        api_key = os.getenv(env_key)

        if not api_key:
            raise EnvironmentError(
                f"Chave de API não encontrada para '{provider}'. "
                f"Configure a variável de ambiente {env_key} no arquivo .env"
            )

        return ProviderClass(api_key=api_key, model=model)

    def get_from_config(self, agent_config: dict) -> BaseProvider:
        """
        Atalho: recebe o dicionário de config do agente e retorna o provedor.

        Args:
            agent_config: Ex: {"provider": "gemini", "model": "gemini-3-flash-preview"}
        """
        return self.get(agent_config["provider"], agent_config["model"])
```

---

## Configuração por Condomínio (`condominios/parque_colibri/config.json`)

```json
{
  "nome": "Parque Colibri",
  "cnpj": "33.690.478/0001-40",
  "endereco": "Rua Alagoas, 477 - Iguaçu - Araucária/PR",
  "unidades": 224,
  "administradora": "Araucária Administradora de Condomínios",
  "sindico_atual": "Thiago dos Santos Gomes",
  "garantidora": "Condoplus Soluções de Cobrança Condominial",

  "limites_aprovacao": {
    "pix_sem_contrato_alerta": 500.00,
    "exige_3_orcamentos": 1500.00,
    "exige_aprovacao_assembleia": 6000.00
  },

  "agentes": {
    "context_agent":     { "provider": "gemini",    "model": "gemini-3-flash-preview" },
    "financial_agent":   { "provider": "gemini",    "model": "gemini-3.1-pro-preview" },
    "contracts_agent":   { "provider": "anthropic", "model": "claude-opus-4-5" },
    "maintenance_agent": { "provider": "groq",      "model": "llama-3.3-70b-versatile" },
    "investment_agent":  { "provider": "groq",      "model": "llama-3.3-70b-versatile" },
    "compliance_agent":  { "provider": "anthropic", "model": "claude-opus-4-5" },
    "orchestrator":      { "provider": "gemini",    "model": "gemini-3.1-pro-preview" },
    "meta_agent":        { "provider": "anthropic", "model": "claude-opus-4-5" }
  }
}
```

> Para trocar o modelo de qualquer agente, basta editar este arquivo. Nenhum código Python precisa ser alterado.

---

## Variáveis de Ambiente (`.env`)

```env
# Google Gemini — https://aistudio.google.com/apikey
GEMINI_API_KEY=sua_chave_gemini_aqui

# OpenAI — https://platform.openai.com/api-keys
OPENAI_API_KEY=sua_chave_openai_aqui

# Groq — https://console.groq.com/keys
GROQ_API_KEY=sua_chave_groq_aqui

# Anthropic — https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=sua_chave_anthropic_aqui

# APIs externas
RECEITA_FEDERAL_API=https://www.receitaws.com.br/v1/cnpj
VIACEP_API=https://viacep.com.br/ws

# Caminhos
CONDOMINIOS_PATH=./condominios
OUTPUTS_PATH=./outputs
SKILLS_PATH=./skills
KNOWLEDGE_PATH=./knowledge

# Configurações do sistema
LOG_LEVEL=INFO
MAX_TOKENS_PER_AGENT=4096
TEMPERATURA_AGENTES=0.1
```

---

## Dependências (`requirements.txt`)

```
# Provedores de IA
google-generativeai>=0.8.0
openai>=1.30.0
groq>=0.9.0
anthropic>=0.25.0

# Leitura de PDFs
pdfplumber>=0.10.0
pypdf>=4.0.0

# Utilitários
python-dotenv>=1.0.0
requests>=2.31.0
pandas>=2.0.0
loguru>=0.7.0
rich>=13.0.0

# Geração de relatórios
reportlab>=4.0.0
markdown>=3.5.0

# Armazenamento de memória vetorial (fase 2)
chromadb>=0.4.0
```

---

## Exemplo de uso completo

```python
from core.orchestrator import Orchestrator

# Os provedores de cada agente são lidos automaticamente do config.json
orq = Orchestrator(condominio="parque_colibri")

# Auditar balancete — cada agente usa seu próprio provider configurado
resultado = orq.processar_documento(
    path="condominios/parque_colibri/documentos/balancetes/marco_2026.pdf",
    tipo="balancete"
)

# Ver relatório completo
print(resultado.relatorio)

# Ver alertas por severidade
for alerta in resultado.alertas_criticos:
    print(f"🔴 {alerta}")

for alerta in resultado.alertas_atencao:
    print(f"🟡 {alerta}")
```

---

## Trocar o provedor de um agente em tempo de execução

```python
from agents.compliance_agent import ComplianceAgent

# Usar o provider padrão definido no config.json
agente = ComplianceAgent(condominio="parque_colibri")

# Ou forçar outro provider em tempo de execução
agente = ComplianceAgent(
    condominio="parque_colibri",
    agent_config={"provider": "openai", "model": "gpt-4o"}
)
```

---

## Criar novo agente via Meta-Agente

```python
from core.meta_agent import MetaAgent

meta = MetaAgent(condominio="parque_colibri")

meta.create_agent(
    necessidade="Preciso de um agente que monitore o consumo de água "
                "comparando mês a mês e detecte variações acima de 20% "
                "que possam indicar vazamento no poço artesiano"
)
# Resultado automático:
# - agents/water_agent.py (código documentado)
# - skills/water/SKILL.md (instruções do agente)
# - registry.json atualizado
# - config.json do condomínio atualizado
```

---

## Próximos passos sugeridos

1. Criar a estrutura de pastas e o `.env` com as chaves de API
2. Implementar `providers/base_provider.py` e os 4 adaptadores
3. Implementar `core/llm_router.py`
4. Implementar `agents/base_agent.py` e `core/memory.py`
5. Implementar `agents/context_agent.py` — testar leitura do balancete de março/2026
6. Implementar os demais agentes um por um, testando cada um
7. Implementar o `core/orchestrator.py`
8. Implementar o `core/meta_agent.py` por último

---

## Contexto do Projeto

Sistema desenvolvido a partir de auditoria real do **Condomínio Parque Colibri**, Araucária/PR. Achados que motivaram o sistema:

- Saldo negativo em fev e mar/2026 (R$ -3.843 e R$ -2.124)
- Empréstimo painéis solares parcela 41/72 sem demonstrativo de retorno
- Contrato E. Senna R$ 79.551 — necessita validação em ata de assembleia
- Escritório Quadros & Voudan — parcelas 11 e 12/12 pagas no mesmo mês
- PIX avulsos a pessoas físicas sem contrato (jardim, hidráulica, elétrica)
- Fuga de energia comprovada em vídeo — acidente com menor em março/2026
- Conta do síndico anterior (Emerson) ainda ativa com R$ 900 parado
- Assembleia convocada para 27/04/2026 com pauta de aumento de taxa

Esses casos reais devem ser usados como cenários de teste durante o desenvolvimento.
