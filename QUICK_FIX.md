# 🔧 Quick Fix — Deploy Vercel

## ❌ Problema
```
500 INTERNAL_SERVER_ERROR
FUNCTION_INVOCATION_FAILED
```

## ✅ Solução Aplicada

### Arquivos Criados/Modificados

| Arquivo | Motivo |
|---------|--------|
| `api/app.py` | Entrypoint para Serverless Functions da Vercel |
| `vercel.json` | Configuração do projeto FastAPI na Vercel |
| `.vercelignore` | Arquivos a ignorar no deploy |
| `requirements.txt` | Dependências otimizadas (removeu duplicatas) |
| `web/app.py` | Adicionado endpoints `/health` |
| `validate_local.py` | Script para validar tudo funciona localmente |

### Próximos Passos (15 minutos)

```bash
# 1. Validar localmente (deve passar)
python validate_local.py

# 2. Commit e push
git add .
git commit -m "fix: Vercel deployment config"
git push origin main

# 3. Redeploy (automático ou manual)
# Vercel fará rebuild em ~2-5 min

# 4. Testar
curl https://auditorcontabil.vercel.app/health
# Deve retornar: {"status":"ok","service":"Auditor Contábil"}
```

## 📋 Checklist

- [ ] Executou `python validate_local.py` com sucesso?
- [ ] Fez `git push origin main`?
- [ ] Viu build iniciando no Vercel dashboard?
- [ ] Build passou (verde) ou falhou (vermelho)?
- [ ] Consegue acessar `/health` sem erro 500?

## 🆘 Se Ainda Falhar

### Ver Logs (Mais Importante)
1. Vercel Dashboard → auditorcontabil → Deployments
2. Clicar no deploy mais recente
3. Aba "Functions" → Ver logs

### Testes Locais
```bash
# Validar tudo
python validate_local.py

# Rodar servidor localmente
uvicorn app:app --reload

# Testar imports
python -c "from api.app import app; print('OK')"
```

### Comum: Timeout de 10 segundos
Vercel Free tem limite de 10s. Se auditoria exceder:
- **Opção 1**: Upgrade para Pro ($20/mês, 60s)
- **Opção 2**: Usar VPS (Railway, Render, ~$5-20/mês)
- **Opção 3**: Criar fila de tarefas (Redis/Celery)

## 📚 Documentação

- [REDEPLOY_VERCEL.md](REDEPLOY_VERCEL.md) — Guia completo passo a passo
- [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md) — Troubleshooting e detalhes técnicos
- [validate_local.py](validate_local.py) — Validação automática

---

**TL;DR**: Fazer `git push`, aguardar build, testar `/health`. Se falhar, ver logs no Vercel.
