# 📱 Deploy na Vercel

Este projeto pode ser deployado na Vercel como uma aplicação FastAPI (Serverless Functions).

## ⚠️ Limitações da Vercel (Free Tier)

| Recurso | Limite |
|---------|--------|
| **Tempo máximo por função** | 10 segundos (Pro: 60s) |
| **Memória** | 512 MB (Pro: 3008 MB) |
| **Armazenamento** | Efêmero (sem persistência) |
| **Uploads de arquivo** | ~25 MB |
| **Concorrência** | 10 funções simultâneas |

> ⚠️ **IMPORTANTE**: Auditorias de condomínios podem **exceder 10 segundos**. Para produção, recomendamos:
> - **Upgrade para Plano Pro** (60s timeout, 3GB RAM)
> - **Usar fila de tarefas** (Redis/Bull) para pipelines longos
> - **Hospedar em VPS** (Linode, AWS EC2) para melhor controle

## 🚀 Deploy Passo a Passo

### 1. **Preparar o GitHub**

```bash
# Commit e push das mudanças
git add .
git commit -m "feat: Configurar para Vercel deployment"
git push origin main
```

### 2. **Importar na Vercel**

1. Acessar [vercel.com](https://vercel.com)
2. Fazer login com GitHub
3. Clicar "Add New" → "Project"
4. Selecionar repositório `auditorcontabil`
5. Não alterar nenhuma configuração (deixar defaults)
6. Clicar "Deploy"

### 3. **Configurar Variáveis de Ambiente**

Durante o deploy, Vercel pedirá para adicionar variáveis de ambiente. Ir para:

**Project Settings → Environment Variables** e adicionar:

```env
GEMINI_API_KEY=sua_chave_aqui
OPENAI_API_KEY=sua_chave_aqui
GROQ_API_KEY=sua_chave_aqui
ANTHROPIC_API_KEY=sua_chave_aqui
LOG_LEVEL=INFO
```

> ⚠️ Nunca deixar `.env` no Git. Use o painel da Vercel para segredos.

### 4. **Aguardar Build**

Vercel vai:
1. ✅ Clonar o repositório
2. ✅ Instalar dependências (`pip install -r requirements.txt`)
3. ✅ Criar as Serverless Functions
4. ✅ Deploy em CDN global

---

## 🔧 Troubleshooting

### Erro: `FUNCTION_INVOCATION_FAILED`

**Causa**: Função excedeu timeout (>10s) ou erro de importação

**Solução**:
```bash
# Testar localmente primeiro
uvicorn api.app:app --reload

# Verificar imports
python -c "from api.app import app; print('OK')"
```

### Erro: `Module not found`

**Causa**: Dependência faltando no `requirements.txt`

**Solução**:
```bash
# Atualizar requirements
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
```

### Erro: `SQLite database locked`

**Causa**: Múltiplas funções tentando acessar BD simultane amente

**Solução**: Implementar **connection pooling** ou usar PostgreSQL:

```python
# Usar PostgreSQL em vez de SQLite
DATABASE_URL = "postgresql://user:pass@host/db"
```

### Timeout de 10 segundos

**Causa**: Auditoria é muito lenta para Free Tier

**Solução**:

1. **Opção A**: Upgrade para Pro (60s)
2. **Opção B**: Criar fila de tarefas
   ```python
   # Usar Celery + Redis
   @app.post("/pipeline/start/{cond_id}")
   async def start_pipeline(cond_id: str):
       # Enviar para fila em vez de rodar direto
       task = celery_app.send_task('run_pipeline', args=[cond_id])
       return {"task_id": task.id}
   ```
3. **Opção C**: Usar VPS (recomendado para produção)

---

## 📊 Performance em Produção

### Local (seu PC)
- Extrair + Analisar + Relatório: ~30-60s ✅

### Vercel Free (10s timeout)
- Apenas leitura de status: ✅
- Chat com agentes: ⚠️ (pode dar timeout)
- Iniciar auditoria: ❌ (vai falhar)

### Vercel Pro (60s timeout)
- Extrair + Analisar + Relatório: ⚠️ (pode funcionar com pipeline menor)

### VPS Recomendado (produção)
- Sem limites: ✅
- Armazenamento ilimitado: ✅
- Pipelines paralelos: ✅

---

## 🎯 Opções de Deploy Recomendadas

| Opção | Custo | Latência | Escalabilidade | Recomendado Para |
|-------|-------|----------|----------------|------------------|
| **Vercel Pro** | $20/mês | Baixa (edge) | Média | MVP, teste inicial |
| **Railway** | $5-20/mês | Média | Boa | Protótipos |
| **Render** | $7-12/mês | Média | Boa | Apps pequenas |
| **AWS EC2** | $5-30/mês | Alta | Excelente | Produção |
| **Linode** | $5-30/mês | Média | Excelente | Produção |
| **DigitalOcean** | $5-20/mês | Média | Boa | Produção |

---

## ✅ Status do Deploy

```
✓ Estrutura: api/app.py (Serverless entrypoint)
✓ Config: vercel.json (3GB RAM, 30s timeout no Pro)
✓ Ignore: .vercelignore (excluir arquivos desnecessários)
✓ Dependências: requirements.txt (verificar versões)
```

---

## 📝 Próximos Passos

1. ✅ Fazer commit: `git push`
2. 🔄 Redeploy na Vercel (Settings → Redeploy)
3. 🔐 Adicionar variáveis de ambiente
4. 🧪 Testar: Acessar domínio da Vercel
5. 📈 Se tiver timeout frequente: Considerar upgrade ou VPS

---

## 🔗 Links Úteis

- [Vercel Docs - Python](https://vercel.com/docs/functions/python)
- [FastAPI on Vercel](https://vercel.com/templates/python/fastapi)
- [Railway Deploy Guide](https://railway.app/)
- [Render Deploy Guide](https://render.com/)

