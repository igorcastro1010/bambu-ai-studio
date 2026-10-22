# Bambu AI Studio

MVP local para criar pecas parametricas por codigo com ajuda de prompts do Codex. CLI em Python, STL/STEP por CadQuery ou build123d, validacao com Trimesh e preview 3D offline. Perfil de referencia: Bambu Lab A1 mini, mesa nominal **180 x 180 x 180 mm**, PLA e AMS Lite.

## Instalar no Windows (PowerShell)

Requer Windows x64, Git e [uv](https://docs.astral.sh/uv/getting-started/installation/). O uv baixa o Python 3.12.15 isoladamente; nao altera seu Python 3.14. As versoes e dependencias transitivas estao fixadas em `uv.lock`.

```powershell
uv sync --locked --extra cadquery --extra dev
.venv/Scripts/python.exe -m bambu_ai doctor
.venv/Scripts/python.exe -m pytest -q
```

Nao precisa ativar o ambiente. Alternativa com Python 3.12 instalado: `py -3.12 -m venv .venv` e `.venv/Scripts/python.exe -m pip install -e ".[cadquery,dev]"` (essa alternativa fixa dependencias diretas, mas nao aplica o lock transitivo).

## Gerar, editar, visualizar e validar

```powershell
.venv/Scripts/python.exe -m bambu_ai generate models/chaveiro.json --out exports/meu-chaveiro
.venv/Scripts/python.exe -m bambu_ai validate exports/meu-chaveiro/model.stl
Start-Process exports/meu-chaveiro/preview.html
.venv/Scripts/python.exe -m bambu_ai generate models/suporte-celular.json --out exports/meu-suporte
.venv/Scripts/python.exe -m bambu_ai generate models/placa.json --out exports/minha-placa
```

Cada geracao produz `model.stl`, `model.step`, `parameters.json`, `validation.json` e `preview.html`. Arraste para girar e role para zoom. HTML inclui o Plotly e funciona sem internet. Para visualizar outro STL: `python -m bambu_ai preview arquivo.stl --out exports/arquivo.html` usando o Python do ambiente.

Edite uma copia do JSON para mudar nome e medidas; execute em **nova pasta**. Saidas existentes sao preservadas. Flags: `--stl-only` e `--no-preview`. Falhas de validacao impedem publicar os arquivos. Os arquivos demonstrativos ja gerados estao em `exports/demo/`. Os HTML estao disponiveis nesta instalacao, mas sao ignorados no Git; depois de clonar, gere um com `preview`.

Prompts para Codex neste repositorio:
- “Use personalizacao para criar um chaveiro ANA de 60 x 24 mm e valide o STL.”
- “Use modelagem-3d para alterar a largura do suporte para 65 mm.”
- “Use preparacao-bambu para revisar esta placa em PLA; nao iniciar impressao.”

As cinco skills estao em `.agents/skills/`; `AGENTS.md` orienta economia de contexto e reutilizacao. Nao ha API de IA embutida, chave paga ou interpretador automatico de prompts: o Codex edita parametros/codigo e executa os comandos.

## Motores opcionais

CadQuery 2.8.0 usa OCP 7.9; build123d 0.13.0 usa OCP 8.0. **Nao instalar os dois no mesmo ambiente.** Para build123d:

```powershell
$env:UV_PROJECT_ENVIRONMENT = '.venv-build123d'
uv sync --locked --extra build123d --extra dev
Remove-Item Env:UV_PROJECT_ENVIRONMENT
.venv-build123d/Scripts/python.exe -m bambu_ai generate models/chaveiro.json --backend build123d --out exports/chaveiro-b123d
.venv-build123d/Scripts/python.exe -m pytest -q
```

OpenSCAD e um aplicativo externo gratuito, independente do Python. Instale pela [pagina oficial](https://openscad.org/downloads.html) ou `winget install --id OpenSCAD.OpenSCAD -e`. Se necessario, configure o caminho:

```powershell
$env:OPENSCAD_PATH = 'C:\Program Files\OpenSCAD\openscad.com'
.venv/Scripts/python.exe -m bambu_ai render-scad models/placa.scad --out exports/placa-scad
```

O adaptador aceita `.scad` local confiavel e gera STL validado + preview; nao oferece STEP pelo OpenSCAD. Ausencia do aplicativo nao impede os outros motores.

## Bambu Studio e 3MF

Instale o [Bambu Studio oficial](https://github.com/bambulab/BambuStudio). Integracao limitada a abrir um arquivo local:

```powershell
$env:BAMBU_STUDIO_PATH = 'C:\Program Files\Bambu Studio\bambu-studio.exe'
.venv/Scripts/python.exe -m bambu_ai open-studio exports/meu-chaveiro/model.stl
```

No Studio, selecione A1 mini e PLA, centralize a peca, confira as camadas, brim/purga e suportes. Para **3MF de projeto**, use **Salvar projeto** e confira reabrindo no Studio. O MVP nao gera 3MF, G-code nem transmite para a impressora; nunca inicia impressoes. STL nao armazena cores; a atribuicao de ate quatro filamentos do AMS Lite e manual no Studio.

## Limites e estrutura

A triagem verifica malha fechada, orientacao de faces, volume positivo, faces degeneradas, um componente e dimensoes na orientacao atual. Nao verifica auto-intersecoes, paredes minimas, encaixes, estabilidade ou resistencia. A estimativa de balancos nao substitui o fatiador. STL assume mm. O limite nominal nao reserva margem para brim/purga. Os exemplos sao prototipos para conferir antes do uso, com texto em Arial e suporte de celular macico.

`src/bambu_ai/`: contrato, motores, pipeline, validacao, preview e integracoes. `models/`: parametros/fontes. `exports/`: gerados. `tests/`: testes de malha, geracao e comandos. `docs/compatibilidade.md`: versoes e verificacao local.

Referencias oficiais: [CadQuery](https://github.com/CadQuery/cadquery), [build123d](https://github.com/gumyr/build123d), [OpenSCAD](https://github.com/openscad/openscad), [Trimesh](https://github.com/mikedh/trimesh), [Bambu Studio](https://github.com/bambulab/BambuStudio). Nenhum repositorio de referencia foi clonado.
