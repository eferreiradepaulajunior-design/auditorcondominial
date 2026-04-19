# Como criar e registrar uma nova skill

## Estrutura

```
skills/
├── registry.json          # Registro central de todas as skills
├── <nome_skill>/
│   ├── SKILL.md           # Instruções principais (system prompt)
│   └── *.md               # Arquivos auxiliares de referência
```

## Passos

1. Crie uma pasta em `skills/<nome>/`
2. Crie o `SKILL.md` com instruções para o agente
3. Adicione arquivos auxiliares conforme necessário
4. Registre no `registry.json`

## O Meta-Agente pode criar skills automaticamente

```python
from core.meta_agent import MetaAgent
meta = MetaAgent(condominio="parque_colibri")
meta.create_agent(necessidade="descrição do que o agente deve fazer")
```
