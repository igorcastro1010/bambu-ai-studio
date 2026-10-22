---
name: modelagem-3d
description: Criar ou editar pecas parametricas locais com CadQuery, build123d ou OpenSCAD, em milimetros.
---

Use para novas geometrias ou alteracoes dimensionais. Para um nome diferente, prefira personalizacao.

1. Confira o JSON de exemplo mais proximo em `models/` e o contrato `src/bambu_ai/spec.py`.
2. Reutilize `cad.py`; escolha um motor por ambiente. Fure/corte/funda de modo a obter um unico solido.
3. Preserve base plana, folgas explicitas e parametros editaveis. Nao invente requisitos mecanicos.
4. Gere em pasta nova, confira `validation.json` e abra o preview. Relate medidas e limites.

Exemplo: “Crie suporte de celular com 65 mm de largura”. Copie `models/suporte-celular.json`, edite `width` e execute:
```powershell
.venv/Scripts/python.exe -m bambu_ai generate models/meu-suporte.json --out exports/meu-suporte
```
STL/STEP via CAD; `.scad` pelo comando `render-scad`, apenas STL. Nao chamar impressora.
