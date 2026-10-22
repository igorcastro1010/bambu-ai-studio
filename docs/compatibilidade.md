# Verificacao local — versao 0.2, 21/10/2026

Windows x64; Python 3.12.15 gerenciado pelo uv. Python 3.14 original preservado. Resolucao por metadados oficiais do PyPI antes da instalacao; `uv.lock` inclui versoes transitivas e hashes. `uv pip check` aprovou os dois ambientes.

| Componente | Versao verificada | Estado |
| --- | --- | --- |
| CadQuery | 2.8.0 / cadquery-ocp 7.9.3.1.1 | Instalado em `.venv`; tres exemplos STL/STEP testados, STEP reimportado |
| build123d | 0.13.0 / cadquery-ocp-novtk 8.0.1.1.0 | Instalado em `.venv-build123d`; tres exemplos STL/STEP testados, STEP reimportado |
| Trimesh / NumPy / SciPy | 5.1.1 / 2.5.4 / 1.18.1 | Instalados e testados em ambos |
| Plotly | 7.1.0 | HTML offline gerado; modos de faces, transparencia, normais, vistas e dimensoes testados na configuracao da figura |
| pytest | 9.1.1 | 49 testes aprovados e 7 pulados em cada ambiente; os pulados pertencem ao outro motor CAD |
| OpenSCAD | 2021.01 | Ja instalado em `C:\Program Files\OpenSCAD`; renderizacao real de `models/placa.scad` aprovada |
| Bambu Studio | FileVersion 02.08.03.66 | Ja instalado em `C:\Program Files\Bambu Studio`; abertura testada apenas com subprocesso simulado; sem fatiamento/envio |

CadQuery depende de OCP <8 e build123d de OCP >=8 nas versoes escolhidas. Os pacotes compartilham o namespace `OCP`; ambientes separados sao obrigatorios. O lock declara os extras como conflitantes. Bibliotecas CAD carregadas sob demanda.

Artefatos demonstrativos em `exports/demo/`: chaveiro 70 x 24 x 4 mm; placa 120 x 35 x 4 mm; suporte 60 x 70 x 55 mm; chaveiro alternativo build123d; placa OpenSCAD 100 x 30 x 4 mm. Todos com STL fechado, componente unico, volume positivo e dimensoes nominais compativeis. HTML gerado localmente e ignorado no Git para evitar copiar o bundle Plotly repetidamente; regenere com o comando `preview` em uma nova instalacao.

Na versao 0.2, `create` reutiliza o mesmo pipeline com parametros legiveis, sem JSON. Testes adicionais cobrem geracao real em ambos os motores, parametros incompativeis, limites por eixo, bordas abertas/nao manifold e paredes amostradas (incluindo base local fina e peca rotacionada). Nenhuma dependencia foi adicionada. Demonstracao nova: `exports/demo/v02-chaveiro/`, 80 x 24 x 4 mm; STL fechado, um componente, sem bordas abertas. O relevo recebeu um alerta de corda interna amostrada de aproximadamente 0,71 mm, sem tratar isso como espessura minima certificada. Geracao alternativa build123d verificada em `exports/v02-build123d/` (ignorada no Git).

O navegador de automacao bloqueou `file://` na verificacao inicial; a renderizacao/interacao visual do HTML permanece sem verificacao manual. Abertura pelo navegador local e documentada no README. A triagem geometrica nao comprova qualidade de impressao ou resistencia e nao detecta auto-intersecoes. Paredes agora possuem apenas estimativa por amostragem, sem garantir espessura minima ou ausencia de detalhes finos. Nenhuma impressao foi iniciada. 3MF de projeto depende do salvamento e da revisao manual no Bambu Studio; nao ha exportador 3MF no MVP.

GitHub CLI autenticado; repositorio publico criado por solicitacao explicita do usuario: [igorcastro1010/bambu-ai-studio](https://github.com/igorcastro1010/bambu-ai-studio). Remoto `origin` configurado para `https://github.com/igorcastro1010/bambu-ai-studio.git`.

Fontes consultadas: [metadados CadQuery](https://pypi.org/pypi/cadquery/2.8.0/json), [metadados build123d](https://pypi.org/pypi/build123d/0.13.0/json), [Trimesh](https://github.com/mikedh/trimesh), [OpenSCAD para Windows](https://openscad.org/downloads.html), [Bambu Studio](https://github.com/bambulab/BambuStudio), [A1 mini e AMS Lite](https://us.store.bambulab.com/products/a1-mini). Consulte o lock para a resolucao exata; disponibilidade futura dos pacotes externos nao e garantida.
