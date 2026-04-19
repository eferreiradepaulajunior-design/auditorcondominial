# Knowledge Base — Auditoria Condominial

Este diretório contém a base de conhecimento utilizada pelos agentes de auditoria.

## Estrutura

```
knowledge/
├── legislacao/           # Resumos de legislação aplicável
│   ├── lei_4591_64.md    # Lei dos Condomínios
│   ├── codigo_civil_1331.md  # Código Civil — Condomínio Edilício
│   └── normas_abnt.md    # Normas técnicas relevantes
└── templates/            # Modelos de documentos
    ├── relatorio_auditoria.md    # Template do relatório final
    └── perguntas_assembleia.md   # Perguntas sugeridas para assembleias
```

## Como adicionar conhecimento

1. Crie um arquivo `.md` na subpasta adequada
2. Use formato Markdown com títulos claros
3. Inclua referências legais quando aplicável
4. O Agente de Compliance carrega automaticamente os arquivos de `legislacao/`
