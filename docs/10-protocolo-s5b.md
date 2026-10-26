# S5B — protocolo adotado, revisão 02

Decisões do projeto autorizadas pelo pedido S5B, sem atribuição ao orientador. A proposta S5A e seu suplemento permanecem preservados. O contrato executável separado está em [experiment_s5b.json](../core/configs/experiment_s5b.json), com [schema](../core/configs/experiment_s5b.schema.json). A revisão 2 suporta um perfil fechado: campos desconhecidos, valores diferentes, booleanos numéricos e alterações silenciosas exigem rejeição ou nova revisão explícita. Identidade do protocolo não substitui verificação de dados, alvos, modalidade, cobertura, recursos e fluxo testado.

## Hipóteses preservadas

- H1: a fusão lexical + semântica tem F1 macro maior que cada motor isolado (ablação, como A6 e A9).
- H2: o siamês ajustado tem Spearman maior que o SBERT sem ajuste no teste sintético.
- H3: o sistema mantém a latência p95 dentro de uma meta sob uma carga definida (metas pendentes).

Treino/validação exploratórios não confirmam essas hipóteses. Escopo adotado: descrição do conjunto finito anotado, referência automatizada dependente, um componente conservador por split, sem bootstrap ingênuo ou intervalo populacional. Formatos não são observações adicionais. H2 original mantém limitação por ausência de referência independente; isso não bloqueia por si só o estudo exploratório autorizado.

## Dados e anotação

Dataset operacional `fccdffc984dca0b30d9c044ee62bee32eb52b3b4a828fe454e6a17de0602fd26`, IDF de treino `9ddb353e50c050f58cc3417f8a41763867550730e7c18c56851d4f6dd74680c6`, sem alteração dos dados congelados. IDF validado em integridade e vínculo com entradas; recomposição lexical C não executada novamente nem rebatizada a partir de hashes.

[Rubricas adotadas](../core/artifacts/s5b-01/rubrics.md), [plano anterior às notas](../core/artifacts/s5b-01/campaign-plan.json), [seleção](../core/artifacts/s5b-01/selection-private.json) e [cobertura](../core/artifacts/s5b-01/coverage.json). Seleção determinística por metadados de construção, sem escores, com 16 células método/severidade, dois itens por célula em treino e um em validação, mais quatro combinações não ancestrais por split. Total36/20, sete lotes de até oito; nenhuma expansão após alvos ou métricas. Textos repetidos em combinações distintas são reportados; combinações textuais ordenadas foram deduplicadas antes de anotar. Nenhum item do teste selecionado.

Anotação efetiva pela sessão Codex, `automated_weak/shared`, sem chamada de API separada. Família de ferramenta/contexto compartilhada com curadoria anterior; independência não demonstrada. Prompts completos, textos, respostas, motivos, trechos, recibos e hashes preservados em [annotation](../core/artifacts/s5b-01/annotation/). Metadados internos de modelo, temperatura, tokens e seed de geração não observáveis não são inventados. Não houve anotador humano, consenso ou adjudicação independente. Erro de citação O040 foi corrigido antes de métricas com original preservado, sem alteração do alvo.

H1 tem32/17 alvos e4/3 ambiguidades; H2 tem28/13 alvos e8/7 ambiguidades; nenhuma exclusão. São tarefas com elegibilidade própria, compartilhada por todos os sistemas de cada comparação. H2 usa três âncoras observadas0/.75/1, com forte concentração nos extremos e apenas um .75 por split. Ausência de contradições e de âncoras .25/.5 nesta campanha limita sua cobertura; não fabricá-las. Aceitação estrutural não certifica qualidade semântica independente.

## H1

Unidade sentença-par. Classes: copia_exata, copia_editada, parafrase, sem_correspondencia_detectada. Igualdade sustenta só cópia operacional literal; não prova plágio. Continuidade de formulação com erros locais recuperáveis versus reformulação sintática/lexical delimita edição/paráfrase. Núcleo incompatível, incluindo contradição central, vai para ausência de correspondência; casos não decidíveis ficam ambiguous/null. C0–C7 e ancestralidade não são rótulos avaliativos automáticos.

Entradas: apenas dois textos. Sinais: cosseno TF-IDF experimental L, cosseno bruto SBERT S, fusão fixa `.4L+.6max(0,S)`. Três regressões logísticas multinomiais da mesma família, um escalar sem padronização por sistema, L2/C1, lbfgs, max_iter1000, seed20261025, sem peso de classe. Uma execução planejada, sem grade, ajuste apenas em treino. Mapeamento é a classe de maior logit; desempate pela ordem das classes exportadas. Nenhuma igualdade textual, r, ID ou classe de construção como atributo oculto. E2/E4 não são classificadores isolados neste contrato.

Matriz de confusão, suporte, precisão/recall/F1 por classe e macro-F1 nas quatro classes, inclusive ausentes (zero_division0). Mesmas observações elegíveis por sistema; falha não é omitida para produzir comparação de sucessos. Exportação JSON com coeficientes/classes/versões/identidades, sem pickle.

## H2 e siamês

Construto: grau de conteúdo proposicional compartilhado [0,1], âncoras discretas0/.25/.5/.75/1 e eixos separados de tema, relação, conteúdo e contexto. Contradição não é automaticamente zero; impede1. Equivalência1 exige preservação bidirecional dos fatos. Contexto essencial ausente implica alvo nulo. Nomes, números, unidades, negação, modalidade, tempo e causalidade são julgados pelo conteúdo, não por motores, r ou taxa de edição. Instrumento adotado pelo projeto, sem validação psicométrica alegada.

Base local fixa `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, revisão `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`, Apache-2.0. Mesmo encoder compartilhado **ajustável**,384 dimensões; concatenação `abs(u-v),u*v`,768→128→1, LayerNorm epsilon1e-5, LeakyReLU .1, dropout .1, sigmoid. MSE/Adam, lr2e-6, weight_decay1e-5. Camadas e dimensões são decisões do projeto, não parâmetros atribuídos ao A7. Evidência primária anterior em [primary-a7.json](../TCC/evidencias/codex-s5a-01/primary-a7.json): arquitetura PDF6–7 e tabela1 PDF9, parâmetros efetivamente encontrados. Não importamos212tokens como limite do modelo local.

Baseline: mesmo SBERT anterior às atualizações. Spearman é a métrica principal da hipótese, com empates por postos médios e indefinição explícita; MSE de validação seleciona o checkpoint, menor valor e empate pela época mais antiga. Diagnósticos do baseline usam `(cos+1)/2`; postos equivalentes aos do cosseno bruto. Patience2épocas, até8épocas, sem escolha de seed. Um encoder congelado/cabeça treinada seria intervenção diferente e não é substituição silenciosa permitida.

Janelas: limite efetivo mínimo entre modelo/tokenizador/posições; local128, com capacidade descontando especiais. Cobertura integral, sem sobreposição, média ponderada por tokens de conteúdo e normalização L2 diferenciáveis. Mais de12000tokens é erro explícito, não truncamento nem exclusão posterior por desempenho. Não há NumPy/detach/no_grad no caminho treinável. Validação/baseline usam eval/no_grad, sem reutilizar embeddings anteriores após atualização.

## Recursos, orçamento e retomada

CPU2threads, microbatch1, acumulação4; último grupo dividido pelo seu tamanho real. Até2000atualizações ou7200segundos incluindo laço/validação, RSS3GiB amostrado nas fronteiras dos grupos e durante validação, disco6GiB para checkpoints, uma tentativa planejada. Preparação de sinais/baseline tem teto separado600s. Esses são limites operacionais escolhidos, não duração prevista nem mínimo de hardware demonstrado. Monitor amostrado não é contenção instantânea de todo pico. Não se usa consumo de treino como benchmark H3.

Antes de carregar a base: memória física disponível mínima escolhida2GiB para H1 e4GiB para encoder ajustável H2. Fundamentação conservadora: arquivo de pesos449MiB, parâmetros/gradientes/momentos Adam perto de1.8GiB antes de ativações/runtime, com reserva. Esses valores não são benchmark de uso efetivo. Fotografia real e decisão por tarefa ficam nos recibos de prontidão; sem matar processos para caber.

Checkpoints próprios, pesos safetensors, estado local de Adam/RNG Python/NumPy/Torch carregado com weights_only=True, sem scheduler. Salvamento atômico em fronteira sem gradiente pendente, ao fim de época e parada segura; ordem/cursor, histórico, seleção, orçamento e identidades preservados. Manifesto verifica bytes/componentes e conflito de vínculos. Arquivos próprios locais somente; hash não autentica origem adversarial. Exceções preservam último checkpoint seguro e registro de falha; retomada só da mesma execução compatível. Limite terminal não se estende por resume. Nenhuma promessa de igualdade entre ambientes; identidade exata é testada apenas no fixture local pequeno. Limite de disco pode impedir novo checkpoint: resultado parcial registra isso e preserva os anteriores.

## H3, aplicação e teste

H3 continua em protocolo separado, sem carga real nesta S5B. Nenhum modelo, IDF, limiar ou classificador novo é ativado na aplicação. Contrato de integração futura: dois textos com o mesmo pré-processamento, referências explícitas de base/pesos/protocolo/IDF/rubrica e classes, um escalar H2 ou classe H1, falha explícita quando recurso/versão incompatível, sem fallback silencioso para modelo diverso. Integração e compatibilidade reais com a aplicação exigem etapa própria.

Executor S5A mantém recusa. CLI S5B oferece apenas readiness/run para H1/H2, constrói entradas somente de train/validation e recusa linhas test; não há comando de inferência de teste. Isso reduz risco, não comprova ausência universal de vazamento. S5C/S5D exigem pedido próprio, modelos congelados e gabarito compatível. Esta sessão não abre o teste final.


## Retomada — retenção revisão02 (decisão do projeto)

O protocolo executável é hts-s5b-2. Revisão01 original preservada em [before.zip](../TCC/evidencias/codex-s5b-retomada-01/before.zip) e no pacote S5B original; não reescreve execução passada. Arquitetura, rubricas, limites de memória/disco, seeds e seleção preservados. [Relatório e antes/depois](../TCC/evidencias/codex-s5b-retomada-01/relatorio-final.md).

Retenção latest-and-selected-owned-v2: quando latest=selected, um checkpoint; quando diferentes, dois. Raiz e inventário autoritativos por execução lógica, run_id/bindings/política/manifestos e segmentos de retomada registrados. O orçamento6GiB soma arquivos de todos os segmentos, inclusive temporários interrompidos e desconhecidos; não reinicia em novo destino. Estimativa inicial4×bytes do state_dict+1MiB, confrontada com1,1×maior tamanho observado+64KiB e espaço físico livre, usando o maior. Tetos não foram aumentados.

Gravar temporário próprio → verificar hashes/componentes e carregamento → publicar diretório → publicar registro atômico e espelhos latest → rotacionar somente intermediários próprios íntegros, com ledger. Nunca apagar selected/latest, arquivos desconhecidos/históricos ou seguir links/reparse points. Falha na transição preserva estados anteriores; pré-recusa de disco registra partial/checkpoint_disk_limit e não seleciona candidato não salvo. Conflitos e resíduos são preservados e contabilizados. Registry é autoridade para recuperar publicação interrompida antes do espelho; conferir claim, bindings, raiz e integridade. Checkpoint legado não é automaticamente incorporado à rotação. Hash não autentica origem.

Verificação atual:409testes oficiais, fixture antes5épocas/cinco checkpoints e depois8épocas/um checkpoint no mesmo2MiB. Esses números são software artificial, não treinamento de pesquisa. Preflight real aceitou contratos/dados/IDF A/B, mas recusou H1/H2 antes da base por memória. Nenhum modelo real ou métrica de validação foi produzido; não há mudança na validade científica ou abertura do teste. [Próximo comando](../TCC/evidencias/codex-s5b-retomada-01/README-reproducao.md).


## Operação vigente — Docker com stack completa

S5B permanece parcial, sem treinamento real. O ajuste atual exige MongoDB/core/web ativos e saudáveis no alcance de seus checks, processo experimental separado e saídas persistentes. Usar [Compose S5B](../docker-compose.s5b.yml) e [launcher host](../core/scripts/run_s5b_docker.py); este executa somente Docker para as operações experimentais. Código/dados/modelo ro, campanha rw para claim, resultados no host. Não substituir por treino Python local, não parar serviços nem reduzir reservas.

Disponibilidade efetiva é o mínimo de MemAvailable da VM, limit-current de cada ancestral cgroup exposto e snapshot físico host fresco fornecido pelo launcher; snapshot>120s/futuro/inválido falha. Ancestrais ocultos pelo namespace não são observados. Docker Memory0 e memory.max=max não significam memória infinita: VM3763134464bytes; H1/H2 bloqueados887087104/709214208 versus2/4GiB. Nenhuma configuração global alterada. Saúde e tempos de readiness não são H3. [Relatório e comandos](../TCC/evidencias/codex-s5b-docker-01/README-reproducao.md). As execuções anteriores acima permanecem históricas.


## Auditoria integrada Docker vigente

[Relatório](../TCC/evidencias/codex-s5b-docker-01/relatorio-final.md) e [gate](../TCC/evidencias/codex-s5b-docker-01/matriz-prontidao-s5c.md): S5A verificada no alcance auditado; S5B ainda sem treino real por recursos. Contratos científicos não modificados retrospectivamente. S5A continua recusando treino; S5B usa fluxo próprio. Teste final e S5C não executados. Falhas de export H1/manifest corrigidas e testadas; carregamento real depende de modelos ainda ausentes.


## Verificação vigente da conclusão S5B

[Relatório atual](../TCC/evidencias/codex-s5b-conclusao-01/relatorio-final.md): IDF A/B/C executado com diferença de lock global explícita e df integral igual; modo padrão permanece estrito, parâmetros científicos/IDF não alterados. Readiness03 H1/H2 continua bloqueado por recurso; nenhum treinamento real. [Preparação futura da referência S5C](12-plano-referencia-final-s5c.md), não executada. Históricos acima preservados.
