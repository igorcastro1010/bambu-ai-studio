---
name: otimizacao-impressao
description: Revisar orientacao e indicios de suportes de uma peca para PLA na A1 mini, com confirmacao no fatiador.
---

Use quando pedirem menos suportes, melhor orientacao ou economia de material.
Leia `validation.json`: dimensoes, volume e `overhang_area_mm2_estimate`. A estimativa usa normais descendentes >45 graus e exclui a base; nao simula pontes nem camadas.
Priorize base plana e contato amplo, considerando a direcao de carga e acabamento. Compare alternativas gerando pastas separadas.
PLA: comece pelo perfil oficial do filamento no Bambu Studio; camada de 0,20 mm pode ser ponto inicial, nao garantia de qualidade.
Exemplo: “O suporte precisa de suporte?” Confira o preview e as camadas no fatiador. O encosto macico dos exemplos privilegia geometria sem grandes balancos e consome mais PLA.
Nunca prometa tempo, massa, resistencia, ausencia de suportes ou parametros termicos sem fatiamento/ensaio. Nao iniciar impressao.
