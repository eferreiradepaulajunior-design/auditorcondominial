# Criação de Skills

## Estrutura de uma skill

Cada skill é um diretório dentro de `skills/` com:
- `SKILL.md` — instruções principais (system prompt do agente)
- Arquivos `.md` auxiliares — regras específicas, tabelas de referência

## Como criar uma nova skill

1. Criar diretório em `skills/<nome_da_skill>/`
2. Criar `SKILL.md` com a estrutura abaixo
3. Registrar em `skills/registry.json`

## Template do SKILL.md

```markdown
# Skill: Nome da Skill

Você é um [papel] especializado em [domínio].

## Sua função
[Descrição clara do que o agente faz]

## Regras de análise
[Lista de regras específicas]

## Formato de resposta
JSON com: resumo, achados, alertas_criticos, alertas_atencao, recomendacoes.
```
