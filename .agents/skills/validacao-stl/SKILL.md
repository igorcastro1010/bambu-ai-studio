---
name: validacao-stl
description: Verificar um STL local quanto a malha fechada, componentes, volume, dimensoes e limite nominal da A1 mini.
---

Use ao receber STL ou depois de alterar geometria. Nao tratar aprovacao geometrica como garantia de impressao.

```powershell
.venv/Scripts/python.exe -m bambu_ai validate exports/chaveiro/model.stl
```

Leia `valid`, `errors`, `warnings`, dimensoes, volume, componentes, `boundary_edges` e `nonmanifold_edges`. Codigo de saida 1 significa reprovacao; 2 significa falha de entrada/execucao.
STL usa mm por convencao. Nao reescale ou repare silenciosamente; corrija a fonte e exporte em outra pasta.
Exemplo: “Este STL cabe na A1 mini?” Compare os tres eixos com 180 mm na orientacao atual e reserve espaco de brim/purga no fatiador.
`wall_analysis` estima cordas internas em ate 128 faces por raios nas normais. Amostras abaixo de 0,8 mm geram alerta, sem reprovar `valid`. `--wall-threshold 1.2` altera o limiar em mm. Ausencia de alerta nao garante paredes adequadas: detalhes pequenos/obliquos podem escapar. Malhas abertas nao recebem estimativa de paredes. Nao detecta auto-intersecoes nem garante espessura minima.
