---
name: personalizacao
description: Personalizar nomes em relevo em chaveiros e placas parametricas usando os exemplos locais.
---

Use para nomes, mensagens e medidas de placas/chaveiros. Para logos SVG ou objetos novos, adapte a geometria explicitamente.
Prefira `create chaveiro` ou `create placa` com `--nome`/`--texto`, `--largura`, `--profundidade`, `--espessura` e `--relevo`. JSON em `models/` continua disponivel para fluxos existentes.
Texto: 1 a 40 caracteres; fonte Arial do sistema. O motor mede e reduz o texto para caber, mas nomes longos podem ficar ilegíveis ao imprimir.
Preserve ao menos 2 mm em torno do furo. Confira glifos/acentos e tamanho visual no preview.

Exemplo: “Chaveiro ANA com 60 mm”:
```powershell
.venv/Scripts/python.exe -m bambu_ai create chaveiro --nome "ANA" --largura 60 --out exports/ana
```
Valide antes da entrega. Relevo faz parte de um unico solido; cores sao atribuidas manualmente no fatiador.
