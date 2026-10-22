---
name: validacao-stl
description: Verificar um STL local quanto a malha fechada, componentes, volume, dimensoes e limite nominal da A1 mini.
---

Use ao receber STL ou depois de alterar geometria. Nao tratar aprovacao geometrica como garantia de impressao.

```powershell
.venv/Scripts/python.exe -m bambu_ai validate exports/chaveiro/model.stl
```

Leia `valid`, `errors`, `warnings`, dimensoes, volume e componentes. Codigo de saida 1 significa reprovacao; 2 significa falha de entrada/execucao.
STL usa mm por convencao. Nao reescale ou repare silenciosamente; corrija a fonte e exporte em outra pasta.
Exemplo: “Este STL cabe na A1 mini?” Compare os tres eixos com 180 mm na orientacao atual e reserve espaco de brim/purga no fatiador.
O MVP nao detecta auto-intersecoes nem paredes finas; declare essa limitacao.
