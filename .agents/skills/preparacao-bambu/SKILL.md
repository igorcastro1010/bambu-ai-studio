---
name: preparacao-bambu
description: Preparar a revisao manual de STL ou STEP na Bambu A1 mini com PLA e AMS Lite, sem enviar impressao.
---

Use antes de importar/fatiar. Valide primeiro o STL correspondente e confirme 180 x 180 x 180 mm.
Base em Z minimo; centralize na mesa. Confira brim, purga e perfil A1 mini no Bambu Studio.
AMS Lite comporta ate quatro filamentos; STL nao contem cores. Atribua cores/regioes manualmente no Studio.

Exemplo: “Prepare o chaveiro para o Bambu Studio”:
```powershell
.venv/Scripts/python.exe -m bambu_ai open-studio exports/chaveiro/model.stl
```
Requer Studio instalado e `BAMBU_STUDIO_PATH` quando nao localizado. O comando so abre o arquivo.
Para 3MF de projeto, use Salvar projeto no Studio e reabra para conferir. Nunca renomeie STL para 3MF nem alegue integracao de envio. Nunca iniciar impressao automaticamente.
