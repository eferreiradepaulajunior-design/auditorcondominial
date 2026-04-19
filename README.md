# 🏢 Auditor Contábil — Sistema de Auditoria Condominial com IA

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-green)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)

Um **sistema inteligente de auditoria condominial** que utiliza uma equipe de **6 agentes de IA especializados** para analisar documentos, detectar irregularidades financeiras, validar contratos e gerar relatórios detalhados automaticamente.

## 🎯 Características Principais

✅ **Equipe de 6 Agentes Especializados**
- 📋 **Analista de Documentos** — Extrai dados de PDFs (balancetes, atas, contratos)
- 💰 **Auditor Financeiro** — Analisa receitas, despesas e detecta anomalias
- 📝 **Analista de Contratos** — Valida pagamentos vs. contratos
- 🔧 **Analista de Manutenção** — Verifica gastos com manutenção e segurança
- 📊 **Analista de Investimentos** — Avalia fundos de reserva e ROI
- ⚖️ **Consultor Jurídico** — Valida compliance legal

✅ **Suporta 4 Provedores de IA**
- Google Gemini (recomendado para extração de PDFs)
- OpenAI GPT-4
- Groq (rápido e barato)
- Anthropic Claude

✅ **Web Interface Moderna**
- 💬 Chat em tempo real com agentes como "funcionários" da empresa
- 📊 Kanban interativo para visualizar pipeline de auditorias
- 🏠 CRUD completo para gerenciar condomínios
- 📁 Upload/download/organização de documentos por categoria
- 🔐 Autenticação com sessões seguras (bcrypt + itsdangerous)

✅ **Pipeline de Auditoria Automatizado**
- 7 etapas sequenciais com atualização em tempo real
- Fallback para modo simulado quando IA indisponível
- Detecção automática de alertas críticos, atenção e recomendações

✅ **Relatórios Profissionais**
- Markdown formatado com estrutura padronizada
- Resumo executivo, análises por agente e conclusões
- Exportação em PDF (ready to implement)

---

## 🚀 Deploy

### Ambiente Local

```bash
# Simples e elegante
uvicorn app:app --reload

# Ou com argumentos customizados
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Vercel (Serverless Cloud)

Para fazer deploy na Vercel:

1. **Fazer commit das mudanças**
   ```bash
   git add .
   git commit -m "Deploy: Prepare for Vercel"
   git push origin main
   ```

2. **Importar no Vercel**
   - Acessar [vercel.com](https://vercel.com)
   - Clicar "Add New" → "Project"
   - Selecionar repositório `auditorcontabil`
   - Clicar "Deploy"

3. **Configurar variáveis de ambiente**
   - Project Settings → Environment Variables
   - Adicionar: `GEMINI_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY`, `ANTHROPIC_API_KEY`

> ⚠️ **Nota**: Vercel Free tem limite de 10 segundos. Para auditorias completas, considere upgrade para **Pro** (60s) ou **hosting em VPS**. Ver [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md) para detalhes.

---

### Pré-requisitos

- Python 3.11+
- pip ou conda
- Chaves de API dos provedores (Gemini, OpenAI, Groq e/ou Anthropic)

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/auditorcontabil.git
cd auditorcontabil
```

### 2. Criar ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` com suas chaves de API:

```env
# Provedores de IA
GEMINI_API_KEY=sua_chave_gemini
OPENAI_API_KEY=sua_chave_openai
GROQ_API_KEY=sua_chave_groq
ANTHROPIC_API_KEY=sua_chave_anthropic

# Configurações
LOG_LEVEL=INFO
FLASK_ENV=production
```

### 5. Executar o servidor web

```bash
# Opção 1: Simples (recomendado)
uvicorn app:app --reload

# Opção 2: Com host/porta customizados
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Acesse: **http://localhost:8000**

> **Primeiro acesso**: Crie uma conta admin (usuário e senha), depois faça login.

> **Nota**: O arquivo `app.py` na raiz é o entrypoint automático descoberto pelo Uvicorn. Ele importa a aplicação de `web/app.py`.

---

## 📋 Uso

### Via Web Interface

#### 1. **Gerenciar Condomínios**
- Dashboard → Aba "Condomínios" → Criar novo
- Preencher dados básicos (nome, endereço, unidades, síndico)
- Sistema cria automaticamente: `condominios/{slug}/config.json`

#### 2. **Fazer Upload de Documentos**
- Ir para "Detalhe do Condomínio"
- Upload de PDFs/Excel em categorias:
  - `balancetes/` — Demonstrativos financeiros mensais
  - `atas/` — Atas de assembleias
  - `contratos/` — Contratos com fornecedores
- Documentos salvos em: `condominios/{slug}/documentos/`

#### 3. **Iniciar Auditoria**
- Na página de detalhe → Botão "🚀 Iniciar Auditoria"
- Sistema cria pipeline e começa a processar
- Acompanhe em tempo real:
  - **Badge de progresso** na página do condomínio
  - **Kanban** (Dashboard → "📊 Pipeline/Kanban") com 9 colunas

#### 4. **Visualizar Resultados**
- **Kanban** mostra alertas críticos, atenção e recomendações por condomínio
- **Clique no card** para ver detalhes completos, log da auditoria e relatório

#### 5. **Chat com Agentes**
- **Aba "Chat"** — Converse com os agentes como se fossem funcionários
- Exemplo: "Roberto, analise o balancete de março"
- Agentes respondem com análises específicas
- Suporta delegação entre agentes automaticamente

### Via CLI

```bash
# Auditar balancete específico
python main.py auditar parque_colibri condominios/parque_colibri/documentos/balancetes/marco_2026.pdf

# Criar novo agente personalizado
python main.py criar-agente parque_colibri "Agente que detecta fraudes em transferências bancárias"
```

---

## 📁 Estrutura do Projeto

```
auditorcontabil/
├── 📄 README.md                         # Este arquivo
├── 📄 requirements.txt                  # Dependências Python
├── 📄 .env.example                      # Template de variáveis de ambiente
├── 🐍 main.py                           # CLI principal (auditar, criar-agente)
├── 🐍 config.py                         # Configurações globais
│
├── 📁 core/                             # Backend — Lógica de auditoria
│   ├── 🐍 orchestrator.py               # Orquestrador (coordena 6 agentes)
│   ├── 🐍 meta_agent.py                 # Meta-Agente (cria novos agentes dinamicamente)
│   ├── 🐍 memory.py                     # Memória compartilhada entre agentes
│   ├── 🐍 tools.py                      # Ferramentas comuns (PDF, busca, APIs)
│   └── 🐍 llm_router.py                 # Roteador de provedores de IA
│
├── 📁 providers/                        # Adaptadores de IA
│   ├── 🐍 base_provider.py              # Interface comum
│   ├── 🐍 gemini_provider.py            # Google Gemini
│   ├── 🐍 openai_provider.py            # OpenAI
│   ├── 🐍 groq_provider.py              # Groq
│   └── 🐍 anthropic_provider.py         # Anthropic Claude
│
├── 📁 agents/                           # Agentes especializados
│   ├── 🐍 base_agent.py                 # Classe base (herança)
│   ├── 🐍 context_agent.py              # Extração de dados
│   ├── 🐍 financial_agent.py            # Análise financeira
│   ├── 🐍 contracts_agent.py            # Validação de contratos
│   ├── 🐍 maintenance_agent.py          # Análise de manutenção
│   ├── 🐍 investment_agent.py           # Análise de investimentos
│   └── 🐍 compliance_agent.py           # Conformidade legal
│
├── 📁 skills/                           # Knowledge base (regras de análise)
│   ├── 📄 registry.json                 # Índice de skills
│   ├── 📁 financial/
│   │   └── 📄 SKILL.md                  # Instruções para agente financeiro
│   ├── 📁 contracts/
│   ├── 📁 maintenance/
│   ├── 📁 compliance/
│   └── 📁 meta/
│
├── 📁 knowledge/                        # Base de conhecimento
│   ├── 📁 legislacao/
│   │   ├── 📄 lei_4591_64.md            # Lei de condomínios
│   │   ├── 📄 codigo_civil_1331.md      # Direitos dos condôminos
│   │   └── 📄 normas_abnt.md            # Normas técnicas
│   └── 📁 templates/
│       ├── 📄 relatorio_auditoria.md    # Template de relatório
│       └── 📄 perguntas_assembleia.md   # Perguntas para assembleia
│
├── 📁 web/                              # Web interface (FastAPI)
│   ├── 🐍 app.py                        # Aplicação FastAPI
│   ├── 🐍 auth.py                       # Autenticação (bcrypt)
│   ├── 🐍 database.py                   # SQLite (usuários, pipelines, chat)
│   ├── 🐍 pipeline.py                   # Engine de pipeline
│   ├── 🐍 agent_profiles.py             # Perfis dos agentes no chat
│   │
│   ├── 📁 routes/
│   │   ├── 🐍 admin.py                  # CRUD de condomínios, documentos
│   │   ├── 🐍 chat.py                   # Chat em tempo real (WebSocket)
│   │   └── 🐍 pipeline.py               # API de pipeline e Kanban
│   │
│   └── 📁 templates/
│       ├── 📄 login.html                # Página de login/registro
│       ├── 📄 layout.html               # Layout base
│       └── 📁 admin/
│           ├── 📄 dashboard.html        # Dashboard principal
│           ├── 📄 condominios.html      # Lista de condomínios
│           ├── 📄 condominio_detail.html # Detalhe (documentos, botão de auditoria)
│           ├── 📄 kanban.html           # Kanban de pipelines
│           └── 📄 chat.html             # Interface de chat com agentes
│
├── 📁 condominios/                      # Dados dos condomínios (não versionar)
│   └── 📁 parque_colibri/ (exemplo)
│       ├── 📄 config.json               # Config: nome, síndico, agentes
│       ├── 📁 documentos/
│       │   ├── 📁 balancetes/
│       │   ├── 📁 atas/
│       │   ├── 📁 contratos/
│       │   └── 📁 outro/
│       ├── 📁 memoria/                  # Histórico de auditorias
│       └── 📁 relatorios/               # Relatórios gerados
│
├── 📁 logs/                             # Logs de execução
│   └── 📄 auditoria_YYYYMMDD.log
│
└── 📁 outputs/                          # Saídas de execução
    ├── 📁 relatorios/
    └── 📁 alertas/
```

---

## ⚙️ Configuração Detalhada

### Configurar Provedores de IA por Agente

Edite `condominios/{nome}/config.json`:

```json
{
  "nome": "Parque Colibri",
  "endereço": "Rua das Flores, 123",
  "unidades": 42,
  "síndico_atual": "João Silva",
  "administradora": "Adm. XYZ",
  "agentes": {
    "context_agent": {
      "provider": "gemini",
      "model": "gemini-3-flash-preview"
    },
    "financial_agent": {
      "provider": "gemini",
      "model": "gemini-3.1-pro-preview"
    },
    "contracts_agent": {
      "provider": "anthropic",
      "model": "claude-opus-4-5"
    },
    "maintenance_agent": {
      "provider": "groq",
      "model": "llama-3.3-70b-versatile"
    },
    "investment_agent": {
      "provider": "groq",
      "model": "llama-3.3-70b-versatile"
    },
    "compliance_agent": {
      "provider": "anthropic",
      "model": "claude-opus-4-5"
    }
  }
}
```

### Recomendações de Custo vs Performance

| Agente | Provedor | Modelo | Razão |
|--------|----------|--------|-------|
| **Context** | Gemini | `gemini-3-flash-preview` | Lê PDFs nativamente, rápido |
| **Financial** | Gemini | `gemini-3.1-pro-preview` | Análise complexa, moderado |
| **Contracts** | Anthropic | `claude-opus-4-5` | Raciocínio jurídico |
| **Maintenance** | Groq | `llama-3.3-70b-versatile` | Rápido, custo baixo |
| **Investment** | Groq | `llama-3.3-70b-versatile` | Rápido, custo baixo |
| **Compliance** | Anthropic | `claude-opus-4-5` | Conformidade legal |

---

## 🔍 Pipeline de Auditoria (7 Etapas)

```
┌─────────────────────────────────────────────────────────┐
│ 🔍 EXTRAÇÃO                                             │
│ → Analista de Documentos lê PDFs, indexa dados         │
│ → Output: Balancete estruturado, atas, contratos      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 💰 ANÁLISE FINANCEIRA                                   │
│ → Auditor Financeiro analisa receitas e despesas      │
│ → Detecta anomalias (sobrepreço, falta de documentos) │
│ → Output: Alertas, anomalias, recomendações           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 📝 VALIDAÇÃO DE CONTRATOS                              │
│ → Analista de Contratos cruza pagamentos vs. contratos │
│ → Verifica reajustes, indices e cláusulas             │
│ → Output: Divergências, irregularidades               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 🔧 ANÁLISE DE MANUTENÇÕES                              │
│ → Analista de Manutenção verifica orçamentos           │
│ → Detecta sobrepreço, segurança predial               │
│ → Output: Alertas de segurança, economia potencial    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 📈 ANÁLISE DE INVESTIMENTOS                            │
│ → Analista de Investimentos avalia fundo de reserva    │
│ → Análise de ROI, empréstimos, aplicações             │
│ → Output: Recomendações de alocação                   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ ⚖️ CONFORMIDADE LEGAL                                   │
│ → Consultor Jurídico valida legislação                │
│ → Verifica Lei 4.591/64, decisões assembleia          │
│ → Output: Riscos legais, obrigações pendentes         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 📊 RELATÓRIO CONSOLIDADO                               │
│ → Orquestrador consolida todas as análises            │
│ → Gera relatório Markdown formatado                   │
│ → Output: Relatório profissional para assembleia      │
└─────────────────────────────────────────────────────────┘
                          ↓
                    ✅ CONCLUÍDO
```

---

## 💻 Exemplos de Uso

### Exemplo 1: Auditar Condomínio via Web

1. Acessar http://localhost:8000
2. Login com suas credenciais
3. Dashboard → "Condomínios" → Criar novo
4. Upload de documentos (balancete, atas)
5. Botão "🚀 Iniciar Auditoria"
6. Acompanhar no Kanban em tempo real
7. Clicar no card concluído para ver relatório

### Exemplo 2: Chat com Agentes

```
Você: "Roberto, há algo irregular no balancete de março?"

Roberto (Auditor Financeiro):
"Achei sim! Há 3 irregularidades críticas:
1. 🔴 Despesa de R$ 8.500 sem nota fiscal (fornecedor desconhecido)
2. 🔴 Diferença de R$ 2.300 entre balancete e extrato bancário
3. 🟡 PIX para fornecedor habitual por valor 35% acima do contratado

Recomendo escalação para o gestor e auditoria de segurança."
```

### Exemplo 3: Criar Novo Agente via CLI

```bash
python main.py criar-agente parque_colibri \
  "Agente que detecta fraudes em transferências PIX para fornecedores"
```

> Sistema cria automaticamente:
> - `agents/fraud_agent.py` (código do agente)
> - `skills/fraud/SKILL.md` (instruções)
> - Atualiza `condominios/parque_colibri/config.json`

---

## 🔐 Segurança

- ✅ **Senhas**: Hashed com bcrypt, nunca armazenadas em texto
- ✅ **Sessões**: Token seguro com itsdangerous + HTTPOnly cookies
- ✅ **Autenticação**: Middleware em todas as rotas admin
- ✅ **Upload**: Validação de tipos, limite de tamanho
- ✅ **Path Traversal**: Proteção contra ataques em download de arquivos
- ✅ **Isolamento**: Dados por condomínio (memória, documentos, relatórios)

---

## 📊 Banco de Dados

Usa **SQLite** (`data/auditoria.db`) com tabelas:

```sql
-- Usuários
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username TEXT UNIQUE,
  password_hash TEXT,
  display_name TEXT,
  role TEXT,
  created_at TIMESTAMP
);

-- Conversas (chat)
CREATE TABLE conversations (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  title TEXT,
  created_at TIMESTAMP
);

-- Mensagens
CREATE TABLE messages (
  id INTEGER PRIMARY KEY,
  conversation_id INTEGER,
  agent_id TEXT,
  content TEXT,
  created_at TIMESTAMP
);

-- Configurações
CREATE TABLE settings (
  id INTEGER PRIMARY KEY,
  key TEXT UNIQUE,
  value TEXT
);

-- Pipelines de Auditoria
CREATE TABLE audit_pipelines (
  id INTEGER PRIMARY KEY,
  condominio_id TEXT,
  condominio_nome TEXT,
  status TEXT,  -- 'running', 'done', 'error'
  current_stage TEXT,
  stages_done JSON,
  stages_errors JSON,
  started_at TIMESTAMP,
  updated_at TIMESTAMP,
  finished_at TIMESTAMP,
  triggered_by TEXT,
  result_summary TEXT,
  alertas_criticos INTEGER,
  alertas_atencao INTEGER,
  recomendacoes INTEGER,
  log JSON
);
```

---

## 🧪 Testando Localmente

### 1. Sem Chaves de API (Modo Simulado)

Se não tiver chaves configuradas, o sistema rodará em **modo simulado** com sleep() — útil para testes de UI.

### 2. Com Chaves (Funcionamento Completo)

Configure `.env` com suas chaves e o sistema usará IA de verdade.

### 3. Testar CLI

```bash
# Auditoria simulada
python main.py auditar parque_colibri condominios/parque_colibri/documentos/balancetes/teste.pdf

# Criar novo agente
python main.py criar-agente parque_colibri "Descrição..."
```

### 4. Testar Web

```bash
uvicorn web.app:app --reload
# Abrir http://localhost:8000
```

---

## 📦 Dependências Principais

```
FastAPI==0.136.0              # Framework web
uvicorn==0.30.0               # Servidor ASGI
Jinja2==3.1.4                 # Templates
python-multipart==0.0.9       # Formulários
itsdangerous==2.1.2           # Tokens de sessão
bcrypt==4.1.4                 # Hash de senhas

google-generativeai==0.8.3    # Google Gemini
openai==1.61.0                # OpenAI API
groq==0.13.0                  # Groq API
anthropic==0.40.0             # Anthropic Claude

PyPDF2==4.3.1                 # Leitura de PDFs
python-pptx==0.6.23           # PowerPoint (opcional)
openpyxl==3.1.5               # Excel (opcional)

loguru==0.7.2                 # Logging
rich==13.9.4                  # UI no terminal
```

Ver `requirements.txt` para versão exata.

---

## 🐛 Troubleshooting

### "Erro ao importar orchestrator"
> **Solução**: Sistema entra em modo simulado. Verifique se `core/orchestrator.py` existe e tem imports corretos.

### "API key inválida"
> **Solução**: Verifique `.env`. Chaves devem estar corretas (copiar-colar sem espaços extras).

### "Banco de dados travado"
> **Solução**: SQLite tem limite de conexões simultâneas. Reinicie o servidor.

### "Upload falha"
> **Solução**: Verifique:
> - Pasta `condominios/{slug}/documentos/` existe
> - Arquivo < 100MB
> - Extensão permitida (.pdf, .xlsx, .csv, .json, .txt)

---

## 🚦 Próximos Passos

- [ ] Exportar relatórios em PDF
- [ ] Integração com Zapier/Make para notificações
- [ ] Dashboard de histórico (auditorias passadas)
- [ ] Comparativo entre períodos (mês vs. mês)
- [ ] Integração com IA Vision para verificação de recibos
- [ ] API pública para integrar em sistemas contábeis
- [ ] Deploy em Docker/Kubernetes
- [ ] Suporte a múltiplos usuários com RBAC

---

## 📞 Suporte

- **Issues**: Abra uma issue no GitHub
- **Email**: suporte@auditorcontabil.com (fictício)
- **Docs**: Consulte `PROJETO_AUDITORIA_CONDOMINIAL.md` para detalhes técnicos

---

## 📄 Licença

MIT License — Veja `LICENSE` para detalhes.

---

## 👥 Autores

Desenvolvido com ❤️ para auditoria automatizada de condomínios.

**Stack**: Python + FastAPI + SQLite + Google Gemini/OpenAI/Groq/Anthropic

---

## 🎓 Aprenda Mais

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Google Gemini API](https://ai.google.dev/gemini-api/docs)
- [OpenAI API](https://platform.openai.com/docs)
- [Lei 4.591/64](http://www.planalto.gov.br/ccivil_03/leis/l4591.htm)
- [Código Civil - Art. 1331+](http://www.planalto.gov.br/ccivil_03/leis/2002/l10406.htm)

---

**Pronto para auditar condomínios com IA? 🚀**
