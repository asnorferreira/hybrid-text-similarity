# Caminho para eventual novo estudo H1/H2

## Estado

Preparação metodológica autorizada pelo autor em 2026-10-27. **Nenhum novo
treino, calibração, seleção de exemplos ou avaliação científica foi executado.**
Este documento não substitui os protocolos r3/r4 nem reabre a avaliação P10.
As hipóteses originais continuam não sustentadas no alcance medido.

Fonte dos resultados existentes: [relatório P10](../TCC/evidencias/codex-p10-01/relatorio.md).
O [plano 16](16-plano-conclusao-e-testes.md) já foi executado no alcance adotado;
um estudo adicional é opcional para a conclusão desse plano e para a redação
de seus resultados negativos.

## Sequência recomendada

1. **Delimitar uma nova pergunta.** H1 deve comparar classificadores no mesmo
   alvo categórico/unidade; H2 deve comparar escores no mesmo construto semântico.
   Declarar se o objetivo é diagnóstico ou confirmação independente. Não renomear
   as hipóteses antigas como se tivessem sido sustentadas.
2. **Preservar o histórico observado.** Manter predições, referência, pesos,
   calibração, fontes, protocolos e hashes P7–P10. P10 passa a ser um conjunto
   já observado: nenhuma métrica adicional nele será apresentada como novo
   teste independente. Não ajustar modelo, limiar, época ou exemplos para
   melhorar suas métricas finais.
3. **Separar desenvolvimento e teste novo.** Usar train/validation para o novo
   desenvolvimento. Se desejada confirmação, reservar referência humana nova,
   com fontes/grupos de ancestralidade e duplicatas controlados em relação ao
   desenvolvimento e ao teste antigo. Verificar vazamento antes do treino e
   registrar exclusões, sem escolher o teste por resultados favoráveis.
4. **Congelar o protocolo antes de abrir o teste novo.** Definir sistemas,
   features permitidas, alvo, unidade, métricas primárias, baselines, divisões,
   seeds, número de tentativas, orçamento de CPU/memória, espaço de busca,
   critério de seleção, parada e política de resultados indefinidos. Qualquer
   adaptação posterior deve ser identificada como exploratória.
5. **Desenvolver mudanças justificadas na validação.** Primeiro diagnosticar
   desequilíbrio, tamanho efetivo, separabilidade das features e convergência.
   H1: comparar fusão aprendida com lexical, semântico, Q5-V2 e majoritária nos
   mesmos itens. H2: preservar baseline e pooling explicitamente comparáveis;
   encoder congelado/cabeça MLP e fine-tuning integral são intervenções distintas.
   Full fine-tuning/LoRA só entram se o novo protocolo e os recursos medidos os
   comportarem; não são correção obrigatória da entrega atual.
6. **Planejar anotação e inferência com a dependência correta.** Definir rubrica,
   cegamento, independência declarada, itens ambíguos, concordância e elegibilidade
   antes das respostas. Justificar tamanho pelo alcance pretendido e por fontes
   independentes; não presumir que 96 derivações equivalem a 96 observações
   independentes. Se houver intervalos/testes, definir previamente método por
   grupos e comparações, sem bootstrap ingênuo de linhas.
7. **Selar e avaliar uma vez.** Selecionar modelos apenas na validação; congelar
   referência, pesos, IDF, configuração e runner antes da avaliação. Inferir no
   teste independente uma vez, preservar todas as predições e recalcular as
   métricas a partir delas, com denominadores e falhas explícitos.

## Decisões ainda necessárias apenas se o novo estudo for iniciado

| Decisão | Recomendação | Evidência antes da execução dependente |
| --- | --- | --- |
| Objetivo científico e alcance | Começar por diagnóstico em train/validation | Protocolo novo, separado do estudo concluído |
| Referência independente | Novos grupos/fontes, avaliação cega, sem resultados de modelo no formulário | Inventário de separação, rubrica e plano de anotação |
| Quantidade e tentativas | Justificar em função da independência e recursos, sem número arbitrário neste rascunho | Desenho amostral e orçamento pré-coleta |
| H2 e pooling | Controlar a representação para poder atribuir diferenças à intervenção | Teste de equivalência do caminho de inferência |
| Fine-tuning | Só após diagnóstico e medição de viabilidade em fixture | Reserva de memória e tempo observadas em Docker/CPU |
| Calibração | Estimar derivação em campo separado, sem convertê-la em índice | Plano de validação e métricas independentes compatíveis |

Nada dessa tabela bloqueia a melhoria de engenharia da H3 ou a redação do TCC
com os resultados já obtidos. Nenhum número de desempenho novo é presumido.
