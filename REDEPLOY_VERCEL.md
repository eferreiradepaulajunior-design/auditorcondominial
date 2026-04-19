# 🚀 Como Fazer Redeploy na Vercel

Seu projeto agora está totalmente configurado para Vercel. Aqui está o passo a passo para corrigir o erro que você teve.

## ✅ O Que Foi Feito

1. **✓ `vercel.json`** — Configuração completa da aplicação FastAPI para Vercel
2. **✓ `api/app.py`** — Entrypoint específico para Serverless Functions da Vercel
3. **✓ `.vercelignore`** — Arquivos a ignorar no deploy
4. **✓ `requirements.txt`** — Dependências otimizadas (sem duplicatas)
5. **✓ `/health` endpoints** — Para health checks
6. **✓ `validate_local.py`** — Script de validação

## 📝 Passo a Passo do Redeploy

### 1. **Commit e Push das Mudanças**

```bash
# Na pasta do projeto
cd c:\Users\Edson\Documents\GitHub\auditorcontabil

# Fazer commit de todas as mudanças
git add .
git commit -m "fix: Configurar para deploy Vercel - adicionar entrypoint e vercel.json"
git push origin main
```

### 2. **Redeploy na Vercel**

**Opção A: Automático (recomendado)**
- O Vercel detectará o push automaticamente
- Fará rebuild e redeploy em ~2-5 minutos
- Acompanhe em: https://vercel.com/dashboard

**Opção B: Manual**
1. Acessar https://vercel.com/dashboard
2. Selecionar projeto "auditorcontabil"
3. Clicar em "Settings" → "Deployments"
4. Clicar "Redeploy" no deploy mais recente
5. Aguardar conclusão

### 3. **Verificar o Deploy**

Após o build terminar:

```bash
# Testar o healthcheck (deve retornar {"status":"ok"})
curl https://auditorcontabil.vercel.app/health

# Testar o login
# Abrir em navegador: https://auditorcontabil.vercel.app/login
```

### 4. **Configurar Variáveis de Ambiente** (se ainda não fez)

No dashboard da Vercel:
1. Project → Settings → Environment Variables
2. Adicionar:
   - `GEMINI_API_KEY=sua_chave`
   - `OPENAI_API_KEY=sua_chave`
   - `GROQ_API_KEY=sua_chave`
   - `ANTHROPIC_API_KEY=sua_chave`
3. Redeploy após adicionar variáveis

## 🔍 Troubleshooting

### Erro: `FUNCTION_INVOCATION_FAILED`

Se ainda receber este erro:

1. **Verificar logs**
   - Dashboard Vercel → "Deployments" → Clicar no deploy → "Functions" → Ver logs

2. **Testar localmente primeiro**
   ```bash
   python validate_local.py  # Deve passar em todos os checks
   uvicorn app:app --reload   # Deve iniciar sem erros
   ```

3. **Aumentar timeout (se tem Pro)**
   ```json
   // vercel.json
   "functions": {
     "api/app.py": {
       "maxDuration": 60  // Aumentar de 30 para 60 segundos
     }
   }
   ```

### Erro: `Module not found`

1. Verificar que `requirements.txt` está na raiz
2. Fazer push de novo
3. Redeploy

### Erro: `Connection timeout`

Vercel Free tem limite de 10 segundos. Para rodar auditorias completas:

**Opção 1**: Usar apenas para chat (sem auditoria)
```python
# Desabilitar pipeline no código
@app.post("/pipeline/start/{cond_id}")
async def start_pipeline(cond_id: str):
    return {"error": "Auditorias não disponíveis no free tier"}
```

**Opção 2**: Upgrade para Vercel Pro ($20/mês, 60s timeout)

**Opção 3**: Hospedar em VPS (Railway, Render, DigitalOcean, ~$5-20/mês)

## ✨ Estrutura Final

```
auditorcontabil/
├── app.py                    # ← Entrypoint local
├── api/app.py               # ← Entrypoint Vercel
├── vercel.json              # ← Config Vercel
├── .vercelignore            # ← Arquivos ignorados
├── requirements.txt         # ← Dependências otimizadas
├── validate_local.py        # ← Script de validação
├── DEPLOY_VERCEL.md        # ← Guia completo de deploy
├── web/app.py              # ← App FastAPI principal
└── ... (resto dos arquivos)
```

## 🎯 Próximos Passos

1. ✅ Fazer commit e push: `git push origin main`
2. 🔄 Aguardar Vercel fazer build (deve passar agora)
3. 🔐 Configurar variáveis de ambiente na Vercel
4. ✓ Testar endpoints: `/health`, `/login`
5. 🚀 Começar a usar!

## 📚 Referências

- [Vercel Python Docs](https://vercel.com/docs/functions/python)
- [FastAPI on Vercel](https://vercel.com/templates/python/fastapi)
- Arquivo [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md) para mais detalhes

---

**Dúvidas?** Verifique os logs de build na Vercel dashboard ou execute `python validate_local.py` para diagnosticar.

Happy deploying! 🚀
