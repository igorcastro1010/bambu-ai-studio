---
name: personalizacao
description: Personalizar nomes em relevo em chaveiros e placas parametricas usando os exemplos locais.
---

Use para nomes, mensagens e medidas de placas/chaveiros. Para logos SVG ou objetos novos, adapte a geometria explicitamente.
Copie `models/chaveiro.json` ou `models/placa.json`; edite `text`, `width`, `depth`, `thickness` e `relief`.
Texto: 1 a 40 caracteres; fonte Arial do sistema. O motor mede e reduz o texto para caber, mas nomes longos podem ficar ilegíveis ao imprimir.
Preserve ao menos 2 mm em torno do furo. Confira glifos/acentos e tamanho visual no preview.

Exemplo: “Chaveiro ANA com 60 mm” -> `text: "ANA"`, `width: 60` em novo JSON.
```powershell
.venv/Scripts/python.exe -m bambu_ai generate models/ana.json --out exports/ana
```
Valide antes da entrega. Relevo faz parte de um unico solido; cores sao atribuidas manualmente no fatiador.
