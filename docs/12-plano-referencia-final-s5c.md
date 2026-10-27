# Referência final da S5C — procedimento preparado, não executado

**Estado em 2026-10-27:** P7/P8 concluídas; PH2/D5 pendentes. O caminho B foi adotado em D1, com 80–100 pares por dois humanos. O procedimento abaixo implementa somente a alternativa histórica A, com até 24 itens automatizados, e precisa de revisão explícita para B antes de selecionar/anotar o teste. Não executar estes comandos como se já implementassem a referência humana. [Plano vigente](16-plano-conclusao-e-testes.md) e [P8](../TCC/evidencias/codex-p08-02/handoff.json).

## Histórico — contrato automatizado preparado na S5B

Este plano é uma decisão operacional preparada na S5B. Não autoriza iniciar a S5C, anotar o teste ou executar predições. O [protocolo S5B](10-protocolo-s5b.md), suas hipóteses e a [campanha existente](../core/artifacts/s5b-01/campaign-plan.json) permanecem preservados. `final_test_targets=null` continua correto nesta entrega.

## Finalidades e sequência

**A — exploração:** referência `automated_weak/shared`, julgada pela sessão de IA autorizada, com dependência em relação ao gerador/contexto registrada. Permite comparação descritiva com essa referência, sem equivalência presumida ao julgamento humano ou confirmação independente de H2.

**B — hipótese semântica original:** requer referência independente apropriada, com procedência, vínculo textual, rubrica, contexto, recursos e independência efetivamente demonstrados. Não existe recurso assim identificado nesta entrega. A ferramenta abaixo prepara somente A; B precisa de contrato próprio, mantendo os itens comparáveis e a seleção anterior às predições. Uma nova conversa/passagem não satisfaz independência. Não se exige revisão humana para concluir o treino exploratório autorizado.

Ordem obrigatória futura:

1. Concluir H1/H2, verificar carga dos modelos reais e congelar seleção, protocolo, pré-processamento, IDF, código e pesos usando somente treino/validação.
2. Obter autorização específica para preparar a referência final no alcance escolhido. Registrar a instrução real; não criar recibo de autorização por presunção.
3. Conferir identidade do plano, gerar entradas cegas, registrar exposição dos textos e executar uma campanha limitada sem consultar predições.
4. Preservar respostas, importar pelo schema adequado, verificar cobertura e coerência, resolver problemas operacionais sem métricas conhecidas e congelar referência/IDs/decisões/hashes. Registrar todas revisões e dependências; não chamar passes dependentes de revisão independente.
5. Somente com autorização própria de avaliação, protocolo final adotado e todos gates satisfeitos, abrir o teste para uma execução. Nenhuma mudança posterior em modelo, alvo, seleção ou hiperparâmetro para favorecer o resultado. Resultados desfavoráveis permanecem.

## Seleção fixada antes das predições

[Plano legível por máquina](../core/configs/reference_s5c.plan.json), seed 20261025, unidade `sentence_pair`, fonte e suspeito ordenados, dataset congelado `fccdffc984dca0b30d9c044ee62bee32eb52b3b4a828fe454e6a17de0602fd26`. Somente split test será selecionado **na preparação futura**, ainda não feita. Os 115 pares documentais históricos não são 115 observações independentes, nem formatos adicionais são novas observações.

Algoritmo implementado: agrupar pares por método/severidade; ordenar células; selecionar uma combinação textual por célula. Dentro da célula, ordenar pares/sentenças pelo SHA-256 da seed e IDs; preferir sentença focal ancestral, quando houver. Adicionar quatro combinações de sentenças sem ancestralidade direta, de fontes declaradas no próprio par. Ancestralidade serve apenas à cobertura, nunca como alvo. Deduplicar globalmente hashes dos pares textuais ordenados. Não consultar escores, rótulos sintéticos como respostas, perdas ou métricas. Isso inclui negativos de construção fáceis/difíceis quando existirem e relações potencialmente ambíguas; não garante que todas classes avaliativas estejam presentes.

Teto 24 observações, lotes≤8, no máximo 3 lotes iniciais. Tamanho efetivo depende das células reais; não foi contado pela abertura dos textos de teste nesta sessão. Se a cobertura ultrapassar o teto ou não puder ser preenchida sem duplicatas, a ferramenta recusa antes de publicar o destino. Não ampliar depois dos rótulos ou métricas. Não substituir itens ambíguos para preencher classes. O desenho é operacional, sem alegação de suficiência estatística.

## Rubricas, contexto e qualidade

Reutilizar exatamente os [bytes da rubrica S5B](../core/artifacts/s5b-01/rubrics.md), cujo hash consta no plano, sem mudar H1–H3. H1: cópia exata, cópia editada, paráfrase, sem correspondência detectada; continuidade de formulação versus reformulação proposicional define a fronteira editada/paráfrase. H2: âncoras 0/.25/.5/.75/1 e eixos temático/proposicional/conteúdo/contexto; negação, números, unidades, entidades, omissões, causalidade e modalidade precisam de julgamento textual explícito. Não calcular notas por edição, r ou motores. Contexto permitido: as duas sentenças completas; se insuficiente, ambiguous/alvo nulo. Corrupção irrecuperável: excluded, motivo e original preservados. Contradição não equivale automaticamente a zero; nota 1 exige equivalência sem contradição relevante.

Prompts cegos contêm só ID de observação, dois textos e rubrica; método, ancestralidade, split e escores ficam fora da entrada do avaliador. Registrar prompts completos, respostas reais, data, modalidade, relação com gerador, justificativas, trechos e hashes. Uma resposta planejada por lote; não regenerar até obter nota conveniente. Se houver falha estrutural, preservar original e permitir no máximo uma correção operacional rastreável antes de qualquer predição; conflito sem solução fica ambiguous. Não inventar versão interna, seed/temperatura de geração, tokens ou revisão humana.

Relatório obrigatório: selecionados/anotados/válidos/ambíguos/excluídos, textos e pares únicos, fontes/temas/métodos/estratos, classes/notas/empates, conflitos e exposição. H1 conserva as quatro classes na macro-F1, inclusive suporte ausente e zero_division=0 declarado; universo não muda após métricas. A comparação final planejada exige≥ 8 itens H1 válidos, classes ausentes explicitadas e sem afirmação de cobertura completa. H2 exige≥ 8 válidos e pelo menos 2 alvos distintos para a correlação planejada; alvo ou predição constante resulta em Spearman nulo com motivo, jamais zero inventado. Esses limites são decisões operacionais, não tamanhos cientificamente suficientes. Se falhar elegibilidade, reportar insuficiência; não expandir após desempenho. Uma componente conservadora por split: estatística descritiva do conjunto finito, sem intervalo populacional por bootstrap de linha/fonte focal.

## Comandos preparados

Conferência do plano, permitida nesta S5B: não abre dataset, não produz notas.

```powershell
docker compose -f docker-compose.s5b.yml -p hts-s5b-docker run --no-deps training python scripts/prepare_s5c_reference.py --plan configs/reference_s5c.plan.json --check-plan-only
```

**Não executar agora.** Depois de autorização separada, criar um registro com os campos exatos abaixo, vinculando uma instrução real. Hash é o emitido pela conferência do plano; não preencher referência de usuário fictícia. O arquivo deve ficar no diretório persistente de saídas do Compose. Esta estrutura não substitui autorização real nem autentica sua origem por si só.

```json
{
  "action": "prepare_final_reference_inputs",
  "plan_identity": "HASH_REAL_DO_PLANO",
  "user_instruction_ref": "REFERENCIA_DA_INSTRUCAO_REAL_FUTURA",
  "predictions_authorized": false
}
```

Preparação futura de entradas vazias, ainda sem alvos, usando destino novo:

```powershell
docker compose -f docker-compose.s5b.yml -p hts-s5b-docker run --no-deps training python scripts/prepare_s5c_reference.py --plan configs/reference_s5c.plan.json --authorization-record /s5b-output/s5c-reference-authorization.json --dataset artifacts/s4-fechamento-01/frozen-curated-01 --out /s5b-output/s5c-reference-inputs-01
```

A ferramenta valida protocolo/rubrica/versão, sela seleção e inputs por hashes e registra exposição. Não anota, não treina, não calcula features/predições e não produz `selected_model`. Após os julgamentos reais, preservar os bundles H1 e H2 com schemas existentes e usar o comando existente `experiment audit-annotations --split test` para validação estrutural em destino novo, não o importador experimental S5A fechado para test. A importação/auditoria não autoriza inferência. O executor final preditivo continuará pendente de protocolo S5C próprio; não há comando de avaliação final liberado nesta entrega.

Congelamento futuro: inventário SHA-256 de todos inputs/respostas/bundles/recibos/revisões/rubrica/protocolo/modelos, contagens e gates por tarefa, timestamp, modalidade e autorização de abertura. Qualquer revisão posterior ao congelamento exige motivo e nova identidade, preservando anterior; após métricas, não substituir silenciosamente o resultado. Referência final só passa a existente quando esses arquivos reais existirem e forem verificados.
