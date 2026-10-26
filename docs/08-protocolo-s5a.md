# Protocolo S5A — complemento candidato, revisão 2

<!-- S5B-CURRENT -->
## Estado vigente — S5B, 2026-10-25

S5A permanece histórica e seu executor mantém recusa de treino. A adoção exploratória e o fluxo posterior pertencem ao protocolo S5B separado; não retroagir autorização à S5A.

[protocolo](../docs/10-protocolo-s5b.md) | [relatório](../TCC/evidencias/codex-s5b-01/relatorio-final.md) | [matriz](../TCC/evidencias/codex-s5b-01/matriz-entrega.md) | [checkpoint](../TCC/evidencias/codex-s5b-01/checkpoint.md)

Os registros anteriores abaixo descrevem os estados de suas respectivas etapas; não são bloqueios vigentes por omissão desta S5B.
<!-- /S5B-CURRENT -->

## Estado vigente

O complemento corrige contratos de preparação; não libera treino, calibração, carga ou desempenho no teste. S4 permanece encerrada no alcance operacional. A [configuração original](../core/configs/experiment_s5a.json) foi preservada; o [suplemento candidato](../core/configs/experiment_candidates_s5a.json) acrescenta propostas completas, **não adotadas nem executáveis para treino**. O preflight vincula ambas as identidades. Hash identifica conteúdo, não aprovação científica.

A versão anterior dos documentos alterados foi preservada byte a byte em [documentacao-anterior.zip](../TCC/evidencias/codex-s5a-complemento-01/documentacao-anterior.zip), com [inventário](../TCC/evidencias/codex-s5a-complemento-01/documentacao-anterior.json). A antiga âncora zero que reunia contradição e ausência de relação é histórica, não a recomendação vigente.

Dataset operacional `fccdffc984dca0b30d9c044ee62bee32eb52b3b4a828fe454e6a17de0602fd26`; IDF experimental `9ddb353e50c050f58cc3417f8a41763867550730e7c18c56851d4f6dd74680c6`. Nenhuma reconstrução ou migração automática do IDF da aplicação. Quantidades e verificações no [relatório](../TCC/evidencias/codex-s5a-complemento-01/relatorio-final.md).

## Hipóteses originais preservadas

Redação recuperada do guia, seção 6, com status histórico de confirmação metodológica preservado. Nenhuma hipótese foi reformulada ou confirmada.

| Hipótese literal | Construto/unidade candidata | Entrada → saída | Gabarito/métrica/comparação | Disponível e ausente |
|---|---|---|---|---|
| H1: a fusão lexical + semântica tem F1 macro maior que cada motor isolado (ablação, como A6 e A9). | Relação avaliativa; par de sentenças | Dois textos → classe | Classe anotada; macro-F1 primária, matriz/precisão/revocação/F1 diagnósticas; mesmos pares | Motores disponíveis; desenho classificatório e rótulos compatíveis ausentes |
| H2: o siamês ajustado tem Spearman maior que o SBERT sem ajuste no teste sintético. | Similaridade semântica; proposta de conteúdo proposicional compartilhado, par de sentenças | Dois textos → escalar | Alvo compatível e procedência documentada; Spearman primária; Pearson/MAE/MSE/R² diagnósticas | SBERT disponível; faltam adoção do construto/rubrica/arquitetura/orçamento e alvos reais |
| H3: o sistema mantém a latência p95 dentro de uma meta sob uma carga definida (metas pendentes). | Latência por tentativa de operação em cenário fixado | Entrada/operação → duração/falha/memória | Relógio monotônico; p95 e taxa de falha conjuntos, p50 diagnóstico | Instrumentação de software disponível; meta/carga propostas |

Código existente não aprova metodologia. E2 é assinatura adaptada, E4 é alinhamento; não são classificadores isolados por figurarem no sistema.

## Contratos distintos

| Tarefa | Contrato e limites |
|---|---|
| Derivação/ancestralidade | Fonte, operação, doadores, ancestrais, contribuição e r_by_source descrevem construção. r documental é fração direcional de sentenças derivadas da fonte focal; não é nota semântica nem rótulo de todos os pares de sentenças. |
| Classificação H1 | Quatro classes avaliativas candidatas abaixo, por par previamente anotado de sentenças; C0–C7 e intended_class não substituem validated_class. |
| Similaridade H2 | Escalar e eixos auxiliares sobre textos/contexto identificados; não usar r, 1−edição, C0=0, C5=1 ou C6=equivalência. |
| Índice da aplicação | F=0,4 cos_TFIDF+0,6 max(0,cos_semântico); média dos máximos bidirecionais ponderada por palavras ×100. Simétrico [0,100] no domínio aceito; distinto de r, probabilidade de classe e alinhamento húngaro. Vazios/sem peso útil recusados; semântico indisponível não vira zero; lexical nulo segue política própria e pode impedir identidade global100. |

Unidade documental de construção não é unidade candidata de avaliação. Avaliar pares fornecidos não mede recuperação/alinhamento do sistema completo.

## H1 — rubrica e comparabilidade candidatas

Classes propostas: copia_exata (igualdade na representação contratada), copia_editada (relação textual editada sustentada, sem presumir sentido), parafrase (reformulação que preserva proposição material, sem contradição central), sem_correspondencia_detectada (ausência de relação sustentada naquele par, nunca originalidade comprovada). Precedência candidata: igualdade, edição textual sustentada, paráfrase sustentada, ausência. Conflitos de categoria/contexto insuficiente → ambiguous, sem alvo. Fronteira edição/paráfrase exige piloto de rubrica antes das predições e exemplos preservados.

| Construção | Rótulo defensável e restrição | Insuficiente |
|---|---|---|
| C0 | Nenhum negativo automático | Doador diferente não impede relação semântica |
| C1 | Cópia exata somente no par efetivamente igual | Não comprova plágio nem rotula todas as combinações |
| C2 | Operação de edição conhecida; classe avaliativa depende da rubrica | Negação/número podem inverter sentido |
| C3/C4 | Par literal pode sustentar cópia exata pela fonte contribuinte correta | Multiorigem não autoriza classe global |
| C5 | Paráfrase somente com proposições preservadas anotadas | Fluência/curadoria do gerador não fornecem gabarito independente |
| C6 | Nenhum alvo semântico automático | Entidades iguais podem ter relações opostas |
| C7 | Par literal de sentenças pode sustentar cópia exata | Não extrapolar à relação discursiva documental |

Exemplos artificiais: “A esfera é azul.”/mesmo texto sustenta igualdade; “A esfera é azul.”/“A esfera não é azul.” sustenta edição e contradição, não equivalência; “O rio fica ao norte.”/“O rio fica ao sul.” preserva entidades e altera proposição; “O menino comprou pão.”/“O garoto adquiriu pão.” pode sustentar paráfrase com contexto suficiente. “Ela chegou.”/“Maria chegou.” exige referente contextual, caso contrário é ambíguo.

Proposta de saída comparável: característica escalar lexical L; semântico cosseno bruto S; fusão fixa 0,4L+0,6max(0,S). Mesma família de classificador multinomial logístico L2, C1, max_iter1000, seed20261025, sem pesos de classe, ajustada só no treino para cada representação; seleção/diagnóstico só na validação. É **camada supervisionada proposta**, não afirmação de que cossenos/E2/E4 já classificam. Delimita “cada motor isolado” aos componentes comparáveis e requer adoção antes do ajuste. Alternativa: regras fixas da aplicação por baseline, com mapeamento prévio; ainda sem equivalência metodológica estabelecida. Fusão aprendida é inventariada como planejada, não ablação obrigatória.

Mesmos exemplos elegíveis e alvo, sem IDs/origem/C0–C7/r/split/gabarito nas características; pares anotados antes dos resultados, sem alinhamento escolhido pelo motor vencedor. Qualquer predição ausente torna a comparação incompleta; F1 só dos sucessos não é comparação primária. Preservar tentativas/falhas e exclusões prévias comuns.

## H2 — construto, rubrica e independência candidatos

Recomendação: **grau de conteúdo proposicional compartilhado**, com eixos separados. Tema, equivalência, contradição e contexto não são sinônimos. Alternativas: equivalência proposicional estrita ou implicação direcional; mudam alvo/desenho e exigem adoção antes de anotar/treinar, sem alterar H2 após resultado.

| Âncora | Interpretação orientadora, não rótulo produzido |
|---|---|
| 0 | Nenhum conteúdo proposicional compartilhado demonstrável com contexto suficiente |
| 0,25 | Conteúdo compartilhado pequeno; tema/entidades isolados não bastam |
| 0,5 | Conteúdo parcialmente compartilhado, diferenças materiais |
| 0,75 | Conteúdo predominantemente compartilhado, diferença secundária justificada |
| 1 | Equivalência sustentada, sem diferença material ou contradição |

Notas intermediárias exigem justificativa. “A água ferveu.”/“O líquido entrou em ebulição.” pode sustentar equivalência com referente resolvido. “A água ferveu.”/“A água não ferveu.” compartilha tema/estrutura e contradiz: **não recebe zero automaticamente nem pode receber1**. Duas frases sobre assuntos diferentes não compartilham proposições só por serem declarativas. Contexto insuficiente → ambiguous/target=null. Exclusão exige motivo anterior aos resultados.

Schema candidato H2 hts-annotations-2 adiciona semantic_axes: thematic_overlap (none/some/strong/uncertain), propositional_relation (compatible/contradiction/unrelated/uncertain), shared_content (none/partial/predominant/equivalent/uncertain), context (sufficient/insufficient). Contradição+equivalência é recusada; nota1 exige equivalência compatível; contexto insuficiente não admite alvo. Importador não calcula notas pelos eixos. Schema1 continua estruturalmente aceito para preservar intercâmbio, mas não libera o estudo novo sem compatibilidade da rubrica.

Procedimento proposto: congelar seleção/rubrica antes das predições; fornecer textos/contexto sem escores ou condição sintética que induza resposta; registrar modalidade/origem/procedimento/dependências/evidência. Um procedimento não é consenso. Adjudicação só com recursos reais designados, preservando julgamentos e regra; sem recurso, conflito continua ambíguo. Nenhum anotador foi inventado.

| Alternativa | Recomendação, consequência e condição de adoção |
|---|---|
| Anotação independente compatível se houver recurso real | Preferida para H2 semântica; exige procedimento/rótulos reais e independência documentada; campo de nome não prova identidade/independência |
| Automatizada/fraca | Estudo limitado se explicitamente adotado; registrar modelo/revisão/prompt/dependências; não é consenso humano; média dos motores avaliados não é verdade independente |
| Derivação com r | Alvo operacional de outro construto/unidade; tarefa separada, não confirma H2 semântica |

## Importação, auditoria e cobertura

Contrato em [experiment_io.py](../core/src/hts_core/adapters/experiment_io.py). Bundle exato: schema, dataset_version, task, unit, rubric_id, procedure_id, origin, generator_relationship, shared_dependencies, records. Registro exato: pair_id, source_id, source_sentence_id, suspect_sentence_id, source_text_sha256, suspect_text_sha256, status, target, reason, evidence_ref; H2/schema2 acrescenta semantic_axes. Identificadores/razões/referências são strings não vazias; dependências strings únicas. Notas finitas [0,1], sem bool; ambiguous/excluded preservam null. Campos desconhecidos/tipos indevidos/duplicatas de observação/contradições de modalidade recusados.

Combinações declaradas: human_independent→independent_declared; automated_weak→independent_declared/shared; generator_dependent→same_generator; artificial_fixture→artificial_fixture. Isso verifica coerência declarada, não comprova independência. evidence_ref é **referência textual opaca declarada**, sem resolver caminho ou conferir recurso externo; recibo não a apresenta como arquivo verificado.

IDs/fontes/splits/hashes dos textos exatos são conferidos. Mesmo par textual com IDs diferentes é preservado/contado como repetição, sem virar observação independente. Conflito de status/alvo em texto repetido exige adjudicação e é recusado; não há deduplicação silenciosa. Cobertura distingue registros/alvos/ambiguidades/exclusões por todos os splits e combinações textuais únicas/repetidas, sem alegação amostral ou exaustiva.

import-annotations seleciona treino/validação; audit-annotations admite armazenamento/auditoria do teste **sem criar entradas de modelo ou abrir desempenho**. Ambas preservam bytes originais/base64, identidade, bundle e recibo, recusando sobrescrita. Fixture artificial recusada no dataset operacional. Validação estrutural não é aprovação científica.

## Siamês — arquitetura e orçamento propostos

A7: [conferência primária preservada](../TCC/evidencias/codex-s5a-01/primary-a7.json), arquitetura PDF6–7, Tabela1 PDF9/impressa8: 8 épocas, Adam,2e-6,212 tokens,weight_decay1e-5,MSELoss. Base específica/dimensões/detalhes ausentes não são atribuídos ao artigo; unidade por sentença é adaptação dos resumos.

Alternativa histórica: BERTimbau, sem revisão de treino fixada/recurso local confirmado. Recomendação candidata: mesma base SBERT do baseline, sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2, revisão e8f8c211226b894fcb81acc59f3b34ba3efd5f42, Apache-2.0, local; reduz confusão entre base e ajuste. Requer adoção, não substitui silenciosamente a alternativa histórica.

Ramos compartilham mesma instância/pesos; embedding384, janelas completas não sobrepostas, média ponderada por conteúdo e L2 conforme baseline. Configuração local: **128 tokens totais/janela**, não212; preservar especiais/cobertura. Dois textos como entrada, alvo separado. concat(abs(u−v),u*v)=768 →Linear128→LayerNorm(eps1e-5)→LeakyReLU0,1→Dropout0,1→Linear1→Sigmoid; saída finita [0,1], MSE, Adam2e-6/weight_decay1e-5. Base/cabeça/dimensões/ativação/dropout são escolhas propostas do projeto, não reprodução integral de A7. Diagnóstico SBERT (cos+1)/2 alinha faixa; Spearman usa cosseno bruto e é invariante a transformação afim.

Tetos propostos: CPU2 threads,microbatch1/acumulação4; máximo8 épocas/2000 atualizações/7200s/3GiB RSS; uma tentativa; parada pelo primeiro teto ou2 épocas sem melhora; seleção menor MSE de validação/empate pela época mais antiga. São limites conservadores no ambiente observado, **não duração estimada/medida ou viabilidade garantida**. Estouro é tentativa parcial/falha preservada, não permite escolher outra seed ou ampliar após teste. Mesma política de sentenças longas do baseline, sem exclusão/truncamento conveniente.

Checkpoint futuro: identidades protocolo/dataset/rótulos/rubrica/modelo/config/código; pesos/otimizador/scheduler se houver; RNG Python/NumPy/Torch; posição época/batch/acumulação; histórico/seleção/parada; gravação atômica/integridade/compatibilidade. Checkpoint S5A é de preparação, sem pesos; não simula retomada real de treino. Laço com atualização permanece etapa futura dependente de contrato/alvo, com interfaces/schemas/dimensões/identidades preparados.

## Dependência estatística e exposição

Grafo conservador inclui fonte focal/doadores/multiorigem/ancestrais: um componente por split. Não há59 unidades independentes demonstradas; formatos/sentenças/derivados não criam fontes. Exposição durante construção é registrada e não autoriza medir desempenho agora.

| Alternativa | Conclusão e limite | Mudança necessária |
|---|---|---|
| Descrição finita — recomendada | Métricas/diferenças descritivas futuras, sem intervalo populacional indevido | Adotar alcance antes das predições; preservar versão atual |
| Desenho prospectivo separado | Inferência por componentes somente se desenho/quantidade justificarem | Planejar fontes/doadores antes de gerar/prever; menor mudança justificada, nova versão; não mover linhas isoladas |
| Inferência dependente | Só conclusões sustentadas pelo modelo de dependência | Justificativa/implementação próprias, sem bootstrap ingênuo por linha/fonte |

Mais derivados conectados não resolvem independência. Não houve reconstrução por presunção nem seleção de subconjunto por desempenho.

## H3 — cenário, falhas e memória

Ambiente: Windows/Ryzen5 5500U/GPU AMD integrada/Torch CPU; inventários [cpu](../TCC/evidencias/codex-s5a-complemento-01/cpu.json), [sistema](../TCC/evidencias/codex-s5a-complemento-01/os.json), [GPU](../TCC/evidencias/codex-s5a-complemento-01/gpu.json). Sem presunção CUDA/conta externa; psutil ausente, sem instalação.

Proposta anterior à medição: concorrência1; dois documentos de1/10/20 sentenças, TXT/DOCX/PDF equivalentes, bytes/caracteres/tokens reais registrados;3 aquecimentos/30 tentativas por célula;3 processos frios separados; timeout30s. Limites da aplicação documentados, sem truncamento para melhorar resultado. Cenário principal HTTP core aquecido20+20 sentenças: meta candidata p95≤2s **e taxa de falha0**. É objetivo interativo escolhido pelo projeto, não capacidade observada ou requisito adotado. Rever antes de medir;30 tentativas dão cauda pouco precisa, não estender até sucesso.

Aceitação conjunta: p95 dos sucessos dentro da meta e falhas/tentativas totais≤limite. Timeouts contam falha; zero sucessos não aceita/p95 indefinido. Preservar totais/sucessos/falhas/timeouts/tempos brutos. latency_acceptance usa percentil linear; fixtures de relógio/RSS verificam software, não H3.

Fronteiras separadas: motor (pré-processado→saída), core (texto→resultado, inclui processamento), HTTP (envio→corpo completo), aplicação (rota→resposta,persistência/auth declaradas), usuário (seleção/envio/renderização). Nenhuma mede as demais. Aplicação com persistência é cenário separado; futuras medições em ambiente isolado com serviços/versões/concorrência inventariados.

tracemalloc mede alocações Python rastreadas, não memória nativa total. RSS mede páginas residentes; duas leituras antes/depois **não são pico**, nem delta garantido da operação. Pico exige amostragem/método/processos identificados; GPU exige coletor próprio. Interface RSS opcional testada sem instalar dependência. Nenhuma carga ou benchmark executado.

## IDF — contratos compartilhados e escopos

[idf_contract.py](../core/src/hts_core/adapters/idf_contract.py) compartilhado pelo preflight e S4. A: schemas exatos, hashes/identidades/bytes. B: N real do treino, fontes/revisões/hashes/bytes reais, configuração real/input_identity/finalidade, TF raw_count, fórmula ln((1+N)/(1+df))+1, unknown_df0, normalização cosine_only, produtor selado e execução vinculada à candidata/congelada permitida. execution.json obrigatório; rehash de contrato incompatível não valida. Para versão congelada, o pai é vinculado à revisão/reprodução/inventário preservados, não ao upstream-manifest de coleta.

C é recomposição lexical efetiva de N/df. **Não ocorre no preflight leve**, nem se reutiliza prova histórica como execução atual. Caminho explícito: `python -m hts_core.cli dataset validar-idf --dataset DATASET --idf IDF`. Usa A/B e projeção do produtor lexical pertinente antes de recompor: módulos produtores, modelo/recursos/stopwords/política de texto/Python/Unicode/lock/pacotes lexicais. Módulos novos sem relação não invalidam automaticamente IDF histórico. CRLF/LF exigem equivalência documentada, sem trocar hashes silenciosamente. Preflight informa produtor atual not_checked e C not_executed. IDF continua41 documentos/13.673 termos ajustado só no treino, separado da aplicação.

## Schemas, métricas e proteção

[experiment_protocol.py](../core/src/hts_core/adapters/experiment_protocol.py) valida raiz/dataset/hypotheses/tasks/baselines/seeds/execution/h3/training/test_policy e suplemento: campos obrigatórios/desconhecidos/tipos/enums/listas/duplicatas/brancos/bool numérico/não finitos/limites/coerência. null só onde explicitamente permitido; não substitui objeto. Planejado exige estado pendente/implementação nula; existente exige inventário completo. Métricas únicas e compatíveis por tarefa, primárias/diagnósticas explicitadas.

Métricas preservadas: labels explícitos; zero_division0/suporte relatado/classes ausentes na macro; não rotulado sem alvo; correlação indefinida não vira zero; empates por postos médios; NaN recusado; arredondamento só na exibição. Fixtures literais/rankings/classes ausentes/todas erradas têm oráculos independentes, não resultados H1–H3.

Contexto/eventos/checkpoints vinculam identidades, falhas e incompatibilidade de retomada. Entradas de modelo só contêm textos. Executor continua recusando treino/calibração/teste mesmo com booleanos/IDs de aprovação. Fluxo futuro exige implementação própria, protocolo adotado, dataset/rótulos/rubrica/unidade/modelos/config/métricas/seeds/repetições e evidência da autorização da etapa. Auditar anotações do teste não abre desempenho. Mudanças geram revisão preservando anteriores.

## Continuidade

H1 depende de desenho/rótulos reais; H2 de construto/rubrica/procedência/alvos/arquitetura/orçamento; H3 de meta/carga adotadas e autorização futura. Alcance estatístico anterior às predições. Ver [matriz](../TCC/evidencias/codex-s5a-complemento-01/matriz-prontidao.md) e [prompt S5B](09-prompt-s5b.md). Engenharia preparada não equivale a treinamento liberado. Nenhuma etapa seguinte iniciada.


## Auditoria integrada Docker vigente

[Relatório](../TCC/evidencias/codex-s5b-docker-01/relatorio-final.md) e [gate](../TCC/evidencias/codex-s5b-docker-01/matriz-prontidao-s5c.md): S5A verificada no alcance auditado; S5B ainda sem treino real por recursos. Contratos científicos não modificados retrospectivamente. S5A continua recusando treino; S5B usa fluxo próprio. Teste final e S5C não executados. Falhas de export H1/manifest corrigidas e testadas; carregamento real depende de modelos ainda ausentes.


## Verificação vigente da conclusão S5B

[Relatório atual](../TCC/evidencias/codex-s5b-conclusao-01/relatorio-final.md): IDF A/B/C executado com diferença de lock global explícita e df integral igual; modo padrão permanece estrito, parâmetros científicos/IDF não alterados. Readiness03 H1/H2 continua bloqueado por recurso; nenhum treinamento real. [Preparação futura da referência S5C](12-plano-referencia-final-s5c.md), não executada. Históricos acima preservados.
