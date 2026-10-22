# Verificacao local — versao 0.3, 21/10/2026

## Desktop 0.3

- PySide6 6.12.0 e QtWebEngine 6.12.0.140 instalados e executados em Windows x64/Python 3.12.15. Keyring 25.7.0 e PyInstaller 6.22.3 fixados no lock. A CLI continua utilizavel sem o extra desktop.
- Suite completa: **72 aprovados e 7 pulados em cada ambiente CAD**; os pulados pertencem ao outro motor. Testes Qt geram peca pelos botoes Enviar/Gerar, completam nome ausente, verificam biblioteca/miniatura/STEP, cena WebGL, arestas/normais/camera, erros e resposta do event loop durante o CAD.
- Diagnostico real em codigo-fonte gerou chaveiro TESTE, 70 x 24 x 4 mm, com STL fechado/STEP, miniatura e copia exportada dos dois formatos. A captura produzida pelo proprio teste Qt foi inspecionada e confirmou o modelo inteiro, sem corte lateral no preview. Arquivos em `.desktop-test/source-final/`, ignorados no Git.
- Gravar/ler/remover uma credencial temporaria no cofre Windows funcionou. Nao houve uso de chaves reais. Provedor API testado com respostas controladas, sem servico remoto real; depende de endpoint/modelo compativeis com JSON. Modo local usa regras, sem IA generativa.
- Empacotamento em pasta **gerado e executado com sucesso nesta maquina**, usando apenas build123d/OCP 8, sem CadQuery/VTK: `dist/BambuAIStudio/BambuAIStudio.exe`. Diagnostico do binario sem console retornou codigo 0: interpretacao pelo chat, geracao real de chaveiro TESTE 70 x 24 x 4 mm, miniatura/biblioteca, STL fechado, STEP e copia exportada dos dois formatos, com cena 3D confirmada e captura inspecionada. Evidencias em `.desktop-test/packaged-release/`, ignoradas no Git. Pasta completa: aproximadamente **0,90 GiB**; nao copiar somente o EXE.
- Falhas corrigidas no empacotamento: ICU do Poppler herdada pelo PATH quebrava a importacao QtCore (a receita agora usa a ICU do Windows); IPython necessario ao build123d nao pode ser excluido; recursos nativos lib3mf sao coletados. Nao foi instalado nem modificado ICU no sistema. O binario final nao tem console; `BAMBU_PACKAGE_DEBUG=1` permite build de diagnostico. Erros de inicializacao sao registrados em `%LOCALAPPDATA%/BambuAIStudio/startup-error.log`.
- Limitacoes: tres modelos parametricos, interpretacao local restrita, nenhum fatiamento/envio/impressao, perfil A1 mini/PLA fixo, sem teste em Windows limpo ou certificacao de drivers graficos. QtWebEngine/OpenCascade exigem espaco e memoria consideraveis; nao ha promessa de aplicacao pequena.

## Base CAD preservada (0.2)

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
