# S5B — entrada após o complemento S5A

<!-- S5B-CURRENT -->
## Estado vigente — S5B, 2026-10-25

Este prompt foi atendido no alcance de engenharia/anotação e guard de execução real; consultar protocolo/relatório/checkpoint S5B. Para retomar, usar os artefatos preservados, não reiniciar campanha. S5C não iniciada.

[protocolo](../docs/10-protocolo-s5b.md) | [relatório](../TCC/evidencias/codex-s5b-01/relatorio-final.md) | [matriz](../TCC/evidencias/codex-s5b-01/matriz-entrega.md) | [checkpoint](../TCC/evidencias/codex-s5b-01/checkpoint.md)

Os registros anteriores abaixo descrevem os estados de suas respectivas etapas; não são bloqueios vigentes por omissão desta S5B.
<!-- /S5B-CURRENT -->

## Estado vigente: prompt preparado, sem autorização automática

Leia [protocolo revisão2](08-protocolo-s5a.md), [referência preservada](../core/configs/experiment_s5a.json), [suplemento candidato](../core/configs/experiment_candidates_s5a.json), [relatório](../TCC/evidencias/codex-s5a-complemento-01/relatorio-final.md), [matriz](../TCC/evidencias/codex-s5a-complemento-01/matriz-prontidao.md) e checkpoint. O prompt anterior está preservado no arquivo documental da sessão. Sua presença não autoriza treino, serviço pago, upload, carga ou teste preditivo.

## Pedido para futura sessão expressamente autorizada

Continue do estado local sem reabrir S4 nem descartar S5A/complemento. Leia AGENTS/guia/mapa/TCC00/14. Registre diretório, HEAD/branch, alterações staged/unstaged/novas e inventário privado. Não iguale checkout ao remoto. Sem commit/push/tag/PR/publicação/remoção de volumes. Crie evidências/checkpoint novos, preserve tentativas falhas. Uma tarefa pesada por vez; inspecione processos/serviços sem encerrar desconhecidos.

Primeiro confira a tarefa e contratos realmente adotados. O complemento corrigiu schemas de protocolo, vínculo A/B do IDF, tipos/procedência de anotações e consumidores. Isso não supriu gabarito nem aprovou propostas científicas.

1. H1: adotar/revisar classes e unidade sentence_pair, exemplos/fronteira edição-paráfrase, elegibilidade e regra comum de saída. Proposta: características escalares L/S/fusão fixa e classificadores logísticos da mesma família treinados somente no treino. Alternativa: regras fixas por baseline com mapeamento anterior aos resultados. Isso exige decisão documentada, não faz de E2/E4 classificadores. Obter/importar classes reais compatíveis; havia zero no complemento. C0–C7 não são gabarito avaliativo.
2. H2: escolher explicitamente construto e rubrica. Recomendação candidata: conteúdo proposicional compartilhado com eixos de tema/relação/contradição/contexto, schema hts-annotations-2. Contradição não equivale automaticamente a zero; insuficiência de contexto exige alvo nulo. Há zero alvos semânticos. Preferir anotação independente compatível se recurso real existir; alternativa automatizada/fraca exige alcance limitado e dependências declaradas. r é outra tarefa, não solução de H2. Não inventar pessoas, consenso ou independência, nem campanha extensa antes do desenho.
3. Estatística: um componente por split. Recomendação: descrição do conjunto finito sem intervalo populacional indevido. Alternativas: novo desenho prospectivo separado ou inferência dependente justificada. Não bootstrap por linha/fonte focal nem seleção pelo desempenho; preservar versão atual.
4. Siamês: adotar arquitetura/base/revisão/licença/cobertura e orçamento antes de implementar laço. Recomendação alternativa ao BERTimbau histórico: mesmo SBERT local fixado do baseline,384dims,concat(absdiff,produto),cabeça768→128→1; detalhes no suplemento. São escolhas do projeto, não parâmetros ausentes do A7. Teto candidato CPU2threads/microbatch1/acum4/8épocas/2000updates/7200s/3GiB/1tentativa; seleção MSEval/empateépocamaisantiga/parada2épocas. Confirmar recursos livres antes de qualquer execução: fotografia de memória disponível era inferior ao teto, sem promessa de viabilidade ou duração. Modeloconfig128tokens/janela completa, não importar212tokens de A7 como política local.
5. H3: só proposta e instrumentação. Adotar meta/cenário/recursos antes de medir: p95HTTPsucessos≤2s E falhas/tentativas=0, não ocultar timeout/falha. Carga real depende de autorização própria posterior. RSS/tracemalloc/pico não são equivalentes.

Se faltar requisito essencial, não treinar. Executar apenas preparação/anotação que a nova sessão autorize, entregar a alternativa concreta e evidência, parar sem inventar gabarito ou alterar hipótese.

Se treinamento for explicitamente autorizado e todos os vínculos estiverem satisfeitos, produzir nova revisão de protocolo adotado preservando candidatos. Implementar/testar fluxo próprio; não retirar a recusa S5A apenas para passar. Exigir dataset/rótulos/rubrica/protocolo/modelo/config/métricas/seeds/repetições/orçamento/código e evidência da autorização, não approved=true isolado. Registrar todas as tentativas/limites/falhas; seleção só na validação; não escolher seed vencedora.

Checkpoint real inclui pesos/otimizador/RNG/posição/histórico/parada/integridade/compatibilidade. O checkpoint S5A é somente de preparação. Testes de software não autorizam nem substituem treino real. Não usar metadados de origem/split/classe/alvo como entrada de inferência.

Dataset fccdffc984dca0b30d9c044ee62bee32eb52b3b4a828fe454e6a17de0602fd26 e IDF9ddb353e50c050f58cc3417f8a41763867550730e7c18c56851d4f6dd74680c6 preservados. Preflight leve verifica Aintegridade e Bcontrato/vínculo; Clexical não reexecutado no complemento. Se necessário, caminho explícito validar-idf, sem rotular hash como recomputação. Não ativar IDF experimental na aplicação.

Anotações podem ser armazenadas/auditadas com audit-annotations inclusive no teste, sem gerar entradas de modelo. Import-annotations seleciona só treino/validação. Não confundir armazenamento/auditoria com execução experimental. Duplicatas textuais permanecem contadas e dependentes; conflito exige adjudicação real, sem exclusão silenciosa.

**Teste final continua fechado para desempenho na S5B.** Não executar motores, medir, calibrar, selecionar exemplos/arquitetura ou abrir teste por localização/booleano. Abertura futura exige etapa e fluxo próprios. Sem S5C/S5D automáticas. Não atualizar TCC13 com fixtures ou resultados fictícios.

## Encerramento futuro

Separar engenharia, contratos candidatos/adotados, dados existentes, treinamento liberável, treinamento realmente executado e bloqueios por tarefa. Atualizar TCC00/01/02/11/12/14, checkpoint e matriz. Nenhuma aprovação de orientador ou revisão humana é presumida. Parar nas fronteiras da autorização recebida.
