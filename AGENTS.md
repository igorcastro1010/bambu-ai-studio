# Bambu AI Studio

- Leia primeiro README.md e apenas os modulos/skills relacionados ao pedido. Use `rg`; evite varrer dependencias e `uv.lock`.
- Reutilize `ModelSpec`, os motores em `cad.py` e o pipeline. Prefira funcoes pequenas e imports CAD sob demanda.
- Todas as medidas em mm. A1 mini: 180 x 180 x 180 mm; PLA como referencia. Preserve margem para brim/purga no fatiador.
- Para personalizacao simples, prefira `create` com opcoes legiveis ou JSON em `models/`; altere Python apenas quando a geometria exigir. Nunca execute codigo baixado sem inspecao.
- CadQuery e build123d usam ambientes separados (bindings OCP diferentes). Nao instale ambos no mesmo ambiente.
- Gere em uma nova pasta de `exports/`. Valide o STL antes de concluir; nao repare nem sobrescreva arquivos silenciosamente.
- Alertas `wall_analysis` sao estimativas por amostragem, nunca garantia de espessura ou impressao. `valid` nao certifica imprimibilidade.
- STL nao preserva unidades/cores; STEP somente com motor CAD. 3MF de projeto: salvar manualmente no Bambu Studio.
- Nunca iniciar impressao, enviar comandos a impressora ou alegar fatiamento/AMS automatico. `open-studio` apenas abre arquivo.
- Testes: `.venv/Scripts/python.exe -m pytest -q`. Rode testes do motor alternativo no ambiente correspondente quando afetado.
- Relate motor, dimensoes, arquivos gerados, testes e limitacoes. Evite copiar manuais ou criar abstracoes sem uso.

Skills locais: `.agents/skills/`. Leia apenas a que corresponde ao pedido.
